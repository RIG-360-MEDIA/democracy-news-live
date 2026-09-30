// Editorial CMS — commit a Top Stories drag-reorder atomically (F10). Epic 002 `POST /api/studio/reorder`.
import { revalidateTag } from 'next/cache';
import { NextResponse } from 'next/server';
import { z } from 'zod';

import { CACHE_TAGS } from '@/lib/cache';
import { guardApi } from '@/lib/studio/guard';
import { MAX_REORDER } from '@/lib/studio/pins';
import { reorderTopStories } from '@/lib/studio/reorder';

export const runtime = 'nodejs';

const bodySchema = z.object({
  order: z
    .array(z.string().uuid())
    .min(1)
    .max(MAX_REORDER)
    .refine((ids) => new Set(ids).size === ids.length, 'order lists a story more than once'),
});

function fail(code: string, message: string, status: number) {
  return NextResponse.json({ ok: false, data: null, error: { code, message } }, { status });
}

export async function POST(req: Request) {
  const guard = await guardApi('editor');
  if (!guard.ok) return guard.response;

  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return fail('400', 'Malformed JSON', 400);
  }
  const parsed = bodySchema.safeParse(raw);
  if (!parsed.success) return fail('400', parsed.error.issues[0]?.message ?? 'Invalid order', 400);

  try {
    const data = await reorderTopStories(parsed.data.order, guard.editor.id);
    revalidateTag(CACHE_TAGS.frontPage);
    revalidateTag(CACHE_TAGS.storyDetail);
    return NextResponse.json({ ok: true, data, error: null });
  } catch (e: unknown) {
    // Nothing was written: the whole reorder ran in one transaction and rolled back.
    return fail('500', e instanceof Error ? e.message : 'Reorder failed', 500);
  }
}
