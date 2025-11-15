import { useState, useCallback, lazy, Suspense, useMemo } from 'react';
import type { ChatMessage as ChatMessageType } from '../../types/unified';
import type { EnhancedCitation } from '../../types/fileStorage';
import MarkdownRenderer from '../MarkdownRenderer';
import CitationList from './CitationList';
import CitationErrorBoundary from './CitationErrorBoundary';
import { useCitations } from '../../hooks/useCitations';

const LessonEditorLazy = lazy(() => import('./LessonEditor'));

interface ChatMessageProps {
  message: ChatMessageType;
  onUpdateMessage?: (id: string, newText: string) => void;
  lessonId?: string;
  citations?: string[];
}

// Function to detect if content looks like a lesson plan
const isLessonContent = (text: string): boolean => {
  const lessonIndicators = [
    /lesson\s+plan/i,
    /objective/i,
    /standards?\s*(?:alignment|alignment\s*to)?/i,
    /materials?\s*(?:needed|required)?/i,
    /assessment/i,
    /activities?\s*(?:and\s*procedures)?/i,
    /warm\s*up/i,
    /closure/i,
    /grade\s+level/i,
    /duration/i,
    /curriculum/i,
    /learning\s+goals?/i,
    /essential\s+questions?/i,
    /[KM]\d+/i, // NC Music Standards format like K.M.1, 3.M.CR.1, etc.
  ];

  // Check if any lesson indicators are present
  const hasLessonIndicator = lessonIndicators.some(pattern => pattern.test(text));
  
  // Also check for structured content that looks like a lesson
  const hasLessonStructure = (
    text.includes('#') && // Has headers
    (text.includes('##') || text.includes('###')) && // Has subheaders
    text.length > 200 // Reasonable length
  );

  return hasLessonIndicator || hasLessonStructure;
};

