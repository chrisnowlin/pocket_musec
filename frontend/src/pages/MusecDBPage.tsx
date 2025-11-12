import { useResizing } from '../hooks/useResizing';
import Sidebar from '../components/unified/Sidebar';

export default function MusecDBPage() {
  const { sidebarWidth, resizingPanel, handleResizerMouseDown } = useResizing(280, 384);

  // Dummy handlers for sidebar
  const handleNewConversation = () => {
    // Placeholder
  };

  const handleSelectConversation = async (sessionId: string) => {
    // Placeholder
  };

  const handleDeleteConversation = (sessionId: string) => {
    // Placeholder
  };

  const handleOpenConversationEditor = (sessionId: string) => {
    // Placeholder
  };

  const handleOpenDraftsModal = () => {
    // Placeholder
  };

  return (
    <>
      <div className="flex h-screen">
        {/* Sidebar */}
        <Sidebar
          width={sidebarWidth}
          mode="chat"
          onModeChange={() => {}}
          onNewConversation={handleNewConversation}
          onUploadDocuments={() => {}}
          onUploadImages={() => {}}
          onOpenSettings={() => {}}
          conversationGroups={[]}
          onSelectConversation={handleSelectConversation}
          isLoadingSessions={false}
          onOpenDraftsModal={handleOpenDraftsModal}
          draftCount={0}
          onDeleteConversation={handleDeleteConversation}
          onOpenConversationEditor={handleOpenConversationEditor}
        />

        <div
          id="sidebarResizer"
          className={`resizer ${resizingPanel === 'sidebar' ? 'resizing' : ''}`}
          onMouseDown={(event) => handleResizerMouseDown('sidebar', event)}
        />

        {/* Main Content */}
        <section className="flex-1 flex flex-col panel workspace-panel-glass">
          <div className="flex-1 flex items-center justify-center bg-ink-900 text-parchment-100">
            <div className="text-center">
              <h1 className="text-3xl font-bold mb-4">MusecDB</h1>
              <p className="text-parchment-300">Coming soon...</p>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

