SELECT sc.story_id || E'\t' ||
 (CASE sc.story_id
   WHEN '1e6d82e2-ed22-4881-aa96-0c1c575348ba' THEN 'BIG'
   WHEN '490fa438-2770-444d-ba27-fb53ede73033' THEN 'SMALL'
   ELSE 'ONE' END) || E'\t' ||
 json_build_object(
   'title', sc.representative_title,
   'topic', sc.topic,
   'subject_country', sc.subject_country,
   'subject_region', sc.subject_region,
   'entities', sc.primary_entities,
   'article_count', sc.article_count,
   'source_count', sc.independent_source_count,
   'rep_quote', sc.representative_quote,
   'stance', (SELECT json_build_object('distribution', s.stance_distribution, 'sentiment', s.sentiment)
              FROM analytics.story_stance s WHERE s.story_id = sc.story_id),
   'geo', (SELECT json_build_object('primary', g.primary_country, 'countries', g.subject_countries, 'continent', g.continent)
           FROM analytics.story_geo g WHERE g.story_id = sc.story_id),
   'facts', (SELECT json_agg(json_build_object('fact', fact_key, 'unit', unit, 'min', value_min,
                'max', value_max, 'latest', value_latest, 'claim', sample_claim, 'n_sources', member_count))
             FROM (SELECT * FROM analytics.story_facts WHERE story_id = sc.story_id
                   ORDER BY member_count DESC NULLS LAST LIMIT 18) f),
   'quotes', (SELECT json_agg(json_build_object('quote', qt, 'speaker', speaker))
              FROM (SELECT qt, speaker FROM
                      (SELECT DISTINCT ON (speaker) speaker, coalesce(quote_text_en, quote_text) qt
                       FROM analytics.story_quotes
                       WHERE story_id = sc.story_id AND is_direct AND coalesce(quote_text_en, quote_text) IS NOT NULL
                       ORDER BY speaker) qq
                    ORDER BY length(qt) DESC LIMIT 18) q),
   'articles', (SELECT json_agg(json_build_object('date', d, 'title', t, 'summary', su, 'lead', le))
                FROM (SELECT a.collected_at::date d, a.title t, a.summary_executive su, a.lead_text_translated le
                      FROM analytics.story_cluster_members m JOIN articles a ON a.id = m.article_id
                      WHERE m.story_id = sc.story_id ORDER BY a.collected_at LIMIT 14) a)
 )::text
FROM analytics.story_clusters sc
WHERE sc.story_id IN ('1e6d82e2-ed22-4881-aa96-0c1c575348ba',
                      '490fa438-2770-444d-ba27-fb53ede73033',
                      'babd8e8b-a37d-45ca-ad04-08908f6f2a3c');
