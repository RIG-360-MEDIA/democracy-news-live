---
name: code-review
description: Review a diff against Rig Wire's CLAUDE.md principles and the six code-style rules. Use after any non-trivial edit, before any commit. Pairs with the /review slash command and the code-reviewer agent.
---

# Code Review

Your job is not to find every possible improvement. It's to find what
*would not pass review*. Two failure modes, both fatal:

1. **You miss a real problem** — a mutation, a dead import, a leaked secret.
2. **You drown the author in bikeshedding** — every preference you have,
   dumped as a comment. They stop reading at #4.

Both lose trust. Pick the BLOCK-worthy issues. Mention FLAGs sparingly.
Skip NOTEs unless the author asked.

---

## Inputs

- The diff (`git diff --cached`, or a path the user named).
- `CLAUDE.md` — the five discipline principles.
- `.claude/rules/code-style.md` — six Rig Wire style rules.
- `STRUCTURE.md` — where things live.
- `src/lib/modes.ts` — mode metadata source of truth.

## What to look for, in priority order

1. **CLAUDE.md violations** — mutation, dead code your change orphaned,
   speculative abstraction, unrelated edits, missing reasoning for a
   non-obvious decision. Always BLOCK.

2. **Cross-mode imports** — `components/<modeA>/x.tsx` importing from
   `components/<modeB>/`. BLOCK.

3. **Hardcoded mode names** — string literals `"Flash"`, `"Newsletter"`,
   `"Worldwide"`, `"Aftermath"`, `"Pocket"`, `"All Sides"`, or their old
   names (`"The Minute"`, `"The Digest"`, `"The Long Read"`, `"The Long
   View"`, `"The Queue"`) appearing anywhere outside `src/lib/modes.ts`.
   BLOCK — rename bug bait.

4. **Mutated state** — `.push`, `.sort` on a state array, `obj.x = y` on a
   prop, `Object.assign` on something not a fresh `{}`. BLOCK.

5. **Type holes** — `any`, `as unknown as`, `// @ts-ignore`. BLOCK unless
   the author has a one-line comment explaining why.

6. **File-size creep** — any file pushed past 800 lines by this diff. BLOCK
   and propose the split.

7. **Tailwind escape hatches** — inline `style={...}` for static values
   that Tailwind can express. FLAG.

8. **Editorial copy in code** — long-form English strings inline in TSX
   instead of in `<feature>-data.ts`. FLAG.

9. **Missing import order** (third-party before alias before relative).
   NOTE.

## Output format

One line per finding:

  <severity>  <file:line>  <problem>  → <fix>

Then a verdict:

- **Ship it.** (zero BLOCKs)
- **Hold.** (list the BLOCKs)

No prose preamble. No closing pleasantries. The author reads the verdict,
fixes, re-runs.

## What you do NOT do

- Do not propose new tests for the static prototype (see `rules/testing.md`).
- Do not rename variables to your preferred style.
- Do not refactor "while you're in there".
- Do not flag the author's diff style; flag the code.
- Do not edit the code yourself — reviewer reviews, author fixes.
