# Democracy News Live — Vercel deploy runbook

Separate Vercel project off **this repo** (Approach A). DNL surfaces only; Rig Wire links to the URL.
Data plane = **Neon** (isolated read replica of the box + native writable `rigwire.*`), per
`docs/handoffs/dnl-vercel-data-architecture.md`.

## App-side changes already made
- **`config.edge.ts`** — `DEPLOY_TARGET=dnl` routes everything except DNL surfaces to `/long-read`.
  Allowlist: `/long-read/**`, `/studio/**`, `/curate`, `/signin`, `/signup`, `/onboarding`, `/api/**`.
  The six-mode Rig Wire landing + mode pages never render on the DNL domain.
- **`db.ts`** — auto-disables prepared statements when the connection URL is a pooler
  (`-pooler.` / `pgbouncer=true`), because Neon's transaction-mode pooler can't use them.
  Direct/session URLs (the box tunnel) keep `prepare: true`.

## Env vars (Vercel project → Settings → Environment Variables)
```
DEPLOY_TARGET=dnl
ANALYTICS_DB_URL=postgresql://reader_ro:PWD@ep-…-pooler.eu-central-1.aws.neon.tech/dnl?sslmode=require&pgbouncer=true
RIGWIRE_DB_URL=postgresql://cms_rw:PWD@ep-…-pooler.eu-central-1.aws.neon.tech/dnl?sslmode=require&pgbouncer=true
AUTH_SECRET=<new 32-byte secret>            # openssl rand -base64 32
AUTH_URL=https://<dnl-domain>               # or NEXTAUTH_URL, per Auth.js v5
AUTH_TRUST_HOST=true
CRON_SECRET=<random>                        # protects /api/cron/image-scan; Vercel Cron sends it as Bearer
```
Both DB URLs point at the SAME Neon database (analytics tables replicated in, `rigwire.*` native) so
the reader's cross-schema joins (`analytics.* … LEFT JOIN rigwire.image_checks`) keep working.

## Integration seam — the box's generator and `rigwire.*`
Strong prior: **the Worldwide generator does NOT read `rigwire.editorial_overrides`.** Overrides are a
READER-side layer, applied at read time in `ranking.ts`/`detail.ts`; the generator only writes
`analytics.story_generated_v8`. So moving `rigwire.*` to Neon does not affect generation.
**Confirm on the box** (one grep): `grep -rEi "editorial_overrides|rigwire\." worldwide_gen_v2.py` — if it's
clean, the seam is closed. The real seam is the reverse: **anything that WRITES `rigwire.*` must target
Neon**, not the box:
- CMS API routes → already via `RIGWIRE_DB_URL` (→ Neon). ✓
- **`scripts/image_graphic_check.mjs`** (image cleanliness) — run it with `DATABASE_URL` = the Neon
  `cms_rw` connection so flags land where the reader reads them.

## Launch blockers
1. **Rotate prod creds** — (owner deferred) issue new Neon roles (`reader_ro` least-priv SELECT on the
   replicated tables; `cms_rw` write on `rigwire`, `auth`). Never reuse box passwords.
2. **Admin account — DONE.** `cms-editor-test@rigwire.test` deleted; `tdsworks@gmail.com` provisioned as
   `admin` (argon2id, login verified). Password delivered out-of-band; owner should change on first login.
3. **Image scanner — DONE (automatic).** `src/lib/studio/image-scan.ts` + `GET /api/cron/image-scan`
   (Bearer `CRON_SECRET`), scheduled hourly in `vercel.json` (`limit=40`/run). Notes:
   - Hourly cron needs **Vercel Pro** (Hobby caps crons at once/day). On Hobby, either accept daily or run
     `scripts/image_graphic_check.mjs` (box/one-off) with `DATABASE_URL`=Neon `cms_rw`.
   - `maxDuration=60` (image downloads are network-bound) — also a Pro feature; Hobby caps at 10s, so drop
     `limit` to ~15 there.
   - For the first bulk backfill, run `image_graphic_check.mjs 2000` once against Neon; the cron keeps up after.

## Neon schema checklist (COMPLETE — from a full scan of every SQL query in the app)
Miss any of these and the affected page 500s. The homepage worked but article pages crashed precisely
because **`public.sources` was not replicated** (only the article page joins it).

**A. REPLICATE from the box (read-only reader/CMS tables — logical replication):**
- `analytics.story_clusters_v8`
- `analytics.story_generated_v8`
- `analytics.story_facts_v8`
- `analytics.story_cluster_members_v8`
- `public.articles`
- `public.sources`   ← the one that was missed (detail.ts joins it for image attribution)

**B. NATIVE + WRITABLE on Neon (DNL owns these — create, do NOT replicate):**
- `auth.users`  (login: signup writes, signin reads)  — run the auth-schema migration; provision the admin.
- `rigwire.editorial_overrides`, `rigwire.editorial_audit`, `rigwire.manual_stories`,
  `rigwire.ranking_weights`, `rigwire.image_checks`  (migrations 002/003/004)
- `rigwire.user_preferences`  (reader prefs / onboarding writes)
- `rigwire.onboarding_seed_articles`  (onboarding page reads it — seed it, or onboarding 500s)

`reader_ro` needs SELECT on group A **and** `rigwire.image_checks` (the reader joins it). `cms_rw` needs
write on all of group B.

## Deploy steps
1. Neon: create project (eu-central-1), DB `dnl`, roles `reader_ro`/`cms_rw`; replicate **every table in
   group A above** from the box; create **every table in group B** natively (migrations + auth schema).
2. `vercel` → new project from this repo, region `fra1`, set env vars above.
3. First deploy to a preview URL. Smoke test: `/long-read` renders with data; an article opens; `/studio`
   loads for an editor; `/` and `/minute` redirect to `/long-read`.
4. Point Rig Wire's "Democracy News Live" tile at the DNL domain.
5. Promote to production; attach custom domain.

## Verify after deploy
- `/long-read` 200 with live stories · article page opens · ticker (`/api/ticker`) returns rows.
- `/` → 307 → `/long-read` (mode landing hidden).
- `/studio` gated (signin → editor). CMS write (pin a story) round-trips → reader reflects it.
- No prepared-statement errors in Vercel logs (confirms the pooler fix).
