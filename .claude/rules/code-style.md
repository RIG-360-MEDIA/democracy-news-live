# Rig Wire — Code Style

Six rules. Every change is reviewed against them. Nothing else is style.

---

## 1. Mode folders are sealed.

`src/components/<mode>/` is a closed world. Components inside one mode folder
**must not** import from another mode folder. Cross-mode primitives go in
`src/components/brand/` or `src/lib/`.

This rule exists because mode pages will evolve at different speeds — Flash
will A/B weekly, Aftermath quarterly. Tight coupling kills that velocity.

WRONG:
  `components/minute/minute-page.tsx` imports `../digest/digest-data`

RIGHT:
  - put the shared thing in `src/lib/`, or
  - duplicate the small piece. Two copies of 30 lines are cheaper than one
    wrong abstraction.

## 2. Data colocates with view.

Per-feature static content lives next to the page that renders it as
`<feature>-data.ts`. Do not centralise content into a single `content.ts`.

Why: when an editor changes a Flash story, they open *one* file. When we
add a seventh mode, we don't grep through a 4000-line content store.

## 3. `modes.ts` is the single source of truth for mode metadata.

Display name, tagline, blurb, color, href, image — ALL of it lives in
`src/lib/modes.ts`. If you find yourself hardcoding `"Flash"`, `"Newsletter"`,
`"Worldwide"`, `"Aftermath"`, `"Pocket"`, or `"All Sides"` anywhere else,
you are creating a future rename bug. Import from `modes.ts`.

## 4. Immutability — return new, never mutate.

ALL state updates produce new objects. No `arr.push`, no `obj.x = y` on
state, no `Object.assign(state, …)`. Use spread, `.map`, `.filter`, `.with`.

React enforces this for hook state. The rule extends to derived data,
reducers, and any helper that touches a shared structure.

## 5. Tailwind utilities first, custom CSS second.

Default to utility classes. Reach for `globals.css` only when:
  - it's a global token (`@font-face`, CSS variable, base reset), or
  - the same arbitrary value appears 4+ times (extract to a utility class).

No inline `style={...}` for things Tailwind can express. The exception is
*dynamic* values: `style={{ width: ${pct}% }}`.

## 6. Typography is a system, not a vibe.

Four families, one role each:

| Family               | Role                                                |
| -------------------- | --------------------------------------------------- |
| Fraunces             | editorial italic display, headlines, masthead       |
| Bricolage Grotesque  | UI display, oversize labels                         |
| Plus Jakarta Sans    | body, UI text, default                              |
| JetBrains Mono       | timestamps, codes, micro-labels                     |

Variable axes (`opsz`, `SOFT`, `WONK` on Fraunces) are tuned in `globals.css`.
Don't introduce new axis values inline.

---

## File size

- Typical: 200–400 lines.
- Soft cap: 500.
- Hard cap: 800. If you cross it, split.

## Naming

- React components — `kebab-case.tsx`, default export named with `PascalCase`.
- Hooks — `use-<thing>.ts`.
- Data files — `<feature>-data.ts`.
- Pages — always `page.tsx` (Next.js requires it).
- Type-only files — `types.ts`, colocated with the feature.

## Imports

Order, top to bottom, with one blank line between groups:

1. React and Next.js
2. Third-party packages
3. `@/lib/...` and other absolute aliases
4. Relative imports (`./`, `../`)
5. Type-only imports (`import type { ... }`)

No deep relative chains (`../../../`). If you need one, the file is in the
wrong folder.
