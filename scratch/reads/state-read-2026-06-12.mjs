// Read-only re-baseline read, 2026-06-12. Analytics chat, rigwire_app fallback.
// Writes RAW output to state-read-2026-06-12.json; prints a structural summary.
import postgres from 'postgres';
import { readFileSync, writeFileSync } from 'node:fs';

const env = readFileSync(new URL('../../.env.local', import.meta.url), 'utf8');
const url = env.match(/^ANALYTICS_DB_URL=(.+)$/m)[1].trim();
const sql = postgres(url, { prepare: false, max: 2, idle_timeout: 5, connect_timeout: 15 });

const out = {};
try {
  // 1. migration tracking tables (find the mechanism)
  out.migration_tables = await sql`
    SELECT table_schema, table_name FROM information_schema.tables
    WHERE table_name ILIKE '%migration%' OR table_name ILIKE '%schema_version%'
    ORDER BY 1,2`;

  // 2. analytics.story_clusters columns
  out.story_clusters_cols = await sql`
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_schema='analytics' AND table_name='story_clusters'
    ORDER BY ordinal_position`;

  // 3. all analytics.story_* + related tables (+ approx row counts via reltuples)
  out.story_tables = await sql`
    SELECT c.relname AS name, c.reltuples::bigint AS approx_rows
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='analytics' AND c.relkind IN ('r','m')
      AND (c.relname LIKE 'story_%' OR c.relname LIKE '%aem%' OR c.relname LIKE 'mc_%')
    ORDER BY c.relname`;

  // 4. parachute existence
  out.parachute = await sql`
    SELECT to_regclass('analytics.story_clusters_old') AS clusters_old,
           to_regclass('analytics.story_members_old')  AS members_old`;

  // 5. exact keeper count
  out.keeper_count = await sql`SELECT count(*)::int AS n FROM analytics.story_clusters`;

  // 6. suppression_reason distribution (if column exists)
  try {
    out.suppression_reasons = await sql`
      SELECT suppression_reason, count(*)::int AS n
      FROM analytics.story_clusters GROUP BY 1 ORDER BY 2 DESC`;
  } catch (e) { out.suppression_reasons = { error: e.message }; }

  // 7. entity_dictionary shape + size
  out.entity_dict_cols = await sql`
    SELECT column_name, data_type FROM information_schema.columns
    WHERE table_schema IN ('analytics','public') AND table_name='entity_dictionary'
    ORDER BY ordinal_position`;

  // 8. AEM matview definition (look for body-presence / extraction-time validation)
  out.aem_matviews = await sql`
    SELECT schemaname, matviewname FROM pg_matviews
    WHERE matviewname ILIKE '%aem%' OR matviewname ILIKE '%entity_mention%'
    ORDER BY 1,2`;

  writeFileSync(new URL('./state-read-2026-06-12.json', import.meta.url),
    JSON.stringify(out, null, 2));

  // structural summary (shapes, not a retyped numbers doc)
  console.log('MIGRATION TABLES:', JSON.stringify(out.migration_tables));
  console.log('STORY_CLUSTERS COLS:', out.story_clusters_cols.map(c=>c.column_name).join(', '));
  console.log('STORY/AEM TABLES:', out.story_tables.map(t=>`${t.name}(~${t.approx_rows})`).join(', '));
  console.log('PARACHUTE:', JSON.stringify(out.parachute[0]));
  console.log('KEEPER COUNT:', out.keeper_count[0].n);
  console.log('SUPPRESSION_REASONS:', JSON.stringify(out.suppression_reasons));
  console.log('ENTITY_DICT COLS:', JSON.stringify(out.entity_dict_cols));
  console.log('AEM MATVIEWS:', JSON.stringify(out.aem_matviews));
} catch (e) {
  console.error('READ ERROR:', e.message);
} finally {
  await sql.end({ timeout: 5 });
}
