import { Link } from 'react-router-dom';
import WorkspacePage from '../pages/WorkspacePage';

export default function WorkspaceShell() {
  return (
    <div className="workspace-shell">
      <div className="workspace-shell__classic-link">
        <Link
          to="/classic"
          className="inline-flex items-center rounded-full border border-white/70 bg-white/90 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-gray-900 shadow-lg shadow-black/10 transition hover:bg-white"
        >
          Open Classic UI
        </Link>
      </div>
      <WorkspacePage />
    </div>
  );
}
