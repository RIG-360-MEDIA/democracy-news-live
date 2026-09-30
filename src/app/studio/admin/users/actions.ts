'use server';

// Admin user-management actions (P07 S07.01.05). Every action re-checks requireRole('admin') — server
// actions are public endpoints and must never trust the page that rendered the form. Every write is
// audited atomically by the data layer (users.ts / reset-tokens.ts).
import { revalidatePath } from 'next/cache';
import { z } from 'zod';

import { BRAND } from '@/lib/brand';
import { createResetToken } from '@/lib/auth/reset-tokens';
import { requireRole } from '@/lib/studio/session';
import { createUser, emailTaken, normaliseEmail, ROLES, setRole, type Role } from '@/lib/studio/users';

export type LinkState = { ok: true; message: string; link: string } | { ok: false; error: string } | null;

const userIdSchema = z.guid();

function linkFor(token: string): string {
  return `${BRAND.siteUrl}/reset-password?token=${encodeURIComponent(token)}`;
}

function parseRole(v: FormDataEntryValue | null): Role | null {
  return ROLES.includes(String(v) as Role) ? (String(v) as Role) : null;
}

function parseUserId(v: FormDataEntryValue | null): string | null {
  const parsed = userIdSchema.safeParse(String(v ?? ''));
  return parsed.success ? parsed.data : null;
}

export async function createUserAction(_prev: LinkState, form: FormData): Promise<LinkState> {
  const guard = await requireRole('admin');
  if (!guard.ok) return { ok: false, error: 'Admin access required.' };
  const email = normaliseEmail(String(form.get('email') ?? ''));
  const role = parseRole(form.get('role'));
  const name = String(form.get('displayName') ?? '').trim().slice(0, 120) || null;
  if (!email) return { ok: false, error: 'Enter a valid email address.' };
  if (!role) return { ok: false, error: 'Choose a role.' };
  if (await emailTaken(email)) return { ok: false, error: 'An account with that email already exists.' };
  const userId = await createUser(email, name, role, guard.editor.id);
  const token = await createResetToken(userId, guard.editor.id);
  console.info('[admin-users] created', { by: guard.editor.id, email, role });
  revalidatePath('/studio/admin/users');
  return { ok: true, message: `Account created for ${email}. Send them this one-time link to set a password (valid 72 h):`, link: linkFor(token) };
}

export async function resetLinkAction(_prev: LinkState, form: FormData): Promise<LinkState> {
  const guard = await requireRole('admin');
  if (!guard.ok) return { ok: false, error: 'Admin access required.' };
  const userId = parseUserId(form.get('userId'));
  const email = String(form.get('email') ?? '');
  if (!userId) return { ok: false, error: 'Unknown user.' };
  const token = await createResetToken(userId, guard.editor.id);
  console.info('[admin-users] reset link', { by: guard.editor.id, userId });
  return { ok: true, message: `One-time password link for ${email} (valid 72 h; any older link is revoked):`, link: linkFor(token) };
}

export async function setRoleAction(form: FormData): Promise<void> {
  const guard = await requireRole('admin');
  if (!guard.ok) return;
  const userId = parseUserId(form.get('userId'));
  const email = String(form.get('email') ?? '');
  const role = parseRole(form.get('role'));
  if (!role || !userId) return;
  // Lockout guard: an admin can't demote themselves.
  if (email.toLowerCase() === guard.editor.id.toLowerCase() && role !== 'admin') return;
  const changed = await setRole(userId, role, guard.editor.id);
  if (!changed) return;
  console.info('[admin-users] role', { by: guard.editor.id, userId, role });
  revalidatePath('/studio/admin/users');
}
