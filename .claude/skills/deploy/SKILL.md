---
name: deploy
description: Ship a build to Vercel. Wraps the /deploy command with broader context — preview vs prod, smoke checks, rollback plan, what deploy is and isn't.
---

# Deploy

A deploy is a state change you can't undo with `git revert`. That makes it
different from a commit. Treat it that way.

---

## Two modes

- **Preview** — every push to a non-`main` branch gets a unique URL. Cheap,
  fast, use these aggressively to share with users for feedback.
- **Production** — `vercel --prod`. The user-facing URL. Requires explicit
  user confirmation in the same turn as the deploy.

## Pre-deploy (every time)

1. `npm run build` is green.
2. `npx tsc --noEmit` is green.
3. `git status` is clean.
4. The branch you are deploying is the branch you intend to deploy. Read
   it out loud (or to the user). Wrong-branch deploys are how you ship
   someone else's half-finished work.

## Smoke check (after every prod deploy)

Open each route in the live deployment, confirm it renders without console
errors:

```
/                  landing
/today             newsstand
/minute            Flash feed
/digest            Newsletter
/all-sides         All Sides
/long-read         Worldwide index
/long-read/<slug>  one article
/long-view         Aftermath flip-book
/queue             Pocket
/signin /signup    auth scene
/onboarding        first-run flow
```

If any route 500s or shows a console error, **rollback first, investigate
second**.

## Rollback

`vercel rollback <previous-url>` — atomic, ~5 seconds. Always faster than
shipping a forward-fix at 11pm with adrenaline in your bloodstream.

Keep the broken deployment up (don't delete) — that URL is the post-mortem
evidence.

## What deploy is NOT

- It is not a release. A release is a tagged version with a changelog (see
  `skills/release`). A deploy can ship an untagged commit during prototyping;
  a release cannot.
- It is not a place to run migrations. When we have a database, migrations
  run as a separate, idempotent step *before* the deploy that depends on
  them. Never inline.
- It is not where you debug. Reproduce locally. Deploy known-good.
- It is not a way to "see if it works in prod". If you don't trust your
  local build, your local build is the bug — fix that first.
