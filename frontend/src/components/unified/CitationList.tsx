import { useState } from 'react';
import type { EnhancedCitation } from '../../types/fileStorage';
import CitationCard from './CitationCard';

interface CitationListProps {
  citations: EnhancedCitation[];
  onDownload?: (fileId: string, filename: string) => void;
  downloadingFileIds?: string[];
  showFullDetails?: boolean;
  compact?: boolean;
  maxVisible?: number;
  title?: string;
  emptyMessage?: string;
}

export default function CitationList({
  citations,
  onDownload,
  downloadingFileIds = [],
  showFullDetails = false,
  compact = false,
  maxVisible,
  title = "Citations",
  emptyMessage = "No citations available"
}: CitationListProps) {
  const [showAll, setShowAll] = useState(false);
  
  if (citations.length === 0) {
    return (
      <div className="text-center py-4 text-ink-500">
        <svg className="w-8 h-8 mx-auto mb-2 opacity-50" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="text-sm">{emptyMessage}</p>
      </div>
    );
  }

  const visibleCitations = maxVisible && !showAll 
    ? citations.slice(0, maxVisible) 
    : citations;

  const hasMore = maxVisible && citations.length > maxVisible;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-ink-800 flex items-center gap-2">
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {title} 
          <span className="text-sm font-normal text-ink-600">({citations.length})</span>
        </h3>
        
        {/* File availability summary */}
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1 text-green-700">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>{citations.filter(c => c.isFileAvailable).length} available</span>
          </div>
          <div className="flex items-center gap-1 text-orange-700">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>{citations.filter(c => !c.isFileAvailable).length} unavailable</span>
          </div>
        </div>
      </div>

      {/* Citation cards */}
      <div className={compact ? "flex flex-wrap gap-2" : "space-y-3"}>
        {visibleCitations.map((citation) => (
          <CitationCard
            key={citation.id}
            citation={citation}
            onDownload={onDownload}
            isDownloading={downloadingFileIds.includes(citation.fileMetadata?.fileId || '')}
            showFullDetails={showFullDetails}
            compact={compact}
          />
        ))}
      </div>

      {/* Show more/less button */}
      {hasMore && (
        <div className="text-center pt-2">
          <button
            onClick={() => setShowAll(!showAll)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-ink-700 bg-ink-100 hover:bg-ink-200 rounded-md transition-colors"
          >
            {showAll ? (
              <>
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
                Show less
              </>
            ) : (
              <>
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
                Show {citations.length - maxVisible} more
              </>
            )}
          </button>
        </div>
      )}

      {/* Bulk download actions */}
      {onDownload && !compact && citations.some(c => c.isFileAvailable && c.canDownload) && (
        <div className="pt-2 border-t border-ink-200">
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                const availableCitations = citations.filter(c => c.isFileAvailable && c.canDownload && c.fileMetadata);
                availableCitations.forEach(citation => {
                  if (citation.fileMetadata) {
                    onDownload(citation.fileMetadata.fileId, citation.fileMetadata.originalFilename);
                  }
                });
              }}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-ink-700 bg-ink-100 hover:bg-ink-200 rounded-md transition-colors"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Download All Available
            </button>
            
            <span className="text-xs text-ink-500">
              {citations.filter(c => c.isFileAvailable && c.canDownload).length} files ready for download
            </span>
          </div>
        </div>
      )}
    </div>
  );
}