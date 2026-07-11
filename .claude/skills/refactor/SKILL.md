---
name: refactor
description: Restructure code without changing behaviour. Use only when the existing structure is actively blocking a change you are about to make — not when you "feel" the code could be cleaner.
---

# Refactor

A refactor that ships in isolation is a refactor that should not have happened.
Refactors are debt payments scheduled the day before you take on new debt in
the same area. If you are not about to add to the file, don't restructure it.

---

## Pre-flight (all must be true)

- [ ] There is a *named* upcoming change that the current structure makes painful.
- [ ] You can describe that change in one sentence.
- [ ] Behaviour will be identical before and after — same outputs, same routes,
      same visual rendering, same error surfaces.
- [ ] You have a way to verify "same behaviour" (build clean, types clean,
      visual diff on the affected page).
- [ ] The refactor is a separate commit from the change that motivated it.

If any box is unchecked, stop. The refactor is premature.

## Protocol

1. **Snapshot.** Note the current visible behaviour: routes that render,
   type signature of the function you're about to touch, screenshots of any
   affected page.

2. **Plan the split.** Write down (in chat, not in code) the new structure
   in 3 bullets max. If you can't, you don't understand the existing
   structure well enough to refactor it.

3. **Move, don't rewrite.** Cut existing code into its new home. Resist the
   urge to "improve" any line you're moving. One git diff per file should
   be a clean rename or a clean cut+paste — no logic deltas mixed in.

4. **Re-verify.** Build clean, types clean, every page from the snapshot
   still renders identically.

5. **Commit.** `refactor: <one-line>`. The commit body lists exactly which
   files moved where. No behavioural changes claimed.

6. **Then** do the new work in a follow-up commit.

## Rig Wire-specific patterns

- **Splitting a mode page** — extract sub-components into the same
  `components/<mode>/` folder. Never lift into `components/` root unless
  used by ≥2 modes.

- **Lifting a primitive** — if `components/<modeA>/<thing>.tsx` is
  duplicated in `<modeB>/`, move both to `components/brand/` or `src/lib/`.
  Trigger is 3+ duplicates. Two copies stay duplicated — abstraction is
  more expensive than redundancy until proven otherwise.

- **Renaming a mode** — touch only `src/lib/modes.ts`. If a string literal
  of the old name appears elsewhere, *that's the bug the refactor is
  fixing* — replace the literal with an import from `modes.ts`.

- **Pulling content out of a component** — move to `<feature>-data.ts` in
  the same folder. Never to a global `content.ts`.

## What refactor is NOT

- It is not a rewrite. A rewrite is a separate decision with its own
  justification, and almost always more expensive than the proponent thinks.
- It is not "modernisation". If `useState` works, leave it.
- It is not "let me extract this into hooks for purity". Extract when
  *reuse arrives*, not before.
- It is not the place for renaming variables to taste.
