import { useState, useMemo } from 'react';
import MarkdownRenderer from '../MarkdownRenderer';
import BaseModal from './BaseModal';
import { formatDateTime } from '../../lib/dateUtils';
import type { DraftItem } from '../../types/unified';

interface VersionComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  draft: DraftItem | null;
  originalContent?: string;
}

export default function VersionComparisonModal({
  isOpen,
  onClose,
  draft,
  originalContent
}: VersionComparisonModalProps) {
  const [viewMode, setViewMode] = useState<'split' | 'original' | 'modified'>('split');

  if (!isOpen || !draft) return null;

  const hasChanges = useMemo(() => {
    return originalContent && originalContent !== draft.content;
  }, [originalContent, draft.content]);

  const getDiffStats = () => {
    if (!originalContent) return { added: 0, removed: 0 };
    
    const originalLines = originalContent.split('\n');
    const modifiedLines = draft.content.split('\n');
    
    // Simple line-based diff stats
    const added = Math.max(0, modifiedLines.length - originalLines.length);
    const removed = Math.max(0, originalLines.length - modifiedLines.length);
    
    return { added, removed };
  };

  const diffStats = getDiffStats();

  return (
    <BaseModal isOpen={isOpen} onClose={onClose} size="lg" zIndexClassName="z-[90]">
      {/* Header */}
      <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-ink-800">Version Comparison</h3>
            <p className="text-sm text-ink-600 mt-1">
              {draft.title || 'Untitled Draft'}
            </p>
          </div>
          <button 
            onClick={onClose} 
            className="text-ink-500 hover:text-ink-700 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Stats Bar */}
        {hasChanges && (
          <div className="bg-ink-50 rounded-lg p-3 flex items-center justify-between">
            <div className="flex items-center gap-4 text-sm">
              <span className="text-green-600 font-medium">
                +{diffStats.added} lines added
              </span>
              <span className="text-red-600 font-medium">
                -{diffStats.removed} lines removed
              </span>
            </div>
            <div className="text-sm text-ink-600">
              Last modified: {formatDateTime(draft.updatedAt)}
            </div>
          </div>
        )}

        {/* View Mode Toggle */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-ink-700">View:</label>
          <div className="flex items-center gap-1 bg-ink-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('split')}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                viewMode === 'split' 
                  ? 'bg-white text-ink-800 shadow-sm' 
                  : 'text-ink-600 hover:text-ink-800'
              }`}
            >
              Split View
            </button>
            <button
              onClick={() => setViewMode('original')}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                viewMode === 'original' 
                  ? 'bg-white text-ink-800 shadow-sm' 
                  : 'text-ink-600 hover:text-ink-800'
              }`}
            >
              Original
            </button>
            <button
              onClick={() => setViewMode('modified')}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                viewMode === 'modified' 
                  ? 'bg-white text-ink-800 shadow-sm' 
                  : 'text-ink-600 hover:text-ink-800'
              }`}
            >
              Modified
            </button>
          </div>
        </div>

        {/* Content Comparison */}
        <div className="flex-1 overflow-hidden">
          {!hasChanges ? (
            <div className="h-full flex items-center justify-center text-ink-500">
              <div className="text-center">
                <svg className="w-12 h-12 mx-auto mb-4 text-ink-400" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-lg font-medium">No changes detected</p>
                <p className="text-sm mt-2">The current version is identical to the original.</p>
              </div>
            </div>
          ) : (
            <div className="h-full flex gap-4">
              {/* Original Content */}
              {(viewMode === 'split' || viewMode === 'original') && (
                <div className={`${viewMode === 'split' ? 'w-1/2' : 'w-full'} flex flex-col`}>
                  <div className="bg-ink-100 rounded-t-lg px-4 py-2 border-b border-ink-200">
                    <h4 className="font-medium text-ink-800">Original Version</h4>
                    <p className="text-xs text-ink-600">Created: {formatDateTime(draft.createdAt)}</p>
                  </div>
                  <div className="flex-1 bg-white border border-ink-200 rounded-b-lg overflow-y-auto">
                    <div className="p-4">
                      <MarkdownRenderer 
                        content={originalContent || ''} 
                        className="prose prose-sm max-w-none"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Modified Content */}
              {(viewMode === 'split' || viewMode === 'modified') && (
                <div className={`${viewMode === 'split' ? 'w-1/2' : 'w-full'} flex flex-col`}>
                  <div className="bg-blue-50 rounded-t-lg px-4 py-2 border-b border-blue-200">
                    <h4 className="font-medium text-blue-800">Modified Version</h4>
                    <p className="text-xs text-blue-600">Updated: {formatDateTime(draft.updatedAt)}</p>
                  </div>
                  <div className="flex-1 bg-white border border-blue-200 rounded-b-lg overflow-y-auto">
                    <div className="p-4">
                      <MarkdownRenderer 
                        content={draft.content} 
                        className="prose prose-sm max-w-none"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-4 border-t border-ink-200">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-ink-600 text-white rounded-md hover:bg-ink-700 transition-colors"
          >
            Close
          </button>
        </div>
    </BaseModal>
  );
}