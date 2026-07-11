-- Post-_v8 re-validation (analytics lane). Fires once the _v8 clusters land.
-- Run: ssh ... "docker exec -i rig-postgres psql -U rig -d rig -tAF'|'" < validate_v8.sql
-- CONFIRM table names first. Assumed: analytics.story_clusters_v8 / _members_v8.
-- Member col assumed `article_id`; cluster size col `article_count`. Adjust if DB chat differs.
-- PHASE 1 = clusters only (no enrichment yet): proves the over-merge SPLIT worked.
-- Section/topic checks (PHASE 2) reuse sections.sql with the table swap below.

\set ON_ERROR_STOP off

-- ── A. Size distribution: did the giants shrink? (compare buckets to job_7) ──
\echo ===A1 size_buckets_v8===
SELECT bucket,
       count(*)                                   AS clusters,
       sum(article_count)                         AS articles,
       count(*) FILTER (WHERE suppression_reason IS NOT NULL) AS suppressed
FROM (
  SELECT article_count, suppression_reason,
         CASE WHEN article_count=1 THEN '1'
              WHEN article_count<10 THEN '2-9'
              WHEN article_count<100 THEN '10-99'
              WHEN article_count<1000 THEN '100-999'
              ELSE '1000+' END AS bucket
  FROM analytics.story_clusters_v8) z
GROUP BY bucket ORDER BY min(article_count);

\echo ===A2 size_buckets_job7_baseline===
SELECT bucket, count(*) clusters, sum(article_count) articles,
       count(*) FILTER (WHERE suppression_reason IS NOT NULL) suppressed
FROM (
  SELECT article_count, suppression_reason,
         CASE WHEN article_count=1 THEN '1' WHEN article_count<10 THEN '2-9'
              WHEN article_count<100 THEN '10-99' WHEN article_count<1000 THEN '100-999'
              ELSE '1000+' END AS bucket
  FROM analytics.story_clusters) z
GROUP BY bucket ORDER BY min(article_count);

-- ── B. Member-fit by bucket: the over-merge PROOF. ──
-- Mean cosine of members to their cluster centroid. job_7 giants sat ~0.68-0.70;
-- a clean split should pull the >=100 buckets UP toward the ~0.83 of small clusters.
-- Sampled (200 clusters/bucket, 40 members each) to bound runtime.
\echo ===B member_fit_by_bucket_v8===
WITH samp AS (
  SELECT story_id, article_count,
         CASE WHEN article_count<10 THEN '2-9' WHEN article_count<100 THEN '10-99'
              WHEN article_count<1000 THEN '100-999' ELSE '1000+' END AS bucket,
         row_number() OVER (PARTITION BY (article_count>=1000), (article_count>=100), (article_count>=10)
                            ORDER BY story_id) AS rn
  FROM analytics.story_clusters_v8 WHERE article_count>=2),
  cl AS (SELECT story_id, bucket FROM samp WHERE rn<=200),
  mem AS (
    SELECT c.bucket, c.story_id, a.labse_embedding_v4 AS v,
           row_number() OVER (PARTITION BY c.story_id ORDER BY m.article_id) AS mrn
    FROM cl c JOIN analytics.story_cluster_members_v8 m USING(story_id)
              JOIN articles a ON a.id=m.article_id
    WHERE a.labse_embedding_v4 IS NOT NULL),
  capped AS (SELECT * FROM mem WHERE mrn<=40),
  cent AS (SELECT story_id, avg(v) c FROM capped GROUP BY 1)
SELECT capped.bucket,
       count(DISTINCT capped.story_id)              AS clusters,
       round(avg(1-(capped.v <=> cent.c))::numeric,3) AS mean_member_fit,
       round(min(1-(capped.v <=> cent.c))::numeric,3) AS worst
FROM capped JOIN cent USING(story_id)
GROUP BY capped.bucket ORDER BY 1;

-- ── C. Recovered stories + headline shape ──
\echo ===C totals_v8===
SELECT count(*) total_clusters,
       count(*) FILTER (WHERE article_count=1)               AS single,
       count(*) FILTER (WHERE article_count>1)               AS multi,
       round(avg(article_count) FILTER (WHERE article_count>1),1) AS avg_multi_size,
       count(*) FILTER (WHERE suppression_reason IS NOT NULL) AS suppressed,
       max(article_count)                                    AS biggest
FROM analytics.story_clusters_v8;

\echo ===C suppression_reasons_v8===
SELECT coalesce(suppression_reason,'(surfaced)') reason, count(*)
FROM analytics.story_clusters_v8 GROUP BY 1 ORDER BY 2 DESC;

-- ── D. No NEW mega-blob class: any >1000 cluster signatures to eyeball ──
\echo ===D giants_remaining_v8===
SELECT story_id, article_count, suppression_reason, left(representative_title,60) rt
FROM analytics.story_clusters_v8 WHERE article_count>=1000
ORDER BY article_count DESC LIMIT 25;

-- ── PHASE 2: section + topic checks ──
-- After enrichment runs on _v8, re-run scratch/worldwide/sections.sql with these swaps:
--   analytics.story_clusters     -> analytics.story_clusters_v8
--   analytics.story_facts        -> analytics.story_facts_v8   (if enrichment wrote a _v8 set)
--   analytics.story_cluster_members -> analytics.story_cluster_members_v8
-- All 8 EDGECHECKS (EC1 suppressed-excluded ... EC8 sections-nonempty) must still PASS,
-- and EC3 OTHER-flood should now resolve (topic=OTHER share drops post-enrichment).
\echo ===PHASE2 note: run sections.sql against _v8 tables after enrichment===
