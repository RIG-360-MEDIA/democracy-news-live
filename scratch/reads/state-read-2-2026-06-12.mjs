// Follow-up read 2026-06-12: AEM matview def, algo/run versions, alias-overreach probe.
import postgres from 'postgres';
import { readFileSync, writeFileSync } from 'node:fs';
const env = readFileSync(new URL('../../.env.local', import.meta.url), 'utf8');
const url = env.match(/^ANALYTICS_DB_URL=(.+)$/m)[1].trim();
const sql = postgres(url, { prepare: false, max: 2, idle_timeout: 5, connect_timeout: 15 });
const out = {};
try {
  // engine re-cluster check: distinct algo_version + run_id + freshness
  out.versions = await sql`
    SELECT algo_version, count(*)::int AS n,
           max(last_seen_at) AS newest, min(created_at) AS oldest_created
    FROM analytics.story_clusters GROUP BY 1 ORDER BY 2 DESC`;
  out.run_ids = await sql`
    SELECT run_id, count(*)::int AS n FROM analytics.story_clusters
    GROUP BY 1 ORDER BY 2 DESC LIMIT 5`;

  // AEM matview definition — is body-presence/extraction validation upstream now?
  out.aem_def = await sql`
    SELECT definition FROM pg_matviews
    WHERE schemaname='public' AND matviewname='article_entity_mentions'`;

  // alias-overreach probe: do the documented dangerous bare-noun aliases still resolve?
  out.alias_probe = await sql`
    SELECT canonical_name, entity_type, state, party, aliases
    FROM public.entity_dictionary
    WHERE canonical_name ILIKE ANY (ARRAY['%congress%','%indian national congress%','%mir zulfeqar%','%bharat rashtra%'])
       OR aliases && ARRAY['Congress','Ali','Party','Samithi','Inc.']
    LIMIT 25`;
  // is there a tier marker in metadata?
  out.dict_meta_sample = await sql`
    SELECT canonical_name, metadata FROM public.entity_dictionary
    WHERE metadata IS NOT NULL AND metadata::text <> '{}' LIMIT 5`;
  out.dict_count = await sql`SELECT count(*)::int AS n,
     count(*) FILTER (WHERE redirected_to IS NOT NULL)::int AS redirected
     FROM public.entity_dictionary`;

  writeFileSync(new URL('./state-read-2-2026-06-12.json', import.meta.url), JSON.stringify(out, null, 2));
  console.log('VERSIONS:', JSON.stringify(out.versions));
  console.log('RUN_IDS:', JSON.stringify(out.run_ids));
  console.log('DICT_COUNT:', JSON.stringify(out.dict_count[0]));
  console.log('ALIAS_PROBE (count):', out.alias_probe.length);
  console.log(JSON.stringify(out.alias_probe.map(r=>({c:r.canonical_name,t:r.entity_type,al:(r.aliases||[]).slice(0,8)})), null, 1));
  console.log('DICT_META_SAMPLE:', JSON.stringify(out.dict_meta_sample));
  console.log('AEM_DEF (first 1200 chars):');
  console.log((out.aem_def[0]?.definition || 'NONE').slice(0,1200));
} catch (e) { console.error('READ ERROR:', e.message); }
finally { await sql.end({ timeout: 5 }); }
