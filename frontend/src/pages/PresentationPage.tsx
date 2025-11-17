import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useResizing } from '../hooks/useResizing';
import Sidebar from '../components/unified/Sidebar';
import PresentationManagement from '../components/presentation/PresentationManagement';
import PresentationCreator from '../components/presentation/PresentationCreator';

type TabType = 'manage' | 'create';

const PresentationPage: React.FC = () => {
  const navigate = useNavigate();
  const { sidebarWidth, resizingPanel, handleResizerMouseDown } = useResizing(280, 384);
  const [activeTab, setActiveTab] = useState<TabType>('manage');

  const handlePresentationGenerated = (presentationId: string) => {
    // Navigate to the presentation viewer directly
    navigate(`/presentations/${presentationId}`);
  };

  const handleViewPresentation = (presentationId: string) => {
    // Navigate to the presentation viewer directly
    navigate(`/presentations/${presentationId}`);
  };

  // Dummy handlers for sidebar
  const handleBrowseStandards = () => {
    // Placeholder
  };

  const handleSelectConversation = async (_sessionId: string) => {
    // Placeholder
  };

  const handleDeleteConversation = (_sessionId: string) => {
    // Placeholder
  };

  const handleOpenConversationEditor = (_sessionId: string) => {
    // Placeholder
  };

  const handleOpenDraftsModal = () => {
    // Placeholder - could navigate to unified page if needed
    navigate('/');
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <Sidebar
        width={sidebarWidth}
        mode="chat"
        onModeChange={() => {}}
        onBrowseStandards={handleBrowseStandards}
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
        <div className="flex-1 flex flex-col bg-ink-900">
          {/* Header */}
          <div className="bg-ink-800 border-b border-ink-700 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-parchment-100">Presentations</h1>
                <p className="text-parchment-300 text-sm mt-1">
                  Create and manage your AI-generated presentations
                </p>
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="bg-ink-700 border-b border-ink-600">
            <div className="flex space-x-1 px-6">
              <button
                onClick={() => setActiveTab('manage')}
                className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'manage'
                    ? 'text-parchment-100 border-parchment-300'
                    : 'text-parchment-400 border-transparent hover:text-parchment-200'
                }`}
              >
                <span className="flex items-center gap-2">
                  📋 Manage Presentations
                </span>
              </button>
              <button
                onClick={() => setActiveTab('create')}
                className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'create'
                    ? 'text-parchment-100 border-parchment-300'
                    : 'text-parchment-400 border-transparent hover:text-parchment-200'
                }`}
              >
                <span className="flex items-center gap-2">
                  ✨ Create New Presentation
                </span>
              </button>
            </div>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-auto bg-parchment-200">
            {activeTab === 'manage' && (
              <PresentationManagement onViewPresentation={handleViewPresentation} />
            )}
            {activeTab === 'create' && (
              <PresentationCreator onPresentationGenerated={handlePresentationGenerated} />
            )}
          </div>
        </div>
      </section>
    </div>
  );
};

export default PresentationPage;