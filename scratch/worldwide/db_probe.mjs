// Connectivity probe: can the Next.js app read _v8? Tests both clients. No secrets printed.
import postgres from 'postgres';
import fs from 'fs';
const env = Object.fromEntries(
  fs.readFileSync('.env.local', 'utf8').split('\n').filter(l => l.includes('=') && !l.trim().startsWith('#'))
    .map(l => { const i = l.indexOf('='); return [l.slice(0, i).trim(), l.slice(i + 1).trim().replace(/^["']|["']$/g, '')]; })
);
for (const key of ['ANALYTICS_DB_URL', 'RIGWIRE_DB_URL']) {
  if (!env[key]) { console.log(key, 'MISSING'); continue; }
  try {
    const sql = postgres(env[key], { max: 1, idle_timeout: 2, connect_timeout: 8 });
    const r = await sql`SELECT count(*)::int n FROM analytics.story_clusters_v8 WHERE suppression_reason IS NULL`;
    console.log(key, 'OK  surfaced story_clusters_v8 =', r[0].n);
    await sql.end();
  } catch (e) { console.log(key, 'ERR', String(e.message).slice(0, 90)); }
}
