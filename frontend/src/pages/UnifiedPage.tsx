import { useState, useRef, useCallback } from 'react';
import { useChat } from '../hooks/useChat';
import { useSession } from '../hooks/useSession';
import { useImages } from '../hooks/useImages';
import { useDrafts } from '../hooks/useDrafts';
import { useTemplates } from '../hooks/useTemplates';
import { useResizing, useMessageContainerResizing } from '../hooks/useResizing';
import Sidebar from '../components/unified/Sidebar';
import HeroFocus from '../components/unified/HeroFocus';
import ChatPanel from '../components/unified/ChatPanel';
import BrowsePanel from '../components/unified/BrowsePanel';
import ImagePanel from '../components/unified/ImagePanel';
import SettingsPanel from '../components/unified/SettingsPanel';
import RightPanel from '../components/unified/RightPanel';
import TemplatesModal from '../components/unified/TemplatesModal';
import DraftsModal from '../components/unified/DraftsModal';
import TemplateCreationModal from '../components/unified/TemplateCreationModal';
import ImageUploadModal from '../components/unified/ImageUploadModal';
import ImageDetailModal from '../components/unified/ImageDetailModal';
import DocumentIngestion from '../components/DocumentIngestion';
import IngestionStatus from '../components/IngestionStatus';
import type {
  UIState,
  ChatState,
  LessonSettings,
  BrowseState,
  SettingsState
} from '../types/unified';
import type { StandardRecord } from '../lib/types';
import { standardLibrary } from '../constants/unified';

