// Recall/precision sweep for the forward-loop JOIN gate. Compares the two proposed
// membership configs by joining each JOIN's article title to its TARGET story title.
import postgres from 'postgres';
import fs from 'fs';

const env = Object.fromEntries(
  fs.readFileSync('.env.local', 'utf8').split('\n').filter(l => l.includes('=') && !l.trim().startsWith('#'))
    .map(l => { const i = l.indexOf('='); return [l.slice(0, i).trim(), l.slice(i + 1).trim().replace(/^["']|["']$/g, '')]; })
);
const sql = postgres(env.ANALYTICS_DB_URL, { max: 2, connect_timeout: 10 });

function parse(path) {
  const out = [];
  const lines = fs.readFileSync(path, 'utf8').split('\n').slice(1);
  for (const ln of lines) {
    if (!ln.trim()) continue;
    const p = ln.split(',');
    out.push({ id: p[0], cls: p[1], story: p[2], score: p[3], jac: p[5], title: p.slice(6).join(',') });
  }
  return out;
}
function tally(rows) { const t = {}; for (const r of rows) t[r.cls] = (t[r.cls] || 0) + 1; return t; }

const A = parse('scratch/worldwide/fwd_membership_df200_jj010.csv'); // df200 jj0.10
const B = parse('scratch/worldwide/fwd_membership_df150_jj012.csv'); // df150 jj0.12
const jA = new Map(A.filter(r => r.cls === 'JOIN').map(r => [r.id, r]));
const jB = new Map(B.filter(r => r.cls === 'JOIN').map(r => [r.id, r]));

console.log('df200@0.10 :', JSON.stringify(tally(A)));
console.log('df150@0.12 :', JSON.stringify(tally(B)));
const onlyA = [...jA.values()].filter(r => !jB.has(r.id));   // df200 joins that df150 DROPS
const onlyB = [...jB.values()].filter(r => !jA.has(r.id));   // df150 joins df200 lacked
console.log(`JOIN df200=${jA.size} df150=${jB.size} | df150-DROPS(inA!B)=${onlyA.length} | inB!A=${onlyB.length}`);

const ids = [...new Set([...jA.values(), ...jB.values()].map(r => r.story))].filter(Boolean);
const titles = new Map();
for (const row of await sql`SELECT story_id, representative_title rt, coalesce(nullif(topic,''),'?') topic FROM analytics.story_clusters_v8 WHERE story_id = ANY(${ids})`)
  titles.set(row.story_id, `[${row.topic}] ${row.rt}`);
const show = (r) => `  j=${r.jac} s=${r.score} | ${(r.title || '').slice(0, 46)}  =>  ${(titles.get(r.story) || '?').slice(0, 50)}`;

console.log('\n=== df150 DROPS these df200-JOINs (errors killed, or legit starved?) ===');
onlyA.slice(0, 60).forEach(r => console.log(show(r)));
console.log('\n=== sample of df150 JOINs (precision of the tighter config) ===');
[...jB.values()].slice(0, 30).forEach(r => console.log(show(r)));
await sql.end();
