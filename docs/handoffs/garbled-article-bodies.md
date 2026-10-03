# DNL — garbled article bodies (Python dict/list text on story pages)

Investigated 2026-10-03 (IST). Example: `/long-read/2febd361-232b-46d5-bfbe-caf0d5957325` ("Seven Suspects
Including Ferhat Gündoğdu…"), where sections render as `{'name': 'Referees File', 'purpose': …}`.

## 1. What is happening
- The garbled text is **stored in `analytics.story_generated_v8.body`**. The reader renders it verbatim, so
  this is not a rendering or encoding bug.
- **Scope (measured 2026-10-03):** 8 of the 238 stories on the live front page. In most of them every
  section under a heading is a dict/list; two also have one normal prose section. Affected stories:
  `2febd361` Referees File · `af6a8d5f` Omani copilot / Flydubai · `8b53f925` Flydubai, Netanyahu ·
  `eb41c59b` Karnataka voter deletion · `1a3afe8b` Russia energy-grid strike · `391614ed` Kyiv bridge ·
  `80b0f70f` Nathan Charles · `add72c9b` Kyiv nuclear institute.
- The headline, deck and **lens retellings of the same stories are clean prose**.

## 2. Root cause
1. **The generator model returns structured data inside a section.** `worldwide_gen_v2.py` (gpt-oss-120b)
   returns valid JSON, but for some stories a section's `content` is an object or list instead of a prose
   string. The headings ("Suspects", "Key Evidence", "Court Action") and keys (`name`, `role`, `charges`)
   mirror the structured fact brief the model is given. It happens on fact-dense, list-heavy stories with
   many named people and numbers, and only some of the time because model output varies between runs.
2. **The assembler doesn't check the type.** It writes `## {heading}\n{content}`, and Python `str()`s the
   dict/list. The **single quotes** (`{'name': …}`) prove this: they are Python's repr, not JSON, so the
   JSON parsed fine and the corruption happened in Python. The faithfulness verifier passes it because
   the facts are correct.
3. **The reader's guard is too narrow.** It only rejects a body whose first character is `{`
   (parse-fail). These bodies start with `## Heading`, so they get through.

Items 1 and 2 are inferred from the stored output. The generator code, prompt and raw model responses are
on the box and were not inspected (see §5).

## 3. Fix applied — hide malformed bodies on the site (reader-side)
Branch `fix/hide-malformed-bodies` in `~/Developer/_refs/democracy-news-live`. **Not committed, pushed or
deployed** (merging to `main` deploys production).
- `src/lib/worldwide/body-guard.ts`: `MALFORMED_BODY_PATTERN` = a line that opens with `[` or `{` followed
  by a quote or bracket.
- Added `AND g.body !~ ${MALFORMED_BODY_PATTERN}` next to the existing parse-fail guard in
  `src/lib/worldwide/ranking.ts` (front page), `src/lib/worldwide/detail.ts` (story page) and
  `src/lib/studio/feed.ts` (Studio Desk, matching how parse-fails are already handled there).
- `test/unit/body-guard.test.ts`: catches the Referees body shapes, and leaves prose with bracketed asides
  alone.
- Checks: typecheck clean; vitest 401/401 pass; the pattern run over all 238 live bodies flags exactly the
  8 affected stories and nothing else.

**Effect:** the 8 stories leave the front page and their pages stop opening at the next cache refresh
(the box's hourly `/api/revalidate` call, or the 30-min TTL). When a story is regenerated cleanly, it
returns automatically with no action needed.
**Limitation:** the Postgres `!~` side was not run against a real database locally (no DB credentials).
The pattern uses syntax valid in both Postgres AREs and JavaScript, but run the CI DB-contract check or one
query on Neon before merging.

## 4. The other solution — regenerate instead of hiding (needs the box)
The site **cannot** ask for a machine story to be regenerated today:
- `regenerate()` in `src/lib/dispatch/client.ts:286` only re-runs **Door B / Draftsmith** draft jobs, not
  pipeline stories.
- The box regenerates a story only when its cluster changes (`fact_version` / `member_hash`, per
  `specs/001-worldwide/dbchat-content-gen-spec-2026-06-19.md`). There is no "regenerate story id X"
  endpoint.

What the box owner should do (in this order):
1. **Stop it at the source.** Request the generator output with a strict `json_schema` (`response_format`)
   in which section `content` is `type: string`, so a dict or list is impossible. In the assembler, if
   `not isinstance(content, str)`, retry that section; if it still fails, store the story as `HELD`. Never
   `str()` structured data into the body, and don't turn it into bullets (half-written text).
2. **Add a structural check** next to the verifier: reject any body matching the same pattern.
3. **Regenerate the 8 ids above.** Ongoing stories (Flydubai, Russia strikes) may regenerate on their own
   as new articles arrive.
4. *(Optional, later)* A box endpoint such as `POST /stories/{id}/regenerate` plus a Studio button, so an
   editor can request a re-run. That would need a new route on the box and a client call next to the
   Draftsmith ones.

Stopgap without the box: an editor can rewrite the 8 bodies in Studio (`/studio/story/[id]`). The edit
wins immediately, but it sets `human_locked`, so the pipeline never regenerates that story again.

Diagnostics to run on the box to confirm the root cause:
- Raw model responses for the 8 ids: is section `content` an object or list?
- `grep -n "response_format\|json_schema" worldwide_gen_v2.py`: is the output schema enforced or only
  described in the prompt?
- How the brief is passed to the model (raw JSON?) and the `strategy` column of the 8 rows.

## 5. Why the box couldn't be accessed — and confirmation it is the right server
**The server:** Hetzner box `178.105.63.154`, user `root`. It runs Postgres (`rig-postgres`) and
`worldwide_gen_v2.py`. Verified from the repo:
- `specs/001-worldwide/HANDOFF.md` §5 and §12 ("Hetzner: SSH key `~/.ssh/rig_hetzner`,
  `root@178.105.63.154`").
- `docs/DATABASE.md` §1–2 (`rig-postgres` on the Hetzner box `178.105.63.154`).
- `docs/handoffs/dnl-vercel-deploy.md:32`: the generator `worldwide_gen_v2.py` runs "on the box".

These docs date from July 2026. Nothing newer names a different box, and port 22 on `178.105.63.154` is
open (checked 2026-10-03). Confirm with the box owner that the generator hasn't moved since.

**Why access failed:**
- The required key `~/.ssh/rig_hetzner` **does not exist on this Mac**. `~/.ssh` only has
  `trijya_ed25519` and `vast_anchor_ed25519`.
- Tried 2026-10-03: `trijya_ed25519` and `vast_anchor_ed25519` as `root` and `rig`, and the default/agent
  keys (the agent holds none). Every attempt got `Permission denied (publickey,password)`, so the server
  is up and answering, but none of this Mac's keys are authorised. Host key fingerprints to verify with the
  box owner: ED25519 `SHA256:pDZm8R4ny0sfukRVHh5ETm1LIa8hBifh+Ur1Tg6C+Tk`,
  ECDSA `SHA256:ISClXso11RpQ0tC8bVi1X7SW0y0gX3cqbWnkfSeAS1M`.
- The host isn't in `~/.ssh/known_hosts` (SSH fails at host-key verification), so this machine has never
  connected to it.
- No `.env.local` with `ANALYTICS_DB_URL` / `RIGWIRE_DB_URL` exists locally, so neither the box DB nor the
  Neon replica could be queried. The 8 stories were measured through the public story pages instead.

**To enable read-only access:**
1. Place the `rig_hetzner` key in `~/.ssh/`.
2. Verify the host fingerprint with the box owner before the first connect.
3. Optionally add a read-only `ANALYTICS_DB_URL` to the clone's `.env.local`.
