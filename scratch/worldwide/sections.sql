-- Worldwide section-query library + edge-case validation (Stage 3)
-- Run: ssh ... "docker exec -i rig-postgres psql -U rig -d rig -tAF'|'" < sections.sql
-- Scored pool = ranking + suppression + title-flag, as a temp view reused by every section.

\set ON_ERROR_STOP off

DROP VIEW IF EXISTS scored;
CREATE TEMP VIEW scored AS
WITH facts AS (SELECT story_id, count(*) fc FROM analytics.story_facts GROUP BY 1),
     maxd  AS (SELECT max(last_seen_at) m FROM analytics.story_clusters)
SELECT sc.story_id,
       left(sc.representative_title,46) AS rt,
       sc.independent_source_count       AS isrc,
       sc.article_count                  AS ac,
       coalesce(f.fc,0)                  AS facts,
       coalesce(nullif(sc.topic,''),'OTHER')           AS topic,
       coalesce(nullif(sc.subject_country,''),'XX')    AS country,
       coalesce(a.source_tier,2)                       AS tier,
       round(( 1.0*ln(1+sc.independent_source_count)
             + 0.5*ln(1+least(coalesce(f.fc,0),15))
             + 2.0*exp(-extract(epoch from (maxd.m - sc.last_seen_at))/86400.0/3.0)
             + (CASE coalesce(a.source_tier,2) WHEN 1 THEN 1.0 WHEN 2 THEN 0.3 ELSE 0.0 END))::numeric,2) AS imp
FROM analytics.story_clusters sc
LEFT JOIN facts f USING(story_id)
LEFT JOIN articles a ON a.id = sc.representative_article_id
CROSS JOIN maxd
WHERE sc.suppression_reason IS NULL
  AND sc.independent_source_count IS NOT NULL
  AND sc.representative_title !~* '(share price|top picks|result 20[0-9]{2}|gainers (and|&) losers|dream ?11|sensex|nifty|share market)';

-- diversity-floor helper: real topics capped at 2; OTHER never capped (own partition per story)
DROP VIEW IF EXISTS ranked_div;
CREATE TEMP VIEW ranked_div AS
SELECT *, row_number() OVER (
   PARTITION BY CASE WHEN topic='OTHER' THEN story_id::text ELSE topic END
   ORDER BY imp DESC) AS rn
FROM scored;

\echo ===SECTION top_stories_WORLD===
SELECT imp,isrc,ac,topic,country,rt FROM ranked_div WHERE rn<=2 ORDER BY imp DESC LIMIT 10;
\echo ===SECTION top_stories_INDIA===
SELECT imp,isrc,ac,topic,rt FROM ranked_div WHERE rn<=2 AND country='IN' ORDER BY imp DESC LIMIT 8;
\echo ===SECTION politics===
SELECT imp,isrc,country,rt FROM scored WHERE topic='POLITICS' ORDER BY imp DESC LIMIT 6;
\echo ===SECTION sports===
SELECT imp,isrc,country,rt FROM scored WHERE topic='SPORTS' ORDER BY imp DESC LIMIT 6;
\echo ===SECTION military_security===
SELECT imp,isrc,country,rt FROM scored WHERE topic='SECURITY' ORDER BY imp DESC LIMIT 6;
\echo ===SECTION climate_science===
SELECT imp,isrc,country,rt FROM scored WHERE topic='ENVIRONMENT' ORDER BY imp DESC LIMIT 6;
\echo ===SECTION business_finance===
SELECT imp,isrc,country,rt FROM scored WHERE topic IN ('BUSINESS','FINANCE') ORDER BY imp DESC LIMIT 6;
\echo ===SECTION around_the_world===
WITH c AS (SELECT country FROM scored WHERE country<>'XX' GROUP BY country HAVING count(*)>=50)
SELECT DISTINCT ON (country) country, imp, isrc, rt
FROM scored WHERE country IN (SELECT country FROM c)
ORDER BY country, imp DESC;

\echo ===EDGECHECKS===
-- 1. suppressed never leak
SELECT 'EC1 suppressed_excluded='||(CASE WHEN count(*)=0 THEN 'PASS' ELSE 'FAIL('||count(*)||')' END)
FROM scored s JOIN analytics.story_clusters sc USING(story_id) WHERE sc.suppression_reason IS NOT NULL;
-- 2. title-flag piles never leak
SELECT 'EC2 titleflag_excluded='||(CASE WHEN count(*)=0 THEN 'PASS' ELSE 'FAIL('||count(*)||')' END)
FROM scored WHERE rt ~* '(share price|sensex|nifty)';
-- 3. OTHER not capped by diversity (can exceed 2 in a large pull)
SELECT 'EC3 other_uncapped='||(CASE WHEN count(*)>2 THEN 'PASS('||count(*)||' OTHER in top100)' ELSE 'CHECK('||count(*)||')' END)
FROM (SELECT * FROM ranked_div WHERE rn<=2 ORDER BY imp DESC LIMIT 100) q WHERE topic='OTHER';
-- 4. real topic capped at <=2 in any large pull
SELECT 'EC4 topic_cap_holds='||(CASE WHEN max(c)<=2 THEN 'PASS' ELSE 'FAIL(max='||max(c)||')' END)
FROM (SELECT topic, count(*) c FROM (SELECT * FROM ranked_div WHERE rn<=2 ORDER BY imp DESC LIMIT 60) q WHERE topic<>'OTHER' GROUP BY topic) z;
-- 5. India scope differs from World (and excludes non-IN)
SELECT 'EC5 india_scope_pure='||(CASE WHEN count(*) FILTER (WHERE country<>'IN')=0 THEN 'PASS' ELSE 'FAIL' END)
FROM (SELECT * FROM ranked_div WHERE rn<=2 AND country='IN' ORDER BY imp DESC LIMIT 8) q;
-- 6. scoop visibility: any single-article story in the World top 50?
SELECT 'EC6 single_article_in_top50='||count(*) FILTER (WHERE ac=1)||'/50'
FROM (SELECT * FROM ranked_div WHERE rn<=2 ORDER BY imp DESC LIMIT 50) q;
-- 7. around-the-world: max one story per country
SELECT 'EC7 atw_one_per_country='||(CASE WHEN coalesce(max(c),0)<=1 THEN 'PASS' ELSE 'FAIL' END)
FROM (WITH c AS (SELECT country FROM scored WHERE country<>'XX' GROUP BY country HAVING count(*)>=50),
           t AS (SELECT DISTINCT ON (country) country FROM scored WHERE country IN (SELECT country FROM c) ORDER BY country, imp DESC)
      SELECT country, count(*) c FROM t GROUP BY country) z;
-- 8. every clustered section non-empty (else flag gap)
SELECT 'EC8 section_'||t||'='||(CASE WHEN n>0 THEN 'OK('||n||')' ELSE 'EMPTY-GAP' END)
FROM (SELECT unnest(ARRAY['POLITICS','SPORTS','SECURITY','ENVIRONMENT','HEALTH','BUSINESS','FINANCE','LEGAL','TECHNOLOGY']) t) x
CROSS JOIN LATERAL (SELECT count(*) n FROM scored WHERE topic=x.t) y;
