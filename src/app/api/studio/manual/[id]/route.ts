// Editorial CMS — change a manual story (F9).
//   PATCH  (editor) — edit fields and/or unpublish / republish  { headline?, dek?, body?, topic?,
//                     country?, image_url?, importance?, status?: 'PUBLISHABLE' | 'UNPUBLISHED' }
//   DELETE (admin)  — soft delete: status DELETED, row kept, hidden everywhere
// Each write is audited in the same transaction (manual-edit.ts).
import { revalidateTag } from 'next/cache';
import { NextResponse } from 'next/server';
import { z } from 'zod';

import { CACHE_TAGS } from '@/lib/cache';
import { guardApi } from '@/lib/studio/guard';
import { changeManualStory, ManualStoryError, type ManualStatus, type ManualStoryPatch } from '@/lib/studio/manual-edit';
import { MANUAL_TOPICS } from '@/lib/studio/topics';

export const runtime = 'nodejs';

interface Ctx {
  params: Promise<{ id: string }>;
}

const idSchema = z.string().uuid();

const text = (max: number) => z.string().trim().min(1).max(max);
const optionalText = (max: number) =>
  z
    .string()
    .trim()
    .max(max)
    .nullable()
    .transform((v) => (v ? v : null));

const patchSchema = z
  .object({
    headline: text(300).optional(),
    dek: optionalText(600).optional(),
    body: text(100_000).optional(),
    topic: z.enum(MANUAL_TOPICS).optional(),
    country: optionalText(8).optional(),
    image_url: optionalText(2048).optional(),
    importance: z.number().finite().min(0).max(100).optional(),
    status: z.enum(['PUBLISHABLE', 'UNPUBLISHED']).optional(),
  })
  .strict()
  .refine((b) => Object.values(b).some((v) => v !== undefined), 'Nothing to change');

function fail(code: string, message: string, status: number) {
  return NextResponse.json({ ok: false, data: null, error: { code, message } }, { status });
}

async function apply(id: string, patch: ManualStoryPatch, status: ManualStatus | undefined, editor: string) {
  try {
    const data = await changeManualStory(id, patch, status, editor);
    revalidateTag(CACHE_TAGS.frontPage);
    revalidateTag(CACHE_TAGS.storyDetail);
    return NextResponse.json({ ok: true, data, error: null });
  } catch (e: unknown) {
    if (e instanceof ManualStoryError) return fail(String(e.status), e.message, e.status);
    return fail('500', e instanceof Error ? e.message : 'Update failed', 500);
  }
}

export async function PATCH(req: Request, ctx: Ctx) {
  const guard = await guardApi('editor');
  if (!guard.ok) return guard.response;

  const id = idSchema.safeParse((await ctx.params).id);
  if (!id.success) return fail('400', 'Invalid story id', 400);

  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return fail('400', 'Malformed JSON', 400);
  }
  const parsed = patchSchema.safeParse(raw);
  if (!parsed.success) return fail('400', parsed.error.issues[0]?.message ?? 'Invalid input', 400);

  const { status, image_url, ...fields } = parsed.data;
  const patch: ManualStoryPatch = {
    ...fields,
    ...(image_url !== undefined ? { imageUrl: image_url } : {}),
  };
  return apply(id.data, patch, status, guard.editor.id);
}

export async function DELETE(_req: Request, ctx: Ctx) {
  // Deleting is irreversible from the UI (the row is kept for the record) — admin only.
  const guard = await guardApi('admin');
  if (!guard.ok) return guard.response;

  const id = idSchema.safeParse((await ctx.params).id);
  if (!id.success) return fail('400', 'Invalid story id', 400);

  return apply(id.data, {}, 'DELETED', guard.editor.id);
}
