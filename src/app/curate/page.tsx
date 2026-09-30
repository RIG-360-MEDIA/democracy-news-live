// Curate — the WYSIWYG editor view (epic 002). Renders the EXACT reader front page the client sees,
// wrapped in EditModeProvider so every story card grows a control puck. Editor-gated.

import { getFrontPage } from '@/lib/worldwide/ranking';
import { guardPage } from '@/lib/studio/guard';

import { CurateWorkspace } from './curate-workspace';

export const dynamic = 'force-dynamic';

export default async function Curate() {
  const editor = await guardPage('editor');

  const data = await getFrontPage('world');

  return (
    <div>
      <CurateWorkspace editor={editor.id} canManageSections={editor.isAdmin} data={data} />
    </div>
  );
}
