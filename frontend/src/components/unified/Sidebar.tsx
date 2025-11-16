import { useNavigate } from 'react-router-dom';
import type { ViewMode, ConversationGroup } from '../../types/unified';
import { quickAccessLinks } from '../../constants/unified';
import ConversationMenu from './ConversationMenu';

interface SidebarProps {
  width: number;
  mode: ViewMode;
  onModeChange: (mode: ViewMode) => void;
  onBrowseStandards: () => void;
  onUploadDocuments: () => void;
  onUploadImages: () => void;
  onOpenSettings: () => void;
  conversationGroups: ConversationGroup[];
  onSelectConversation: (sessionId: string) => Promise<void>;
  isLoadingSessions: boolean;
  // Draft management props
  onOpenDraftsModal: () => void;
  draftCount: number;
  // Conversation menu props
  onDeleteConversation: (sessionId: string) => void;
  onOpenConversationEditor: (sessionId: string) => void;
}

export default function Sidebar({
  width,
  mode,
  onModeChange,
  onUploadDocuments,
  onUploadImages,
  onOpenSettings,
  conversationGroups,
  onSelectConversation,
  isLoadingSessions,
  onOpenDraftsModal,
  draftCount,
  onDeleteConversation,
  onOpenConversationEditor,
}: SidebarProps) {
  const navigate = useNavigate();

  return (
    <aside
      id="sidebar"
      className="bg-ink-800 text-parchment-100 flex flex-col panel overflow-hidden"
      style={{ width: `${width}px`, minWidth: '200px', maxWidth: '400px' }}
    >
      <div className="p-4 border-b border-ink-700">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-gradient-to-br from-ink-600 to-ink-700 rounded-lg flex items-center justify-center">
            <svg
              className="w-6 h-6 text-parchment-100"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
              />
            </svg>
          </div>
          <div>
            <h1 className="font-bold">PocketMusec</h1>
            <p className="text-xs text-parchment-300">AI Assistant</p>
          </div>
        </div>
      </div>

      <div className="p-3 border-b border-ink-700">
        <div className="bg-ink-700 rounded-lg p-1 flex flex-wrap gap-1">
          {(['chat', 'images', 'settings'] as ViewMode[]).map(
            (viewMode) => (
              <button
                key={viewMode}
                onClick={() => onModeChange(viewMode)}
                className={`flex-1 px-2 py-1.5 text-xs font-medium rounded capitalize ${
                  mode === viewMode
                    ? 'bg-ink-600 text-parchment-100'
                    : 'text-parchment-300 hover:text-parchment-100 transition-colors'
                }`}
              >
                {viewMode}
              </button>
            )
          )}
        </div>
      </div>

      <nav className="flex-1 scrollable p-3 space-y-1">
        {mode === 'chat' && (
          <>
            {isLoadingSessions ? (
              <div className="px-3 py-2 text-parchment-400 text-sm">
                Loading conversations...
              </div>
            ) : conversationGroups.length === 0 ? (
              <div className="px-3 py-2 text-parchment-400 text-sm">
                No previous conversations
              </div>
            ) : (
              conversationGroups.map((group) => (
                <div key={group.label} className="mb-4">
                  <h3 className="px-3 text-xs font-semibold text-parchment-300 uppercase mb-2">
                    {group.label}
                  </h3>
                  <div className="space-y-1">
                    {group.items.map((item) => (
                      <div
                        key={item.id}
                        className={`relative flex items-center group ${
                          item.active
                            ? 'bg-ink-700 text-parchment-100'
                            : 'text-parchment-200 hover:bg-ink-700 hover:text-parchment-100'
                        } rounded-lg transition-colors`}
                      >
                        <button
                          onClick={() => onSelectConversation(item.id)}
                          className="flex-1 text-left px-3 py-2 rounded-lg transition-colors"
                        >
                          <div className="text-sm font-medium truncate">{item.title}</div>
                          <div className="text-xs text-parchment-400">{item.hint}</div>
                        </button>
                        <div className="pr-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <ConversationMenu
                            sessionId={item.id}
                            onDelete={onDeleteConversation}
                            onOpenEditor={onOpenConversationEditor}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </>
        )}

        <div className="pt-4 mt-4 border-t border-ink-700">
          <h3 className="px-3 text-xs font-semibold text-parchment-300 uppercase mb-2">
            Quick Access
          </h3>
          <div className="space-y-1 mb-4">
            <button
              onClick={onOpenDraftsModal}
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-parchment-200 hover:bg-ink-700 hover:text-parchment-100 w-full"
            >
              <span className="text-sm">Saved Drafts</span>
              <span className="ml-auto text-xs text-parchment-400">
                {draftCount > 0 ? `${draftCount} draft${draftCount !== 1 ? 's' : ''}` : 'No drafts'}
              </span>
            </button>
          </div>

          <h3 className="px-3 text-xs font-semibold text-parchment-300 uppercase mb-2 mt-4">
            Quick Actions
          </h3>
          <div className="space-y-1">
            <button
              onClick={onUploadDocuments}
              className="w-full text-left px-3 py-2 rounded-lg text-parchment-200 hover:bg-ink-700 hover:text-parchment-100"
            >
              <span className="text-sm">📄 Upload Documents</span>
            </button>
            <button
              onClick={onUploadImages}
              className="w-full text-left px-3 py-2 rounded-lg text-parchment-200 hover:bg-ink-700 hover:text-parchment-100"
            >
              <span className="text-sm">🖼️ Upload Images</span>
            </button>
            <button
              onClick={onOpenSettings}
              className="w-full text-left px-3 py-2 rounded-lg text-parchment-200 hover:bg-ink-700 hover:text-parchment-100"
            >
              <span className="text-sm">⚙️ Settings</span>
            </button>
          </div>
        </div>
      </nav>

      <div className="p-3 border-t border-ink-700">
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => navigate('/')}
            className="bg-ink-600 hover:bg-ink-700 text-parchment-100 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
          >
            PocketMusec
          </button>
          <button
            onClick={() => navigate('/planner')}
            className="bg-ink-600 hover:bg-ink-700 text-parchment-100 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
          >
            PocketPlanner
          </button>
          <button
            onClick={() => navigate('/db')}
            className="bg-ink-600 hover:bg-ink-700 text-parchment-100 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
          >
            MusecDB
          </button>
          <button
            onClick={() => navigate('/tracker')}
            className="bg-ink-600 hover:bg-ink-700 text-parchment-100 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
          >
            MusecTracker
          </button>
        </div>
      </div>
    </aside>
  );
}
