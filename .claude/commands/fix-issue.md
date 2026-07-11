---
description: Reproduce and fix a GitHub issue by number or description.
argument-hint: "<issue-number-or-description>"
---

Fix $ARGUMENTS.

Workflow (do not skip steps):

1. **Read the issue.** If `$ARGUMENTS` is numeric: `gh issue view $ARGUMENTS`.
   Otherwise treat it as a description and ask the user to confirm the scope
   if anything is ambiguous.

2. **Reproduce.** Write the failing test or the manual repro recipe that
   captures the bug. Run it. Confirm it fails for the reason claimed. If you
   cannot reproduce, **stop** and report what you tried — do not guess-fix.

3. **Localize.** Read the minimum set of files needed to understand the
   failure. Resist exploration drift. If you've opened more than 5 files,
   you've lost the thread — narrow the search.

4. **Fix.** Smallest change that makes the test pass / fixes the symptom.
   No adjacent cleanup. No new abstractions. No "while I'm in there".

5. **Verify.**
   - `npm run build` is green.
   - `npx tsc --noEmit` is green.
   - The repro from step 2 no longer reproduces.

6. **Commit.** `fix: <one-line summary> (#<issue>)`. Body lists the file(s)
   changed and one sentence on why.

Surface uncertainty out loud — "I think the bug is in X but Y might also be
involved" beats silently picking one. The user can redirect; you cannot undo
a wrong silent choice.
