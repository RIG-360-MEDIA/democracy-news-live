---
description: Pre-deploy checks + Vercel deploy. Add --prod to ship production.
argument-hint: "[--prod]"
---

Pre-flight (must all pass before the deploy command runs):

1. `npm run build` — must succeed.
2. `npx tsc --noEmit` — must be clean.
3. `git status` — must be empty. Nothing unstaged, nothing untracked that should be committed.
4. Branch sanity — read the current branch back to the user before deploying
   from anything that isn't `main`.

Deploy:

- Preview:    `vercel`
- Production: `vercel --prod`  — **only** if `$ARGUMENTS` contains `--prod`
  **and** the user has confirmed in this turn. Never assume.

Post-deploy:

- Print the deployment URL.
- List the routes for the user to smoke-check (status 200, page renders, no
  console errors):

  ```
  /                  /today
  /minute            /digest            /all-sides
  /long-read         /long-view         /queue
  /signin            /signup            /onboarding
  ```

- On any 500 or hard error in prod: rollback first (`vercel rollback <previous-url>`),
  investigate second.

Never `vercel --prod` without explicit user confirmation in the same turn.
