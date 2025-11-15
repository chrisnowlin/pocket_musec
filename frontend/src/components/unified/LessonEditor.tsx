import React, { useState, useEffect, useCallback, useRef, useMemo, useDeferredValue } from 'react';
import MarkdownRenderer from '../MarkdownRenderer';
import { lessonEditorStorage } from '../../utils/lessonEditorStorage';
import { useAutoSave } from '../../hooks/useAutoSave';
import type { LessonEditorProps, EditorMode, SaveStatus } from '../../types/unified';

const LessonEditor: React.FC<LessonEditorProps> = ({
  content,
  onSave,
  onCancel,
  autoSave = true,
}) => {
  // Generate unique storage key to prevent collisions across tabs
  const [storageKey] = useState(() => `lesson-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);
  const [editorContent, setEditorContent] = useState(content);
  const [mode, setMode] = useState<EditorMode>('edit');
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('saved');
  const [lastSaveTime, setLastSaveTime] = useState<Date | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const deferredPreviewContent = useDeferredValue(editorContent);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { wordCount, charCount } = useMemo(() => {
    const trimmed = editorContent.trim();
    return {
      wordCount: trimmed ? trimmed.split(/\s+/).length : 0,
      charCount: editorContent.length,
    };
  }, [editorContent]);


  // Auto-save functionality
  const { triggerSave, saveImmediately } = useAutoSave({
    onSave: async (content: string) => {
      await onSave(content);
      await lessonEditorStorage.saveContent(storageKey, content);
    },
    enabled: autoSave,
  });

  const performSave = useCallback(async () => {
    // Validate content before saving
    if (!editorContent.trim()) {
      setSaveStatus('error');
      console.warn('Cannot save empty content. Please add some content to your lesson.');
      return;
    }
    
    setSaveStatus('saving');
    
    try {
      await saveImmediately(editorContent);
      setSaveStatus('saved');
      setLastSaveTime(new Date());
    } catch (error) {
      setSaveStatus('error');
      console.error('Save failed:', error);
      // Show user-friendly error message
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      console.warn(`Failed to save lesson: ${errorMessage}. Please try again or check your connection.`);
    }
  }, [saveImmediately, editorContent]);

  // Handle content changes
  const handleContentChange = useCallback((newContent: string) => {
    setEditorContent(newContent);
    if (autoSave) {
      setSaveStatus('unsaved');
      triggerSave(newContent);
    }
  }, [autoSave, triggerSave]);

  // Keyboard shortcuts
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.ctrlKey || event.metaKey) {
      switch (event.key) {
        case 's':
          event.preventDefault();
          performSave();
          break;
      }
    } else if (event.key === 'Escape') {
      if (isFullscreen) {
        setIsFullscreen(false);
      } else {
        onCancel();
      }
    }
  }, [performSave, onCancel, isFullscreen]);

  // Load saved content on mount
  useEffect(() => {
    const loadSavedContent = async () => {
      try {
        const savedContent = await lessonEditorStorage.loadContent(storageKey);
        if (savedContent && savedContent !== content) {
          // Ask user if they want to recover saved content
          const shouldRecover = window.confirm(
            'Found unsaved changes from a previous session. Would you like to recover them?'
          );
          if (shouldRecover) {
            setEditorContent(savedContent);
            setSaveStatus('unsaved');
          }
        }
      } catch (error) {
        console.error('Failed to load saved content:', error);
        // Don't block the editor if recovery fails, just log it
        console.warn('Unable to recover unsaved content. Starting with fresh content.');
      }
    };

    loadSavedContent();
  }, [content, storageKey]);


  // Focus textarea on mount
  useEffect(() => {
    if (textareaRef.current && mode !== 'preview') {
      textareaRef.current.focus();
    }
  }, [mode]);

  const formatSaveStatus = (): string => {
    switch (saveStatus) {
      case 'saving':
        return 'Saving...';
      case 'saved':
        if (lastSaveTime) {
          const timeAgo = new Date().getTime() - lastSaveTime.getTime();
          if (timeAgo < 60000) {
            return 'Saved just now';
          } else {
            return `Saved ${lastSaveTime.toLocaleTimeString()}`;
          }
        }
        return 'Saved';
      case 'unsaved':
        return 'Unsaved changes';
      case 'error':
        return 'Save failed';
      default:
        return '';
    }
  };

  const getSaveStatusColor = (): string => {
    switch (saveStatus) {
      case 'saving':
        return 'text-blue-600';
      case 'saved':
        return 'text-green-600';
      case 'unsaved':
        return 'text-orange-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div 
      className={`flex flex-col h-full bg-parchment-50 ${isFullscreen ? 'fixed inset-0 z-50' : 'rounded-lg border border-ink-200'}`}
      role="dialog"
      aria-modal={isFullscreen}
      aria-label="Lesson Editor"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-ink-200 bg-white">
        <div className="flex items-center gap-3">
          <h3 className="font-semibold text-ink-800">Lesson Editor</h3>
          
          {/* Mode Toggle */}
          <div className="flex items-center gap-1 bg-ink-100 rounded-lg p-1" role="tablist" aria-label="View mode">
            <button
              onClick={() => setMode('edit')}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                mode === 'edit' 
                  ? 'bg-white text-ink-800 shadow-sm' 
                  : 'text-ink-600 hover:text-ink-800'
              }`}
              role="tab"
              aria-selected={mode === 'edit'}
              aria-controls="editor-panel"
              tabIndex={mode === 'edit' ? 0 : -1}
            >
              Edit
            </button>
            <button
              onClick={() => setMode('split')}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                mode === 'split' 
                  ? 'bg-white text-ink-800 shadow-sm' 
                  : 'text-ink-600 hover:text-ink-800'
              }`}
              role="tab"
              aria-selected={mode === 'split'}
              aria-controls="editor-panel preview-panel"
              tabIndex={mode === 'split' ? 0 : -1}
            >
              Split
            </button>
            <button
              onClick={() => setMode('preview')}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                mode === 'preview' 
                  ? 'bg-white text-ink-800 shadow-sm' 
                  : 'text-ink-600 hover:text-ink-800'
              }`}
              role="tab"
              aria-selected={mode === 'preview'}
              aria-controls="preview-panel"
              tabIndex={mode === 'preview' ? 0 : -1}
            >
              Preview
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Save Status */}
          <div className={`text-sm ${getSaveStatusColor()}`}>
            {formatSaveStatus()}
          </div>

          {/* Word/Char Count */}
          <div className="text-sm text-ink-600">
            {wordCount} words • {charCount} chars
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 text-ink-600 hover:text-ink-800 hover:bg-ink-100 rounded-md transition-colors"
              title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
            >
              {isFullscreen ? (
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
                </svg>
              ) : (
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0-4l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
              )}
            </button>
            <button
              onClick={() => performSave()}
              disabled={saveStatus === 'saving'}
              className="px-4 py-2 bg-ink-600 text-white rounded-md hover:bg-ink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {saveStatus === 'saving' ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-parchment-200 text-ink-700 rounded-md hover:bg-parchment-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>

      {/* Editor Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Editor Pane */}
        {(mode === 'edit' || mode === 'split') && (
          <div className={`${mode === 'split' ? 'w-1/2 border-r border-ink-200' : 'w-full'} flex flex-col`}>
            <textarea
              ref={textareaRef}
              value={editorContent}
              onChange={(e) => handleContentChange(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 p-4 bg-white border-0 resize-none focus:outline-none font-mono text-sm leading-relaxed"
              placeholder="Start typing your lesson content here..."
              style={{
                fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace',
              }}
            />
          </div>
        )}

        {/* Preview Pane */}
        {(mode === 'preview' || mode === 'split') && (
          <div className={`${mode === 'split' ? 'w-1/2' : 'w-full'} flex flex-col overflow-hidden`}>
            <div className="flex-1 p-4 bg-white overflow-y-auto">
              <MarkdownRenderer 
                content={deferredPreviewContent} 
                className="prose prose-sm max-w-none"
              />
            </div>
          </div>
        )}
      </div>

      {/* Footer with shortcuts */}
      <div className="px-4 py-2 border-t border-ink-200 bg-ink-50 text-xs text-ink-500">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span>Ctrl+S: Save</span>
            <span>Esc: {isFullscreen ? 'Exit fullscreen' : 'Cancel'}</span>
          </div>
          {autoSave && (
            <span>Auto-save enabled (2s after typing • every 30s)</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default LessonEditor;