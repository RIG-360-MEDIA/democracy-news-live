// Admin user management (DNL program P07 S07.01.05). DNL sign-up is invitation-only, so admins create
// accounts here; a new account has an unusable random password until the person opens the one-time
// set-password link. Server-only; callers must enforce requireRole('admin'). Every write is audited (F7).
import 'server-only';

import { randomBytes } from 'node:crypto';

import { hashPassword } from '@/lib/auth/password';
import { sql } from '@/lib/db';
import { writeAudit } from '@/lib/studio/audit-log';

export const ROLES = ['reader', 'editor', 'admin'] as const;
export type Role = (typeof ROLES)[number];

export interface UserRow {
  id: string;
  email: string;
  display_name: string | null;
  role: Role;
  created_at: Date;
}

export async function listUsers(): Promise<UserRow[]> {
  return sql<UserRow[]>`
    SELECT id, email, display_name, role, created_at FROM auth.users ORDER BY role DESC, email
  `;
}

export function normaliseEmail(raw: string): string | null {
  const e = String(raw ?? '').trim().toLowerCase();
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e) && e.length <= 254 ? e : null;
}

/** Create an account (unusable password until the set-password link is used). The insert and its
 *  audit row share one transaction. */
export async function createUser(email: string, displayName: string | null, role: Role, actor: string): Promise<string> {
  const unusable = await hashPassword(randomBytes(32).toString('base64url'));
  const userId = await sql.begin(async (tx) => {
    const rows = await tx<{ id: string }[]>`
      INSERT INTO auth.users (email, password_hash, display_name, role)
      VALUES (${email}, ${unusable}, ${displayName}, ${role})
      RETURNING id
    `;
    const id = rows[0].id;
    await writeAudit(tx, {
      actor,
      action: 'user_create',
      target: `user:${id}`,
      before: null,
      after: { email, displayName, role },
    });
    return id;
  }) as string;
  // Outside the transaction on purpose: RLS may reject this insert (it needs app.user_id), and a
  // failed statement would abort the account creation. Preferences are created on first login otherwise.
  await sql`INSERT INTO rigwire.user_preferences (user_id) VALUES (${userId}) ON CONFLICT (user_id) DO NOTHING`
    .catch(() => undefined);
  return userId;
}

/** Change a user's role, auditing before/after atomically. Returns false (and writes nothing) when
 *  the user is unknown, or when an admin tries to demote themselves (lockout guard — checked against
 *  the DB row, not the client-supplied form email). */
export async function setRole(userId: string, role: Role, actor: string): Promise<boolean> {
  return sql.begin(async (tx) => {
    const rows = await tx<{ email: string; role: Role }[]>`
      SELECT email, role FROM auth.users WHERE id = ${userId} FOR UPDATE
    `;
    const prev = rows[0];
    if (!prev) return false;
    if (prev.email.toLowerCase() === actor.toLowerCase() && role !== 'admin') return false;
    await tx`UPDATE auth.users SET role = ${role}, updated_at = now() WHERE id = ${userId}`;
    await writeAudit(tx, {
      actor,
      action: 'user_role',
      target: `user:${userId}`,
      before: { email: prev.email, role: prev.role },
      after: { email: prev.email, role },
    });
    return true;
  }) as Promise<boolean>;
}

export async function emailTaken(email: string): Promise<boolean> {
  const rows = await sql`SELECT 1 FROM auth.users WHERE lower(email) = ${email} LIMIT 1`;
  return rows.length > 0;
}