export default function ChatMessage({
  message,
  onUpdateMessage,
  lessonId,
  citations = []
}: ChatMessageProps) {
  const [isEditMode, setIsEditMode] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showCitations, setShowCitations] = useState(false);

  // Check if this AI message contains lesson content
  const isEditableLesson = message.sender === 'ai' && isLessonContent(message.text);

  // Handle citations - only load enhanced citations if lessonId is provided
  const { citations: enhancedCitations, loading: citationsLoading, downloadFile } = useCitations({
    lessonId,
    autoLoad: !!lessonId,
  });

  // Use enhanced citations if available, otherwise show nothing (legacy format removed)
  const citationsToShow = enhancedCitations;
  const hasCitations = citationsToShow.length > 0;
  
  const handleEnterEditMode = useCallback(() => {
    if (!isEditableLesson) return;
    setIsEditMode(true);
  }, [isEditableLesson]);

  const handleExitEditMode = useCallback(() => {
    setIsEditMode(false);
  }, []);

  const handleSaveContent = useCallback(async (newContent: string) => {
    if (!onUpdateMessage) return;
    
    // Validate content before saving
    if (!newContent.trim()) {
      console.warn('Cannot save empty content. Please add some content to your lesson.');
      return;
    }
    
    setIsSaving(true);
    try {
      // Update the message with new content
      await onUpdateMessage(message.id, newContent);
      handleExitEditMode();
    } catch (error) {
      console.error('Failed to save message:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      console.warn(`Failed to save changes: ${errorMessage}. Please try again.`);
      // Don't exit edit mode on error so user can retry
    } finally {
      setIsSaving(false);
    }
  }, [message.id, onUpdateMessage, handleExitEditMode]);

  const handleCancelEdit = useCallback(() => {
    handleExitEditMode();
  }, [handleExitEditMode]);

  const memoizedMarkdown = useMemo(() => (
    <MarkdownRenderer content={message.text} className="text-sm leading-relaxed" />
  ), [message.text]);

  return (
    <div
      className={`flex gap-3 items-start ${
        message.sender === 'user' ? 'justify-end' : ''
      }`}
      role="article"
      aria-label={`${message.sender === 'ai' ? 'PocketMusec AI' : 'User'} message${message.isModified ? ' (modified)' : ''}`}
    >
      {message.sender === 'ai' && (
        <div className="w-8 h-8 bg-ink-600 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm" aria-hidden="true">
          <svg
            className="w-5 h-5 text-parchment-100"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
            />
          </svg>
        </div>
      )}
      <div className={message.sender === 'user' ? 'flex justify-end w-full' : 'flex-1 max-w-3xl'}>
        <div
          className={
            message.sender === 'user' ? 'flex flex-col items-end max-w-[80%]' : 'w-full'
          }
        >
          <div
            className={`flex items-center gap-2 mb-2 ${
              message.sender === 'user' ? 'justify-end' : ''
            }`}
          >
            <span className="text-xs font-semibold text-ink-700">
              {message.sender === 'ai' ? 'PocketMusec AI' : 'You'}
            </span>
            <span className="text-xs text-ink-400" aria-hidden="true">•</span>
            <time className="text-xs text-ink-600" dateTime={message.timestamp}>
              Just now
            </time>
            
            {/* Modified indicator */}
            {message.isModified && (
              <>
                <span className="text-xs text-ink-400" aria-hidden="true">•</span>
                <span className="text-xs text-orange-600 font-medium" aria-label="This message has been modified from its original version">
                  Modified
                </span>
              </>
            )}
          </div>
          
          {/* Edit Mode */}
          {message.sender === 'ai' && isEditMode && isEditableLesson ? (
            <div className="w-full" aria-live="polite">
              <Suspense fallback={<div className="p-6 text-sm text-ink-600">Loading editor...</div>}>
                <LessonEditorLazy
                  content={message.text}
                  onSave={handleSaveContent}
                  onCancel={handleCancelEdit}
                  autoSave={false}
                />
              </Suspense>
            </div>
          ) : (
            /* View Mode */
            <div
              className={`group relative rounded-lg shadow-sm border px-4 py-3 transition-all duration-200 ${
                message.sender === 'ai'
                  ? 'bg-parchment-50 border-ink-300 text-ink-800'
                  : 'bg-ink-700 text-parchment-100'
              } ${message.sender === 'user' ? 'w-fit max-w-full' : ''} ${
                isEditableLesson && isHovered ? 'ring-2 ring-ink-400 ring-opacity-50' : ''
                }`}
                data-testid={`chat-message-bubble-${message.id}`}
              onMouseEnter={() => setIsHovered(true)}
              onMouseLeave={() => setIsHovered(false)}
              tabIndex={0}
              onFocus={() => setIsHovered(true)}
              onBlur={() => setIsHovered(false)}
            >
              {/* Edit button overlay */}
              {isEditableLesson && (
                <div
                  className={`absolute top-2 right-2 flex gap-1 transition-opacity duration-200 ${
                    isHovered ? 'opacity-100' : 'opacity-0'
                  }`}
                  aria-hidden={!isHovered}
                >
                  <button
                    onClick={handleEnterEditMode}
                    disabled={isSaving}
                    className="p-1.5 bg-ink-600 text-white rounded-md hover:bg-ink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
                    title="Edit lesson"
                    aria-label="Edit this lesson"
                    aria-describedby={`message-content-${message.id}`}
                  >
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                </div>
              )}

              {/* Message content */}
              <div id={`message-content-${message.id}`}>
                {message.sender === 'ai' ? (
                  memoizedMarkdown
                ) : (
                  <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                    {message.text}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Citations section */}
          {hasCitations && (
            <div className="mt-3 pt-3 border-t border-ink-200" role="region" aria-label="Sources and citations">
              <div className="flex items-center justify-between mb-2">
                <button
                  onClick={() => setShowCitations(!showCitations)}
                  className="flex items-center gap-2 text-sm font-medium text-ink-700 hover:text-ink-900 transition-colors"
                  aria-expanded={showCitations}
                  aria-controls={`citations-list-${message.id}`}
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${showCitations ? 'rotate-90' : ''}`}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  Sources & Citations ({citationsToShow.length})
                </button>
                
                {/* Download all button */}
                {showCitations && citationsToShow.some(c => c.is_file_available && c.can_download) && (
                  <button
                    onClick={() => {
                      const downloadableCitations = citationsToShow.filter(c => c.is_file_available && c.can_download);
                      downloadableCitations.forEach(citation => {
                        if (citation.file_metadata) {
                          downloadFile(citation.file_metadata.file_id, citation.file_metadata.original_filename);
                        }
                      });
                    }}
                    className="text-xs text-ink-600 hover:text-ink-800 transition-colors"
                    aria-label="Download all available citation files"
                  >
                    Download All
                  </button>
                )}
              </div>

              {showCitations && (
                <div 
                  className="space-y-2"
                  id={`citations-list-${message.id}`}
                  role="region"
                  aria-label="Citation details"
                >
                  {citationsLoading ? (
                    <div className="flex items-center gap-2 text-sm text-ink-500 py-2" aria-live="polite">
                      <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Loading citations...
                    </div>
                  ) : (
                    <CitationErrorBoundary>
                      <CitationList
                        citations={citationsToShow}
                        onDownload={downloadFile}
                        compact={true}
                        showFullDetails={false}
                        title=""
                        emptyMessage=""
                      />
                    </CitationErrorBoundary>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
