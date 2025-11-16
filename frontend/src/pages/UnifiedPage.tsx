import { useState, useRef, useCallback, useEffect, lazy, Suspense } from 'react';
import { useChat } from '../hooks/useChat';
import { useSession } from '../hooks/useSession';
import { useImages } from '../hooks/useImages';
import { useDrafts } from '../hooks/useDrafts';
import { useResizing, useMessageContainerResizing } from '../hooks/useResizing';
import Sidebar from '../components/unified/Sidebar';
import ChatPanel from '../components/unified/ChatPanel';
import BrowsePanel from '../components/unified/BrowsePanel';
import ImagePanel from '../components/unified/ImagePanel';
import SettingsPanel from '../components/unified/SettingsPanel';
import RightPanel from '../components/unified/RightPanel';
import DraftsModal from '../components/unified/DraftsModal';
import ImageUploadModal from '../components/unified/ImageUploadModal';
import ImageDetailModal from '../components/unified/ImageDetailModal';
import DocumentIngestion from '../components/DocumentIngestion';
import IngestionStatus, { IngestionStatusRef } from '../components/IngestionStatus';
import ErrorBoundary from '../components/ErrorBoundary';
import ToastContainer from '../components/unified/ToastContainer';
import ConfirmDialog from '../components/unified/ConfirmDialog';
import EmbeddingsManager from '../components/EmbeddingsManager';
import { useToast } from '../hooks/useToast';
import api from '../lib/api';
import { frontendToBackendGrade } from '../lib/gradeUtils';
import type {
  BrowseState,
  SettingsState
} from '../types/unified';
import type { StandardRecord } from '../lib/types';
import { useConversationStore } from '../stores/conversationStore';
import { useUIStore } from '../stores/uiStore';

const LessonEditor = lazy(() => import('../components/unified/LessonEditor'));

