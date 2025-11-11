import { useState, useRef, useCallback } from 'react';
import { useChat } from '../hooks/useChat';
import { useSession } from '../hooks/useSession';
import { useImages } from '../hooks/useImages';
import { useResizing, useMessageContainerResizing } from '../hooks/useResizing';
import Sidebar from '../components/unified/Sidebar';
import HeroFocus from '../components/unified/HeroFocus';
import ChatPanel from '../components/unified/ChatPanel';
import BrowsePanel from '../components/unified/BrowsePanel';
import ImagePanel from '../components/unified/ImagePanel';
import SettingsPanel from '../components/unified/SettingsPanel';
import RightPanel from '../components/unified/RightPanel';
import ImageUploadModal from '../components/unified/ImageUploadModal';
import ImageDetailModal from '../components/unified/ImageDetailModal';
import DocumentIngestion from '../components/DocumentIngestion';
import IngestionStatus from '../components/IngestionStatus';
import type {
  ViewMode,
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
  const { session, sessionError, standards, setSession } = useSession();
  const {
    messages,
    isTyping,
    chatError,
    appendMessage,
    processChatMessage,
    resetMessages,
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

  const handleSendMessage = () => {
    const trimmed = chatState.input.trim();
    if (!trimmed) return;

    appendMessage('user', trimmed);
    updateChatState({ input: '' });
    processChatMessage(trimmed, setSession);
  };

  const handleStartChat = (standard: StandardRecord, prompt: string) => {
    updateUIState({ mode: 'chat' });
    updateLessonSettings({ selectedStandard: standard });
    appendMessage('user', prompt);
    processChatMessage(prompt, setSession);
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
                fileInputRef={useRef<HTMLInputElement>(null)}
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
          onGradeChange={(grade) => updateLessonSettings({ selectedGrade: grade })}
          onStrandChange={(strand) => updateLessonSettings({ selectedStrand: strand })}
          onStandardChange={(standard) => updateLessonSettings({ selectedStandard: standard })}
          onObjectiveChange={(objective) => updateLessonSettings({ selectedObjective: objective })}
          onLessonContextChange={(context) => updateLessonSettings({ lessonContext: context })}
          onLessonDurationChange={(duration) => updateLessonSettings({ lessonDuration: duration })}
          onClassSizeChange={(size) => updateLessonSettings({ classSize: size })}
          onBrowseStandards={() => updateUIState({ mode: 'browse' })}
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
        fileInputRef={useRef<HTMLInputElement>(null)}
      />

      <ImageDetailModal
        image={imageHooks.selectedImage}
        onClose={() => imageHooks.setSelectedImage(null)}
        onDelete={imageHooks.handleDeleteImage}
      />
    </>
  );
}
