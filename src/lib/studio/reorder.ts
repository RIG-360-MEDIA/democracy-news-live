// Editorial CMS — Top Stories drag-reorder as ONE transaction (F10).
//
// The /curate overlay used to commit a reorder as N sequential single pins: a failure half-way left
// the page in a mixed old/new order, and every pin lived forever. Now the whole new order is written
// in a single sql.begin: current pins not in the new order are unpinned, the order is pinned 1..n with
// a fresh expiry, and every row change is audited on the same transaction. Any failure (including the
// audit insert, or migration 008's one-pin-per-rank constraint at commit) rolls all of it back.

import { sql } from '@/lib/db';

import { writeOverride } from './overrides';
import { planReorder, validateOrder } from './pins';

export interface ReorderResult {
  pinned: Array<{ storyId: string; rank: number }>;
  unpinned: string[];
}

export async function reorderTopStories(order: ReadonlyArray<string>, editorId: string): Promise<ReorderResult> {
  const invalid = validateOrder(order);
  if (invalid) throw new RangeError(invalid);
  return sql.begin(async (tx) => {
    const current = (await tx`
      SELECT story_id FROM rigwire.editorial_overrides WHERE action = 'pinned' FOR UPDATE
    `) as unknown as Array<{ story_id: string }>;
    const plan = planReorder(order, current.map((r) => r.story_id));
    for (const storyId of plan.unpin) {
      // eslint-disable-next-line no-await-in-loop -- sequential on one transaction by design.
      await writeOverride(tx, storyId, { action: 'live', pinnedRank: null }, editorId, 'unpin', { displace: false });
    }
    for (const { storyId, rank } of plan.pin) {
      // eslint-disable-next-line no-await-in-loop -- sequential on one transaction by design.
      await writeOverride(tx, storyId, { action: 'pinned', pinnedRank: rank }, editorId, 'reorder', { displace: false });
    }
    return { pinned: plan.pin, unpinned: plan.unpin };
  }) as Promise<ReorderResult>;
}