export default function UnifiedPage() {
  // Grouped state management
  const [uiState, setUiState] = useState<UIState>({
    mode: 'chat',
    imageModalOpen: false,
  });

  const [draftsModalOpen, setDraftsModalOpen] = useState(false);
  const [templatesModalOpen, setTemplatesModalOpen] = useState(false);
  const [templateCreationModalOpen, setTemplateCreationModalOpen] = useState(false);

  const [chatState, setChatState] = useState<ChatState>({
    input: '',
  });

  const [lessonSettings, setLessonSettings] = useState<LessonSettings>({
    selectedStandard: null,
    selectedGrade: 'Grade 3',
    selectedStrand: 'Connect',
    selectedObjective: null,
    lessonContext: 'Class has recorders and a 30-minute block with mixed instruments.',
    lessonDuration: '30 minutes',
    classSize: '25',
  });

  const [browseState, setBrowseState] = useState<BrowseState>({
    query: '',
  });

  const [settingsState, setSettingsState] = useState<SettingsState>({
    processingMode: 'cloud',
  });

  // State setter functions with proper immutability
  const updateUIState = useCallback((updates: Partial<UIState>) => {
    setUiState(prev => ({ ...prev, ...updates }));
  }, []);

  const updateChatState = useCallback((updates: Partial<ChatState>) => {
    setChatState(prev => ({ ...prev, ...updates }));
  }, []);

  const updateLessonSettings = useCallback((updates: Partial<LessonSettings>) => {
    setLessonSettings(prev => ({ ...prev, ...updates }));
  }, []);

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
  } = useSession();
  const {
    messages,
    isTyping,
    chatError,
    appendMessage,
    processChatMessage,
    resetMessages,
    isLoadingConversation,
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
  } = useDrafts();

  // Template management hook
  const {
    templates,
    isLoading: isLoadingTemplates,
    templateCount,
    getTemplate,
    deleteTemplate,
    createTemplateFromLesson,
  } = useTemplates();

  // Refs - must be declared at top level (React hooks rule)
  const imageFileInputRef = useRef<HTMLInputElement>(null);
  const modalFileInputRef = useRef<HTMLInputElement>(null);

  // Event handlers
  const handleNewConversation = () => {
    resetMessages();
    updateLessonSettings({
      selectedGrade: 'Grade 3',
      selectedStandard: standards[0] ?? standardLibrary[0],
      selectedStrand: 'Connect',
      selectedObjective: null,
    });
    updateUIState({ mode: 'chat' });
  };

  const handleSelectConversation = async (sessionId: string) => {
    const loadedSession = await loadConversation(sessionId);
    
    if (loadedSession) {
      // Update lesson settings based on the loaded session
      updateLessonSettings({
        selectedGrade: loadedSession.grade_level || 'Grade 3',
        selectedStrand: loadedSession.strand_code || 'Connect',
        selectedStandard: loadedSession.selected_standard || null,
        selectedObjective: null,
        lessonContext: loadedSession.additional_context || '',
      });
      
      // Switch to chat mode - messages will be loaded by the useEffect hook in useChat
      updateUIState({ mode: 'chat' });
    }
  };

  const handleSendMessage = () => {
    const trimmed = chatState.input.trim();
    if (!trimmed) return;

    updateChatState({ input: '' });
    processChatMessage(trimmed, setSession);
  };

  const handleStartChat = (standard: StandardRecord, prompt: string) => {
    updateUIState({ mode: 'chat' });
    updateLessonSettings({ selectedStandard: standard });
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
      updateUIState({ mode: 'chat' });
      
      // TODO: Load the draft content into the chat/editor
      // This would require extending the chat system to load draft content
    }
  };

  const handleDeleteDraft = async (draftId: string) => {
    const success = await deleteDraft(draftId);
    if (success) {
      // Draft is automatically removed from the list by the hook
    }
  };

  // Template event handlers
  const handleOpenTemplatesModal = () => {
    setTemplatesModalOpen(true);
  };

  const handleCloseTemplatesModal = () => {
    setTemplatesModalOpen(false);
  };

  const handleOpenTemplateCreationModal = () => {
    setTemplateCreationModalOpen(true);
  };

  const handleCloseTemplateCreationModal = () => {
    setTemplateCreationModalOpen(false);
  };

  const handleSaveTemplate = (name: string, description: string) => {
    // Get the latest lesson content from messages or create a template from current settings
    const lessonContent = messages.length > 0
      ? messages[messages.length - 1].text
      : `Lesson template for ${lessonSettings.selectedGrade} - ${lessonSettings.selectedStrand}`;

    try {
      createTemplateFromLesson(
        lessonContent,
        lessonSettings.selectedStandard,
        {
          grade: lessonSettings.selectedGrade,
          strand: lessonSettings.selectedStrand,
          objective: lessonSettings.selectedObjective,
          lessonContext: lessonSettings.lessonContext,
          lessonDuration: lessonSettings.lessonDuration,
          classSize: lessonSettings.classSize,
        },
        name,
        description
      );
      handleCloseTemplateCreationModal();
    } catch (error) {
      console.error('Failed to create template:', error);
    }
  };

  const handleSelectTemplate = async (templateId: string) => {
    const template = getTemplate(templateId);
    if (template) {
      // Update lesson settings based on the template
      updateLessonSettings({
        selectedGrade: template.grade,
        selectedStrand: template.strand,
        selectedStandard: standards.find(s => s.id === template.standardId) || null,
        selectedObjective: template.objective || null,
        lessonContext: template.content.substring(0, 200) + '...',
        lessonDuration: template.lessonDuration || '30 minutes',
        classSize: template.classSize || '25',
      });
      
      // Close the modal and switch to chat mode
      handleCloseTemplatesModal();
      updateUIState({ mode: 'chat' });
      
      // Optionally, add a message to the chat about using a template
      const templateMessage = `I'm using the "${template.name}" template. ${template.description}`;
      processChatMessage(templateMessage, setSession);
    }
  };

  const handleDeleteTemplate = async (templateId: string) => {
    const success = await deleteTemplate(templateId);
    if (success) {
      // Template is automatically removed from the list by the hook
    }
  };

  return (
    <>
      <div className="flex h-screen">
        {/* Sidebar */}
        <Sidebar
          width={sidebarWidth}
          mode={uiState.mode}
          onModeChange={(newMode) => updateUIState({ mode: newMode })}
          onNewConversation={handleNewConversation}
          onUploadDocuments={() => updateUIState({ mode: 'ingestion' })}
          onUploadImages={() => updateUIState({ imageModalOpen: true })}
          onOpenSettings={() => updateUIState({ mode: 'settings' })}
          conversationGroups={formatSessionsAsConversations()}
          onSelectConversation={handleSelectConversation}
          isLoadingSessions={isLoadingSessions}
          onOpenDraftsModal={handleOpenDraftsModal}
          draftCount={draftCount}
          onOpenTemplatesModal={handleOpenTemplatesModal}
          templateCount={templateCount}
        />

        <div
          id="sidebarResizer"
          className={`resizer ${resizingPanel === 'sidebar' ? 'resizing' : ''}`}
          onMouseDown={(event) => handleResizerMouseDown('sidebar', event)}
        />

        {/* Main Content */}
        <section className="flex-1 flex flex-col panel workspace-panel-glass">
          <HeroFocus
            selectedStandard={lessonSettings.selectedStandard}
            selectedGrade={lessonSettings.selectedGrade}
            selectedStrand={lessonSettings.selectedStrand}
            lessonDuration={lessonSettings.lessonDuration}
            classSize={lessonSettings.classSize}
            session={session}
            sessionError={sessionError}
          />

          {/* Dynamic Content Area */}
          <div className="flex-1 overflow-hidden">
            {uiState.mode === 'chat' && (
              <ChatPanel
                messages={messages}
                isTyping={isTyping}
                chatInput={chatState.input}
                setChatInput={(input) => updateChatState({ input })}
                onSendMessage={handleSendMessage}
                sessionError={sessionError}
                chatError={chatError}
                messageContainerHeight={messageContainerHeight}
                onResizerMouseDown={handleMessageContainerResizerMouseDown}
                resizing={resizingMessageContainer}
                isLoadingConversation={isLoadingConversation}
              />
            )}

            {uiState.mode === 'browse' && (
              <BrowsePanel
                standards={standards}
                selectedGrade={lessonSettings.selectedGrade}
                selectedStrand={lessonSettings.selectedStrand}
                selectedStandard={lessonSettings.selectedStandard}
                browseQuery={browseState.query}
                onGradeChange={(grade) => updateLessonSettings({ selectedGrade: grade })}
                onStrandChange={(strand) => updateLessonSettings({ selectedStrand: strand })}
                onStandardSelect={(standard) => updateLessonSettings({ selectedStandard: standard })}
                onBrowseQueryChange={(query) => updateBrowseState({ query })}
                onStartChat={handleStartChat}
              />
            )}

            {uiState.mode === 'ingestion' && (
              <div className="h-full overflow-y-auto px-6 py-4">
                <div className="max-w-4xl mx-auto">
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold text-ink-800">Document Ingestion</h2>
                    <p className="text-ink-600 mt-2">
                      Upload and process music education documents with AI-powered analysis
                    </p>
                  </div>
                  <DocumentIngestion onIngestionComplete={() => {}} />
                  <div className="mt-8">
                    <IngestionStatus />
                  </div>
                </div>
              </div>
            )}

            {uiState.mode === 'images' && (
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

            {uiState.mode === 'settings' && (
              <SettingsPanel
                processingMode={settingsState.processingMode}
                onProcessingModeChange={(mode) => updateSettingsState({ processingMode: mode })}
              />
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
          selectedStandard={lessonSettings.selectedStandard}
          selectedObjective={lessonSettings.selectedObjective}
          lessonContext={lessonSettings.lessonContext}
          lessonDuration={lessonSettings.lessonDuration}
          classSize={lessonSettings.classSize}
          standards={standards}
          session={session}
          sessionError={sessionError}
          mode={uiState.mode}
          messageCount={messages.length}
          storageInfo={imageHooks.storageInfo}
          isRetryingSession={isRetryingSession}
          retrySuccess={retrySuccess}
          retryMessage={retryMessage}
          onGradeChange={(grade) => updateLessonSettings({ selectedGrade: grade })}
          onStrandChange={(strand) => updateLessonSettings({ selectedStrand: strand })}
          onStandardChange={(standard) => updateLessonSettings({ selectedStandard: standard })}
          onObjectiveChange={(objective) => updateLessonSettings({ selectedObjective: objective })}
          onLessonContextChange={(context) => updateLessonSettings({ lessonContext: context })}
          onLessonDurationChange={(duration) => updateLessonSettings({ lessonDuration: duration })}
          onClassSizeChange={(size) => updateLessonSettings({ classSize: size })}
          onBrowseStandards={() => updateUIState({ mode: 'browse' })}
          onRetrySession={() => retrySession(lessonSettings.selectedGrade, lessonSettings.selectedStrand)}
          onSaveAsTemplate={handleOpenTemplateCreationModal}
        />
      </div>

      {/* Modals */}
      <ImageUploadModal
        isOpen={uiState.imageModalOpen}
        onClose={() => {
          updateUIState({ imageModalOpen: false });
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

      {/* Templates Modal */}
      <TemplatesModal
        isOpen={templatesModalOpen}
        onClose={handleCloseTemplatesModal}
        templates={templates}
        isLoading={isLoadingTemplates}
        onSelectTemplate={handleSelectTemplate}
        onDeleteTemplate={handleDeleteTemplate}
      />

      {/* Template Creation Modal */}
      <TemplateCreationModal
        isOpen={templateCreationModalOpen}
        onClose={handleCloseTemplateCreationModal}
        onSaveTemplate={handleSaveTemplate}
      />

      {/* Drafts Modal */}
      <DraftsModal
        isOpen={draftsModalOpen}
        onClose={handleCloseDraftsModal}
        drafts={drafts}
        isLoading={isLoadingDrafts}
        onOpenDraft={handleOpenDraft}
        onDeleteDraft={handleDeleteDraft}
      />
    </>
  );
}
