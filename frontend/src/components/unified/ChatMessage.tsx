import { useState, useCallback } from 'react';
import type { ChatMessage as ChatMessageType } from '../../types/unified';
import type { EnhancedCitation } from '../../types/fileStorage';
import MarkdownRenderer from '../MarkdownRenderer';
import LessonEditor from './LessonEditor';
import CitationList from './CitationList';
import CitationErrorBoundary from './CitationErrorBoundary';
import { useCitations, useLegacyCitations } from '../../hooks/useCitations';

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

  // Handle citations - use enhanced citations if lessonId is provided, otherwise use legacy
  const { citations: enhancedCitations, loading: citationsLoading, downloadFile } = useCitations({
    lessonId,
    autoLoad: !!lessonId && citations.length > 0,
  });

  const { enhancedCitations: legacyCitations } = useLegacyCitations(citations);

  // Determine which citations to show
  const citationsToShow = lessonId ? enhancedCitations : legacyCitations;
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
    
    setIsSaving(true);
    try {
      // Update the message with new content
      onUpdateMessage(message.id, newContent);
      handleExitEditMode();
    } catch (error) {
      console.error('Failed to save message:', error);
    } finally {
      setIsSaving(false);
    }
  }, [message.id, onUpdateMessage, handleExitEditMode]);

  const handleCancelEdit = useCallback(() => {
    handleExitEditMode();
  }, [handleExitEditMode]);

  return (
    <div
      className={`flex gap-3 items-start ${
        message.sender === 'user' ? 'justify-end' : ''
      }`}
    >
      {message.sender === 'ai' && (
        <div className="w-8 h-8 bg-ink-600 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
          <svg
            className="w-5 h-5 text-parchment-100"
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
            <span className="text-xs text-ink-400">•</span>
            <span className="text-xs text-ink-600">Just now</span>
            
            {/* Modified indicator */}
            {message.isModified && (
              <>
                <span className="text-xs text-ink-400">•</span>
                <span className="text-xs text-orange-600 font-medium">Modified</span>
              </>
            )}
          </div>
          
          {/* Edit Mode */}
          {message.sender === 'ai' && isEditMode && isEditableLesson ? (
            <div className="w-full">
              <LessonEditor
                content={message.text}
                onSave={handleSaveContent}
                onCancel={handleCancelEdit}
                autoSave={false} // Disable auto-save for inline editing
              />
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
              onMouseEnter={() => setIsHovered(true)}
              onMouseLeave={() => setIsHovered(false)}
            >
              {/* Edit button overlay */}
              {isEditableLesson && (
                <div
                  className={`absolute top-2 right-2 flex gap-1 transition-opacity duration-200 ${
                    isHovered ? 'opacity-100' : 'opacity-0'
                  }`}
                >
                  <button
                    onClick={handleEnterEditMode}
                    disabled={isSaving}
                    className="p-1.5 bg-ink-600 text-white rounded-md hover:bg-ink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
                    title="Edit lesson"
                  >
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                </div>
              )}

              {/* Message content */}
              {message.sender === 'ai' ? (
                <MarkdownRenderer content={message.text} className="text-sm leading-relaxed" />
              ) : (
                <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                  {message.text}
                </p>
              )}
            </div>
          )}

          {/* Citations section */}
          {hasCitations && (
            <div className="mt-3 pt-3 border-t border-ink-200">
              <div className="flex items-center justify-between mb-2">
                <button
                  onClick={() => setShowCitations(!showCitations)}
                  className="flex items-center gap-2 text-sm font-medium text-ink-700 hover:text-ink-900 transition-colors"
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${showCitations ? 'rotate-90' : ''}`}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
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
                  >
                    Download All
                  </button>
                )}
              </div>

              {showCitations && (
                <div className="space-y-2">
                  {citationsLoading ? (
                    <div className="flex items-center gap-2 text-sm text-ink-500 py-2">
                      <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor">
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
