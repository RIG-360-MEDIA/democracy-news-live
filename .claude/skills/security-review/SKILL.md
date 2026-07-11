---
name: security-review
description: Security pass on changes that touch user input, auth, secrets, or external network calls. Use before merging anything to do with login, signup, API routes, env vars, third-party fetches, or AI-generated user-facing content.
---

# Security Review

The prototype today has no backend, no auth, and no production secrets. That
means most of this review is *forward-looking* — auditing the surfaces that
exist today against the abuses they will face the day we wire them up.

The work is preventing six-month-old design decisions from becoming the bug
you discover at 11pm during a launch.

---

## What to check on every relevant diff

### 1. Secrets — never in source

- No API keys, tokens, passwords, DB connection strings in any file under
  `src/`, `.claude/`, `tools/`, `docs/`, `public/`.
- `.env*.local` and `.env.local` are gitignored. Verify the diff didn't
  accidentally stage a `.env` file.
- If a key appears in a diff, **assume it is compromised**. Rotate it before
  doing anything else, including before removing the commit. The value is
  already in git history.

### 2. User input — validate at the boundary

The auth-shell, signup, signin, and onboarding flows take user input. For
every input field:

- The component must not blindly trust the value (no
  `dangerouslySetInnerHTML` with user content, no `eval`, no template
  injection into `<style>` or `<script>`).
- When we add a real API, validate server-side with a schema (Zod).
  Client-side validation is a UX nicety, not a security control.

### 3. External requests

- No `fetch` to a user-supplied URL without an allowlist (SSRF prevention).
- No `<img src={userValue}>` without scheme validation — `https:` only.
- Third-party scripts (`<Script src=...>`) must be pinned. If loaded from a
  CDN we don't control, include SRI hashes.

### 4. Auth surfaces (forward-looking)

When auth lands:

- Session cookies — `httpOnly`, `SameSite=Lax`, `Secure` in production.
- Password storage — Argon2id. Never bcrypt-only. Never SHA-anything alone.
- Rate-limit signup, signin, and password-reset per-IP and per-email.
- Email enumeration — identical response time and message for "user not
  found" and "wrong password". This is a basic mistake that ships often.

### 5. Personalisation / model output as product (news-AI surface)

When Pocket / Worldwide / All Sides start ranking content with a model:

- The ranking model output IS the product surface. If it can be biased by
  an attacker (vote-brigading, coordinated reading patterns, prompt injection
  via article text), it must be rate-limited and audited.
- Log who saw what and why — which model version, which features, which
  score. Without an audit log, you cannot defend against "your algorithm
  showed me X because of my political views". True or false, you need the
  receipts.
- Pin the model version. A silent model swap changes product behaviour
  without a deploy log entry — that is unshippable in journalism.

### 6. Content safety for AI-generated text

For any AI-summarised or AI-generated text shown to users:

- Faithfulness check before display. Does the summary contradict the
  source? If yes, hide it, do not show "best guess".
- Hard-block phrase list for defamation-bait constructions when the source
  doesn't support them ("X is a criminal", "Y died", "Z resigned").
- A path for editorial override of any AI output, always. If editors can't
  pull a story or override a tag without an engineer, the system isn't
  shippable for a newsroom.

---

## Output

For each finding:

  <severity>  <file:line>  <vulnerability + concrete exploit>  → <fix>

Severities:

- **CRITICAL** — exploitable in production today. Block merge. If a
  CRITICAL is a leaked secret: **rotate first, fix second.**
- **HIGH** — exploitable when the feature lands as designed. Must fix in
  the same PR.
- **MEDIUM** — defence-in-depth gap. Fix in the next release.
- **LOW** — informational. Suggest, don't block.

Close with:

- **Safe to merge.**
- **Hold — fix CRITICAL + HIGH first.**
