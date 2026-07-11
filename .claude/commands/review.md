---
description: Review staged or named changes against CLAUDE.md + code-style rules.
argument-hint: "[path-or-commit-range]"
---

Run a review of $ARGUMENTS against the five principles in `CLAUDE.md` and the
six Rig Wire rules in `.claude/rules/code-style.md`.

If no argument is given: review the staged diff (`git diff --cached`).
If the argument is a path: review that file.
If it's a commit range (e.g. `HEAD~3..HEAD`): review that diff.

For each finding emit one line:

  <severity>  <file:line>  <one-sentence problem>  → <one-sentence fix>

Severities:
- **BLOCK** — violates a CLAUDE.md principle or a code-style rule (mutation,
  dead code, hardcoded mode name, cross-mode import, speculative abstraction)
- **FLAG** — works but smells (style mismatch, unclear naming, missing error
  path, file pushed past 500 lines)
- **NOTE** — worth knowing, not worth blocking

Close with one of:
- **Ship it.** — no BLOCKs.
- **Hold.** — list the BLOCKs that must be resolved first.

Do not propose unrelated improvements. Do not refactor while reviewing. Do not
flag style preferences not in the rules. Operate surgically.
