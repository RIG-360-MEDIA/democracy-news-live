// Manual-story importance → the ranking pool's scale (F11 fix). Pure.
//
// Editors set a manual story's importance on a 0–100 scale (Create form default 40, input schema max
// 100) and that value is STORED unchanged in rigwire.manual_stories.importance. Automated stories are
// scored on a very different scale (ln sources + facts + tier + velocity, × recency — roughly 0.5–3).
// Fed raw into one pool, every CMS story (40) outranked every generated story.
//
// Mapping (the only place it happens): the editor value is read as a PERCENTILE of the current
// automated pool. 0 → the weakest automated story, 50 → the median, 100 → the strongest (ties it, never
// exceeds it), linear interpolation between neighbours; values outside 0–100 are clamped. So "40" means
// "a bit below the middle of today's front page", whatever today's absolute scores are. An editor who
// wants a story to LEAD pins it — a pin's boost is far above any pool score, so a manual 100 never beats
// a pinned rank-1 lead. With no automated stories to compare against (empty pool) the value is mapped
// linearly onto FALLBACK_POOL_RANGE.

import type { StoryCard } from './types';

export const EDITOR_IMPORTANCE_MAX = 100;
export const FALLBACK_POOL_RANGE = { min: 0.5, max: 3 } as const;

/** Map an editor 0–100 importance onto the pool scale given the pool's automated importances. */
export function editorImportanceToPool(value: number, poolImportances: ReadonlyArray<number>): number {
  const v = Number.isFinite(value) ? Math.min(EDITOR_IMPORTANCE_MAX, Math.max(0, value)) : 0;
  const q = v / EDITOR_IMPORTANCE_MAX;
  const sorted = poolImportances.filter(Number.isFinite).slice().sort((a, b) => a - b);
  if (sorted.length === 0) return FALLBACK_POOL_RANGE.min + q * (FALLBACK_POOL_RANGE.max - FALLBACK_POOL_RANGE.min);
  const pos = q * (sorted.length - 1);
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}

/** Manual cards with importance re-expressed on the automated pool's scale (new objects). */
export function placeManualCards(
  manual: ReadonlyArray<StoryCard>,
  automated: ReadonlyArray<StoryCard>,
): StoryCard[] {
  const pool = automated.map((c) => c.importance);
  return manual.map((c) => ({ ...c, importance: editorImportanceToPool(c.importance, pool) }));
}
