SELECT sc.article_count || E'\t' || sc.independent_source_count || E'\t' ||
  replace(replace(left(sc.representative_title, 60), chr(10), ' '), E'\t', ' ') || E'\t' ||
  coalesce((SELECT string_agg(replace(fact_key || ': ' || coalesce(sample_claim,''), chr(10), ' '), ' ~~ ')
            FROM (SELECT * FROM analytics.story_facts WHERE story_id = sc.story_id ORDER BY member_count DESC NULLS LAST LIMIT 12) f), '') || E'\t' ||
  coalesce((SELECT string_agg(replace('"' || coalesce(quote_text_en, quote_text) || '" - ' || coalesce(speaker,'?'), chr(10), ' '), ' ~~ ')
            FROM (SELECT * FROM analytics.story_quotes WHERE story_id = sc.story_id AND is_direct AND coalesce(quote_text_en,quote_text) IS NOT NULL LIMIT 12) q), '') || E'\t' ||
  coalesce((SELECT string_agg(replace(a.collected_at::date || ' :: ' || a.title || ' :: ' || left(coalesce(a.summary_executive, a.lead_text_translated, ''),300), chr(10), ' '), ' ~~ ' ORDER BY a.collected_at)
            FROM (SELECT a.collected_at, a.title, a.summary_executive, a.lead_text_translated
                  FROM analytics.story_cluster_members m JOIN articles a ON a.id = m.article_id
                  WHERE m.story_id = sc.story_id ORDER BY a.collected_at LIMIT 8) a), '')
FROM analytics.story_clusters sc
WHERE sc.suppression_reason IS NULL AND sc.article_count BETWEEN 3 AND 80
  AND (SELECT count(*) FROM analytics.story_facts f WHERE f.story_id = sc.story_id) >= 2
ORDER BY random() LIMIT 12;
