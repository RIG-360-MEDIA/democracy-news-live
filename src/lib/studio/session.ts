// Editorial CMS — editor identity + THE authorization guard (epic 002, E7; F8 roles).
//
// requireRole() is the single role check for every Studio surface: API routes, pages and server
// actions all go through it (directly for actions, or via the thin guardApi/guardPage adapters in
// ./guard.ts). It distinguishes 401 (not signed in) from 403 (signed in, insufficient role) so API
// routes and pages can respond correctly per .claude/rules/api-conventions.md.
//
//   'editor' — newsroom work (desk, queue, stories, drafts, merges, manual stories, audit).
//              Satisfied by role editor OR admin.
//   'admin'  — feed-wide configuration (sources, weights/sections, /studio/admin/*). Admin only.
//   reader   — never satisfies either; a signed-in reader gets 403 everywhere in the Studio.
//
// The full route → role policy is enforced by test/unit/studio-role-matrix.test.ts, which fails
// when a new Studio route/page/action is added without a declared role.

import { auth } from '@/lib/auth';
import { isAdmin, isEditor } from '@/lib/auth/roles';

export type StudioRole = 'editor' | 'admin';

export interface EditorIdentity {
  /** Stable id used for audit/display — email, falling back to name, then user id. */
  id: string;
  role: string;
  isAdmin: boolean;
}

export type EditorGuard =
  | { ok: true; editor: EditorIdentity }
  | { ok: false; status: 401 | 403 };

function satisfies(required: StudioRole, role: string | null | undefined): boolean {
  return required === 'admin' ? isAdmin(role) : isEditor(role);
}

/** Resolve the signed-in user and check they hold `required` (or better). */
export async function requireRole(required: StudioRole): Promise<EditorGuard> {
  // DEV-ONLY local verification bypass — INERT in production (Vercel sets NODE_ENV=production, so this
  // branch is dead code there). It exists only so a developer can run the CMS against the box to verify
  // UI without minting a login credential. NEVER set CMS_DEV_EDITOR in any deployed environment.
  if (process.env.NODE_ENV !== 'production' && process.env.CMS_DEV_EDITOR === '1') {
    return { ok: true, editor: { id: 'dev@local', role: 'admin', isAdmin: true } };
  }
  const session = await auth();
  const u = session?.user;
  if (!u) return { ok: false, status: 401 };
  if (!satisfies(required, u.role)) return { ok: false, status: 403 };
  return {
    ok: true,
    editor: { id: u.email ?? u.name ?? u.id, role: u.role, isAdmin: isAdmin(u.role) },
  };
}
