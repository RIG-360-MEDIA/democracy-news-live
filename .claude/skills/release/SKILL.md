---
name: release
description: Cut a versioned release of Rig Wire — runs the full pre-flight, bumps version, writes the changelog entry, tags, and prepares the deploy. Different from /deploy (which can ship untagged commits during prototyping).
---

# Release

A release is a promise. Once the tag is pushed, that bundle is what users
see and what we cite in bug reports. Treat every release as if you'd be
asked to defend it in a post-mortem.

---

## When to cut a release

- A user-visible feature is complete (a new mode page, an onboarding flow).
- A bug fix has been requested by name.
- A weekly cadence cut, even if it's just dependency bumps.

Do NOT cut a release for:

- Work-in-progress branches.
- A single typo fix — let it ride to the next cadence cut.

## Pre-flight

```
npm run build          # green
npx tsc --noEmit       # clean
git status             # empty
git log main..HEAD     # read every commit subject. If you don't recognise one, stop.
```

Visual smoke at every mode page (`/`, `/today`, `/minute`, `/digest`,
`/all-sides`, `/long-read`, `/long-view`, `/queue`, `/onboarding`,
`/signin`, `/signup`).

## Versioning

Semver, but for a frontend prototype the meaning is:

- **MAJOR** — a route renamed, a mode added/removed, the visual identity changed.
- **MINOR** — a new mode page section, a new onboarding step, a new feature.
- **PATCH** — bug fixes, copy tweaks, typography polish.

Until we have a stable backend and external integrators, we stay on `0.x.y`.

## Steps

1. **Bump** version in `package.json`.

2. **Changelog** entry — three bullets max. What changed *for the user*,
   not what changed for the developer.

   ```md
   ## 0.4.0 — 2026-05-28
   - Flash: full-bleed Reels-style feed with swipe-up affordance
   - Today: museum-vitrine shelf with six product covers
   - Auth: animated mode-list scene, six product taglines
   ```

3. **Commit**: `chore(release): 0.4.0`

4. **Tag**: `git tag -a v0.4.0 -m "0.4.0"`

5. **Push**: `git push origin main --follow-tags`

6. **Deploy**: `/deploy --prod` (separate skill, separate confirmation).

## Post-release

- Smoke-check the production URL — every route, no console errors.
- Note any rollback criteria you'd act on in the next 24h.
- If a critical bug is reported, *don't* push a hotfix without bumping to
  `0.4.1`. Untagged hotfixes are how you lose the ability to bisect.

## Rollback

`vercel rollback <previous-url>` — atomic, ~5 seconds. Always faster than
shipping a forward-fix at 11pm.

Do **not** delete the broken deployment. Keep it for the post-mortem —
that URL is evidence. Tag the rollback in your team chat with
`#release-rollback` so it's findable later.