export default function UnifiedPage() {
  // UI and global state stores
  const mode = useUIStore((state) => state.mode);
  const setMode = useUIStore((state) => state.setMode);
  const imageModalOpen = useUIStore((state) => state.imageModalOpen);
  const setImageModalOpen = useUIStore((state) => state.setImageModalOpen);
  const draftsModalOpen = useUIStore((state) => state.draftsModalOpen);
  const setDraftsModalOpen = useUIStore((state) => state.setDraftsModalOpen);
  const conversationEditor = useUIStore((state) => state.conversationEditor);
  const openConversationEditorUI = useUIStore((state) => state.openConversationEditor);
  const closeConversationEditorUI = useUIStore((state) => state.closeConversationEditor);
  const setConversationEditorSaving = useUIStore((state) => state.setConversationEditorSaving);
  const seedConversationEditor = useUIStore((state) => state.seedConversationEditor);
  const deleteConfirm = useUIStore((state) => state.deleteConfirm);
  const openDeleteConfirm = useUIStore((state) => state.openDeleteConfirm);
  const closeDeleteConfirm = useUIStore((state) => state.closeDeleteConfirm);
  const clearAllHistoryConfirmOpen = useUIStore((state) => state.clearAllHistoryConfirmOpen);
  const setClearAllHistoryConfirmOpen = useUIStore((state) => state.setClearAllHistoryConfirmOpen);

  const lessonSettings = useConversationStore((state) => state.lessonSettings);
  const updateLessonSettings = useConversationStore((state) => state.updateLessonSettings);
  const chatState = useConversationStore((state) => state.chatState);
  const setChatInputValue = useConversationStore((state) => state.setChatInput);

  // Toast notifications
  const { toasts, removeToast, success, error, info } = useToast();

  const [browseState, setBrowseState] = useState<BrowseState>({
    query: '',
  });

  const [settingsState, setSettingsState] = useState<SettingsState>({
    processingMode: 'cloud',
  });

  const updateBrowseState = useCallback((updates: Partial<BrowseState>) => {
    setBrowseState(prev => ({ ...prev, ...updates }));
  }, []);

  const updateSettingsState = useCallback((updates: Partial<SettingsState>) => {
    setSettingsState(prev => ({ ...prev, ...updates }));
  }, []);

  // Custom hooks
  const {
    session,
    sessionError,
    standards,
    setSession,
    retrySession,
    isRetryingSession,
    retrySuccess,
    retryMessage,
    isLoadingSessions,
    loadConversation,
    formatSessionsAsConversations,
    initSession,
    loadSessions,
    loadStandards,
    sessions,
    setSessions,
    updateSelectedModel,
  } = useSession();
  const {
    messages,
    isTyping,
    chatError,
    processChatMessage,
    resetMessages,
    isLoadingConversation,
    updateMessageWithMetadata,
    loadConversationMessages,
    loadDraftContent,
  } = useChat({
    session,
    lessonDuration: lessonSettings.lessonDuration,
    classSize: lessonSettings.classSize
  });

  const imageHooks = useImages();
  const { sidebarWidth, rightPanelWidth, resizingPanel, handleResizerMouseDown } = useResizing(
    256,
    384
  );

  // Ref for IngestionStatus to refresh after ingestion
  const ingestionStatusRef = useRef<IngestionStatusRef>(null);

  const {
    messageContainerHeight,
    resizing: resizingMessageContainer,
    handleResizerMouseDown: handleMessageContainerResizerMouseDown,
  } = useMessageContainerResizing(null);

  // Draft management hook
  const {
    drafts,
    isLoading: isLoadingDrafts,
    draftCount,
    getDraft,
    deleteDraft,
    updateDraft,
  } = useDrafts();


  // Refs - must be declared at top level (React hooks rule)
  const imageFileInputRef = useRef<HTMLInputElement>(null);
  const modalFileInputRef = useRef<HTMLInputElement>(null);

  // Load standards when grade or strand changes
  useEffect(() => {
    loadStandards(lessonSettings.selectedGrade, lessonSettings.selectedStrand);
  }, [lessonSettings.selectedGrade, lessonSettings.selectedStrand, loadStandards]);

  // Event handlers
  const handleNewConversation = async () => {
    // Create a new session with the current lesson settings (not defaults)
    // This allows users to set grade/strand in the right panel before starting a conversation
    const newSession = await initSession(
      lessonSettings.selectedGrade,
      lessonSettings.selectedStrand,
      lessonSettings.selectedStandards.length > 0 ? lessonSettings.selectedStandards[0].id : null,
      lessonSettings.lessonContext || null,
      parseInt(lessonSettings.lessonDuration) || 30,
      parseInt(lessonSettings.classSize) || 25,
      lessonSettings.selectedObjectives,
      lessonSettings.selectedStandards.slice(1) // All standards except the first one
    );
    
    if (newSession) {
      // Update lesson settings to match the created session
      updateLessonSettings({
        selectedGrade: newSession.grade_level || lessonSettings.selectedGrade,
        selectedStrand: newSession.strand_code || lessonSettings.selectedStrand,
        selectedStandards: newSession.selected_standards || [],
        selectedObjectives: newSession.selected_objectives || [],
        lessonContext: newSession.additional_context || lessonSettings.lessonContext,
      });
      
      // Refresh the sessions list so the new conversation appears in Recent Chats
      await loadSessions();
    }
    
    // Reset messages for the new conversation
    resetMessages();
    setMode('chat');
  };

  const handleSelectConversation = async (sessionId: string) => {
    const loadedSession = await loadConversation(sessionId);
    
    if (loadedSession) {
      // Update lesson settings based on the loaded session
      updateLessonSettings({
        selectedGrade: loadedSession.grade_level || 'All Grades',
        selectedStrand: loadedSession.strand_code || 'All Strands',
        selectedStandards: loadedSession.selected_standards || [],
        selectedObjectives: loadedSession.selected_objectives || [],
        lessonContext: loadedSession.additional_context || '',
      });
      
      // Explicitly load conversation messages into the chat UI
      await loadConversationMessages(loadedSession);
      
      // Refresh the sessions list to update timestamps and ensure accurate display
      await loadSessions();
      
      // Switch to chat mode
      setMode('chat');
    }
  };

  const handleSendMessage = () => {
    const trimmed = chatState.input.trim();
    if (!trimmed) return;

    setChatInputValue('');
    processChatMessage(trimmed, setSession);
  };

  const handleUpdateMessage = useCallback((messageId: string, newText: string) => {
    // Use the new function that handles metadata automatically
    updateMessageWithMetadata(messageId, newText);
  }, [updateMessageWithMetadata]);

  const handleStartChat = async (standard: StandardRecord, prompt: string) => {
    setMode('chat');
    updateLessonSettings({ 
      selectedStandards: [standard],
      selectedGrade: standard.grade,
      selectedStrand: standard.strand_name
    });
    
    // Update session with the selected standard if session exists
    if (session?.id) {
      const backendGrade = frontendToBackendGrade(standard.grade);
      const result = await api.updateSession(session.id, {
        grade_level: backendGrade,
        strand_code: standard.strand_code,
        standard_id: standard.id
      });
      if (result.ok) {
        setSession(result.data);
      }
    }
    
    processChatMessage(prompt, setSession);
  };

  // Draft event handlers
  const handleOpenDraftsModal = () => {
    setDraftsModalOpen(true);
  };

  const handleCloseDraftsModal = () => {
    setDraftsModalOpen(false);
  };

  const handleOpenDraft = async (draftId: string) => {
    const draft = await getDraft(draftId);
    if (draft) {
      // Update lesson settings based on the draft
      updateLessonSettings({
        selectedGrade: draft.grade || 'Grade 3',
        selectedStrand: draft.strand || 'Connect',
        lessonContext: draft.content.substring(0, 200) + '...',
      });
      
      // Close the modal and switch to chat mode
      handleCloseDraftsModal();
      setMode('chat');
      
      // Load the draft content into the chat so the user can continue iterating
      loadDraftContent(draft.title, draft.content);

      // Seed the conversation editor so edits start from the selected draft
      const sessionIdFromMetadata = typeof draft.metadata?.['session_id'] === 'string'
        ? (draft.metadata['session_id'] as string)
        : null;
      seedConversationEditor(sessionIdFromMetadata, draft.content);
    }
  };

  const handleDeleteDraft = async (draftId: string) => {
    const success = await deleteDraft(draftId);
    if (success) {
      // Draft is automatically removed from the list by the hook
    }
  };

  const handleEditDraft = async (draftId: string) => {
    const draft = await getDraft(draftId);
    if (draft) {
      // This will be handled by the DraftsModal component's internal edit state
      console.log('Editing draft:', draft);
    }
  };

  const handleUpdateDraft = async (draftId: string, updates: { title?: string; content?: string; metadata?: Record<string, unknown> }) => {
    return await updateDraft(draftId, updates);
  };


  // Conversation menu handlers
  const handleDeleteConversation = (sessionId: string) => {
    openDeleteConfirm(sessionId);
  };

  const confirmDeleteConversation = async () => {
    if (!deleteConfirm.sessionId) return;

    const sessionId = deleteConfirm.sessionId;
    closeDeleteConfirm();

    // Optimistically remove the session from the list immediately
    setSessions(prev => prev.filter(s => s.id !== sessionId));

    try {
      const result = await api.deleteSession(sessionId);
      if (result.ok) {
        success('Conversation deleted successfully');
        // Refresh the sessions list to ensure consistency
        await loadSessions();
        // If the deleted session was the current one, reset
        if (session?.id === sessionId) {
          resetMessages();
          setSession(null);
        }
      } else {
        console.error('Failed to delete conversation:', result.message);
        error(`Failed to delete conversation: ${result.message}`);
        // Revert optimistic update on failure
        await loadSessions();
      }
    } catch (err) {
      console.error('Error deleting conversation:', err);
      error('An error occurred while deleting the conversation.');
      // Revert optimistic update on error
      await loadSessions();
    }
  };

  const cancelDeleteConversation = () => {
    closeDeleteConfirm();
  };

  // Clear all chat history handlers
  const handleClearAllChatHistory = () => {
    setClearAllHistoryConfirmOpen(true);
  };

  const confirmClearAllChatHistory = async () => {
    setClearAllHistoryConfirmOpen(false);

    // Optimistically clear the sessions list immediately
    setSessions([]);

    try {
      const result = await api.deleteAllSessions();
      if (result.ok) {
        success(`Successfully cleared all chat history (${result.data.count} conversation${result.data.count !== 1 ? 's' : ''} deleted)`);
        // Refresh the sessions list to ensure consistency
        await loadSessions();
        // Reset current session and messages
        resetMessages();
        setSession(null);
      } else {
        console.error('Failed to clear chat history:', result.message);
        error(`Failed to clear chat history: ${result.message}`);
        // Revert optimistic update on failure
        await loadSessions();
      }
    } catch (err) {
      console.error('Error clearing chat history:', err);
      error('An error occurred while clearing chat history.');
      // Revert optimistic update on error
      await loadSessions();
    }
  };

  const cancelClearAllChatHistory = () => {
    setClearAllHistoryConfirmOpen(false);
  };

  const handleOpenConversationEditor = async (sessionId: string) => {
    try {
      // First, try to get lesson from drafts
      const draftsResult = await api.getLessonBySession(sessionId);
      let lessonContent = '';

      if (draftsResult.ok && draftsResult.data.length > 0) {
        // Use the most recent lesson
        lessonContent = draftsResult.data[0].content;
      } else {
        // Fallback: try to extract from conversation history
        const sessionResult = await api.getSession(sessionId);
        if (sessionResult.ok && sessionResult.data.conversation_history) {
          try {
            const history = JSON.parse(sessionResult.data.conversation_history);
            // Find the last assistant message that contains lesson content
            for (let i = history.length - 1; i >= 0; i--) {
              if (history[i].role === 'assistant' && history[i].content) {
                const content = history[i].content;
                // Check if it looks like a lesson (contains markdown headers or lesson structure)
                if (content.includes('#') || content.includes('Lesson') || content.length > 200) {
                  lessonContent = content;
                  break;
                }
              }
            }
          } catch (e) {
            console.error('Failed to parse conversation history:', e);
          }
        }
      }

      if (!lessonContent) {
        info('No lesson content found for this conversation.');
        return;
      }

      openConversationEditorUI(sessionId, lessonContent);
    } catch (err) {
      console.error('Error opening conversation editor:', err);
      error('An error occurred while opening the editor.');
    }
  };

  const handleSaveConversationEditor = async (content: string) => {
    const editorSessionId = conversationEditor.sessionId;
    if (!editorSessionId) return;

    setConversationEditorSaving(true);
    try {
      // Try to update existing draft or create new one
      const draftsResult = await api.getLessonBySession(editorSessionId);
      
      if (draftsResult.ok && draftsResult.data.length > 0) {
        // Update existing draft
        const draftId = draftsResult.data[0].id;
        const updateResult = await api.updateDraft(draftId, { content });
        if (updateResult.ok) {
          closeConversationEditorUI();
        } else {
          throw new Error(updateResult.message);
        }
      } else {
        // Create new draft
        const sessionResult = await api.getSession(editorSessionId);
        if (sessionResult.ok) {
          const session = sessionResult.data;
          const createResult = await api.createDraft({
            session_id: editorSessionId,
            title: `${session.grade_level || 'Lesson'} · ${session.strand_code || 'Lesson'} Strand`,
            content,
            metadata: {
              session_id: editorSessionId,
              grade_level: session.grade_level,
              strand_code: session.strand_code,
              standard_id: session.selected_standards?.[0]?.code,
            },
          });
          if (createResult.ok) {
            closeConversationEditorUI();
          } else {
            throw new Error(createResult.message);
          }
        }
      }
    } catch (err: any) {
      console.error('Error saving conversation editor:', err);
      error(`Failed to save: ${err.message || 'Unknown error'}`);
    } finally {
      setConversationEditorSaving(false);
    }
  };

  const handleCancelConversationEditor = () => {
    closeConversationEditorUI();
  };

  return (
    <>
      <div className="flex h-screen">
        {/* Sidebar */}
        <Sidebar
          width={sidebarWidth}
          mode={mode}
          onModeChange={setMode}
          onUploadDocuments={() => setMode('ingestion')}
          onUploadImages={() => setImageModalOpen(true)}
          onOpenSettings={() => setMode('settings')}
          conversationGroups={formatSessionsAsConversations()}
          onSelectConversation={handleSelectConversation}
          isLoadingSessions={isLoadingSessions}
          onOpenDraftsModal={handleOpenDraftsModal}
          draftCount={draftCount}
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
          {/* Dynamic Content Area */}
          <div className="flex-1 overflow-hidden">
            {mode === 'chat' && (
              <ChatPanel
                messages={messages}
                isTyping={isTyping}
                chatInput={chatState.input}
                setChatInput={setChatInputValue}
                onSendMessage={handleSendMessage}
                sessionError={sessionError}
                chatError={chatError}
                messageContainerHeight={messageContainerHeight}
                onResizerMouseDown={handleMessageContainerResizerMouseDown}
                resizing={resizingMessageContainer}
                isLoadingConversation={isLoadingConversation}
                onUpdateMessage={handleUpdateMessage}
                sessionId={session?.id}
                selectedModel={session?.selected_model ?? null}
                onModelChange={(model, updatedSession) => session?.id && updateSelectedModel(session.id, model, updatedSession)}
                processingMode={settingsState.processingMode}
              />
            )}

            {mode === 'browse' && (
              <BrowsePanel
                standards={standards}
                selectedGrade={lessonSettings.selectedGrade}
                selectedStrand={lessonSettings.selectedStrand}
                selectedStandard={lessonSettings.selectedStandards[0] || null}
                browseQuery={browseState.query}
                onGradeChange={(grade) => updateLessonSettings({ selectedGrade: grade })}
                onStrandChange={(strand) => updateLessonSettings({ selectedStrand: strand })}
                onStandardSelect={(standard) => updateLessonSettings({ selectedStandards: [standard] })}
                onBrowseQueryChange={(query) => updateBrowseState({ query })}
                onStartChat={handleStartChat}
              />
            )}

            {mode === 'ingestion' && (
              <div className="h-full overflow-y-auto px-6 py-4">
                <div className="max-w-4xl mx-auto">
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold text-ink-800">Document Ingestion</h2>
                    <p className="text-ink-600 mt-2">
                      Upload and process music education documents with AI-powered analysis
                    </p>
                  </div>
                  <DocumentIngestion 
                    onIngestionComplete={async () => {
                      // Refresh ingestion status after successful ingestion
                      if (ingestionStatusRef.current) {
                        await ingestionStatusRef.current.refresh();
                      }
                    }} 
                  />
                  <div className="mt-8">
                    <IngestionStatus ref={ingestionStatusRef} />
                  </div>
                </div>
              </div>
            )}

            {mode === 'images' && (
              <ImagePanel
                images={imageHooks.images}
                storageInfo={imageHooks.storageInfo}
                selectedImage={imageHooks.selectedImage}
                isUploading={imageHooks.isUploading}
                uploadProgress={imageHooks.uploadProgress}
                uploadError={imageHooks.uploadError}
                imageDragActive={imageHooks.imageDragActive}
                onImageSelect={imageHooks.setSelectedImage}
                onFileSelect={imageHooks.handleFileSelect}
                onDrop={imageHooks.handleDrop}
                onDeleteImage={imageHooks.handleDeleteImage}
                onDragOver={imageHooks.setImageDragActive}
                fileInputRef={imageFileInputRef}
              />
            )}

            {mode === 'settings' && (
              <SettingsPanel
                processingMode={settingsState.processingMode}
                onProcessingModeChange={(mode) => updateSettingsState({ processingMode: mode })}
                onClearChatHistory={handleClearAllChatHistory}
              />
            )}

            {mode === 'embeddings' && (
              <div className="h-full overflow-y-auto">
                <EmbeddingsManager />
              </div>
            )}
          </div>
        </section>

        <div
          id="rightPanelResizer"
          className={`resizer ${resizingPanel === 'right' ? 'resizing' : ''}`}
          onMouseDown={(event) => handleResizerMouseDown('right', event)}
        />

        {/* Right Panel */}
        <RightPanel
          width={rightPanelWidth}
          selectedGrade={lessonSettings.selectedGrade}
          selectedStrand={lessonSettings.selectedStrand}
          selectedStandards={lessonSettings.selectedStandards}
          selectedObjectives={lessonSettings.selectedObjectives}
          lessonContext={lessonSettings.lessonContext}
          lessonDuration={lessonSettings.lessonDuration}
          classSize={lessonSettings.classSize}
          standards={standards}
          session={session}
          sessionError={sessionError}
          mode={mode}
          messageCount={messages.length}
          storageInfo={imageHooks.storageInfo}
          draftCount={draftCount}
          lessonsCount={sessions.length}
          isRetryingSession={isRetryingSession}
          retrySuccess={retrySuccess}
          retryMessage={retryMessage}
          onGradeChange={(grade) => updateLessonSettings({ selectedGrade: grade })}
          onStrandChange={(strand) => updateLessonSettings({ selectedStrand: strand })}
          onSelectedStandardsChange={(standards) => updateLessonSettings({ selectedStandards: standards })}
          onSelectedObjectivesChange={(objectives) => updateLessonSettings({ selectedObjectives: objectives })}
          onLessonContextChange={(context) => updateLessonSettings({ lessonContext: context })}
          onLessonDurationChange={(duration) => updateLessonSettings({ lessonDuration: duration })}
          onClassSizeChange={(size) => updateLessonSettings({ classSize: size })}
          onNewConversation={handleNewConversation}
          onBrowseStandards={() => updateUIState({ mode: 'browse' })}
          onViewConversations={() => {
            updateUIState({ mode: 'chat' });
            // Scroll to sidebar conversations if needed
            const sidebar = document.getElementById('sidebar');
            if (sidebar) {
              sidebar.scrollTo({ top: 0, behavior: 'smooth' });
            }
          }}
          onViewMessages={() => {
            updateUIState({ mode: 'chat' });
            // Scroll to the bottom of the messages container to show latest messages
            setTimeout(() => {
              const messageContainer = document.getElementById('chatMessagesContainer');
              if (messageContainer) {
                messageContainer.scrollTo({ top: messageContainer.scrollHeight, behavior: 'smooth' });
              }
            }, 100);
          }}
          onViewDrafts={handleOpenDraftsModal}
          onRetrySession={() => retrySession(lessonSettings.selectedGrade, lessonSettings.selectedStrand)}
        />
      </div>

      {/* Modals */}
      <ImageUploadModal
        isOpen={imageModalOpen}
        onClose={() => {
          setImageModalOpen(false);
          imageHooks.setImageDragActive(false);
        }}
        isUploading={imageHooks.isUploading}
        uploadProgress={imageHooks.uploadProgress}
        uploadError={imageHooks.uploadError}
        imageDragActive={imageHooks.imageDragActive}
        onDrop={imageHooks.handleDrop}
        onDragOver={imageHooks.setImageDragActive}
        onFileSelect={imageHooks.handleFileSelect}
        fileInputRef={modalFileInputRef}
      />

      <ImageDetailModal
        image={imageHooks.selectedImage}
        onClose={() => imageHooks.setSelectedImage(null)}
        onDelete={imageHooks.handleDeleteImage}
      />

      {/* Drafts Modal */}
      <DraftsModal
        isOpen={draftsModalOpen}
        onClose={handleCloseDraftsModal}
        drafts={drafts}
        isLoading={isLoadingDrafts}
        onOpenDraft={handleOpenDraft}
        onDeleteDraft={handleDeleteDraft}
        onEditDraft={handleEditDraft}
        onUpdateDraft={handleUpdateDraft}
      />

      {/* Conversation Editor Modal */}
      {conversationEditor.open && (
        <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/60 p-4">
          <div className="w-full h-full max-h-[90vh] flex flex-col">
            {conversationEditor.isSaving && (
              <div className="absolute top-4 right-4 z-90 bg-blue-100 text-blue-800 px-3 py-2 rounded-md text-sm flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                Saving lesson...
              </div>
            )}
            <ErrorBoundary>
              <Suspense fallback={<div className="flex-1 flex items-center justify-center text-ink-600">Loading editor...</div>}>
                <LessonEditor
                  content={conversationEditor.content}
                  onSave={handleSaveConversationEditor}
                  onCancel={handleCancelConversationEditor}
                  autoSave={false}
                />
              </Suspense>
            </ErrorBoundary>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteConfirm.open}
        title="Delete Conversation"
        message="Are you sure you want to delete this conversation? This action cannot be undone."
        confirmLabel="Delete"
        cancelLabel="Cancel"
        onConfirm={confirmDeleteConversation}
        onCancel={cancelDeleteConversation}
        variant="danger"
      />

      {/* Clear All History Confirmation Dialog */}
      <ConfirmDialog
        isOpen={clearAllHistoryConfirmOpen}
        title="Clear All Chat History"
        message="Are you sure you want to delete all conversations? This will permanently remove all your chat history and cannot be undone."
        confirmLabel="Clear All"
        cancelLabel="Cancel"
        onConfirm={confirmClearAllChatHistory}
        onCancel={cancelClearAllChatHistory}
        variant="danger"
      />

      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </>
  );
}
