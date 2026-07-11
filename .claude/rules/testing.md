# Rig Wire — Testing

We do not have a test suite yet. This is a deliberate choice for a design-stage
prototype, not an oversight. This file defines (a) what we verify manually
today, and (b) what we adopt the moment we have a real backend or user data.

---

## Today (prototype, all-static content)

Manual verification protocol after every change:

1. `npm run build` — must succeed.
2. `npx tsc --noEmit` — must be clean.
3. Visual check at `/`, `/today`, and any mode page touched.
4. Mobile (iPhone 12 viewport via DevTools) check for any layout change.

That's it. We do not write Jest tests against a JSX tree that is going to be
redesigned three more times this month. Tests calcify exploration; in the
prototype phase that is a bug, not a feature.

## The day we add a backend

Stack:

- **Vitest** — unit and component tests. Jest-compatible API, Vite-native,
  fast.
- **React Testing Library** — component tests. Query by role and text, not
  by class name. If you can't query by role, your component is inaccessible.
- **Playwright** — E2E for the critical user flows: onboarding → first read,
  Flash swipe-through, Pocket queue play, sign-in → resumed reading state.

Coverage floor: 80% for `src/lib/` and any future `src/api/`. 60% for
`src/components/`. Aim higher; do not chase 100% (the last 20% is testing
the test framework).

## What to test (when we test)

Test these because they fail invisibly:

- `src/lib/modes.ts` shape — every mode has the full schema, no orphan fields.
- Article slug routing — `/long-read/[slug]` resolves for every slug in
  `long-reads-data.ts`. The same for any future dynamic route.
- Onboarding flow — preferences persist, can be re-edited, can be skipped.
- Auth shell — sign-in and sign-up share the visual scene without flicker.
- Any future ranking, recommendation, or summarisation logic — **golden tests
  on a fixed input set**, re-run on every model change. A recsys without
  golden tests silently regresses; you will find out from a journalist.
- Any future i18n string lookup — every locale has every key.

Do NOT test these — they are tautologies in a static prototype:

- "MinuteCard renders the title prop."
- "the brand wordmark exists."
- "the page exports a default."

## Test naming

```
describe('<unit-under-test>', () => {
  it('does <behaviour> when <condition>', () => { ... });
});
```

A reader skimming the test file should learn what the unit *does* without
opening the implementation.

## When a test fails

- **Read the failure.** Don't re-run hoping for a different result.
- **Reproduce locally.** A test that's flaky on CI but green locally is
  telling you something about timing, ordering, or environment — not about
  the framework.
- **Fix the code, not the test** — unless the test was wrong, in which case
  delete it and write the correct one. Never mute a test.
