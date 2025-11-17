import { useState } from 'react';
import type { EnhancedCitation } from '../../types/fileStorage';
import { 
  getCitationIcon, 
  getCitationTypeLabel, 
  getCitationDisplayText, 
  formatFileSize,
  formatDate 
} from '../../types/fileStorage';

interface CitationCardProps {
  citation: EnhancedCitation;
  onDownload?: (fileId: string, filename: string) => void;
  isDownloading?: boolean;
  showFullDetails?: boolean;
  compact?: boolean;
}

export default function CitationCard({
  citation,
  onDownload,
  isDownloading = false,
  showFullDetails = false,
  compact = false
}: CitationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const handleDownload = () => {
    if (onDownload && citation.fileMetadata && citation.canDownload) {
      onDownload(citation.fileMetadata.fileId, citation.fileMetadata.originalFilename);
    }
  };

  const handleToggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const icon = getCitationIcon(citation);
  const typeLabel = getCitationTypeLabel(citation);
  const displayText = getCitationDisplayText(citation);

  if (compact) {
    return (
      <div className="inline-flex items-center gap-1 px-2 py-1 bg-ink-100 rounded-md text-xs">
        <span>{icon}</span>
        <span className="font-medium text-ink-700">[{citation.citationNumber}]</span>
        <span className="text-ink-600">{citation.sourceTitle}</span>
        {citation.fileMetadata && (
          <button
            onClick={handleDownload}
            disabled={!citation.canDownload || isDownloading}
            className="ml-1 text-ink-500 hover:text-ink-700 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Download source file"
          >
            <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="border border-ink-200 rounded-lg p-4 bg-parchment-50 hover:bg-parchment-100 transition-colors">
      {/* Citation header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-ink-800">[{citation.citationNumber}]</span>
              <span className="text-sm text-ink-600 bg-ink-100 px-2 py-0.5 rounded">
                {typeLabel}
              </span>
            </div>
            <h4 className="font-medium text-ink-900 mt-1">{citation.sourceTitle}</h4>
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex items-center gap-1">
          {citation.fileMetadata && citation.canDownload && (
            <button
              onClick={handleDownload}
              disabled={isDownloading}
              className="p-1.5 text-ink-600 hover:text-ink-800 hover:bg-ink-100 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Download source file"
            >
              {isDownloading ? (
                <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              ) : (
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              )}
            </button>
          )}
          
          {(citation.pageNumber || citation.excerpt || citation.fileMetadata) && (
            <button
              onClick={handleToggleExpand}
              className="p-1.5 text-ink-600 hover:text-ink-800 hover:bg-ink-100 rounded transition-colors"
              title={isExpanded ? "Show less" : "Show more"}
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Citation text */}
      {citation.citationText && (
        <p className="text-sm text-ink-700 mb-2 italic">{citation.citationText}</p>
      )}

      {/* Expanded details */}
      {isExpanded && (
        <div className="space-y-2 pt-2 border-t border-ink-200">
          {/* File information */}
          {citation.fileMetadata && (
            <div className="text-sm">
              <div className="font-medium text-ink-800 mb-1">Source File:</div>
              <div className="grid grid-cols-1 gap-1 text-ink-600">
                <div>• Filename: {citation.fileMetadata.originalFilename}</div>
                <div>• Size: {formatFileSize(citation.fileMetadata.fileSize)}</div>
                <div>• Type: {citation.fileMetadata.mimeType}</div>
                {citation.fileMetadata.documentType && (
                  <div>• Document Type: {citation.fileMetadata.documentType}</div>
                )}
                <div>• Uploaded: {formatDate(citation.fileMetadata.createdAt)}</div>
                {citation.relativeTime && (
                  <div>• {citation.relativeTime}</div>
                )}
                {!citation.isFileAvailable && (
                  <div className="text-orange-600">• File unavailable for download</div>
                )}
              </div>
            </div>
          )}

          {/* Page number */}
          {citation.pageNumber && (
            <div className="text-sm">
              <span className="font-medium text-ink-800">Page:</span>
              <span className="text-ink-600 ml-1">{citation.pageNumber}</span>
            </div>
          )}

          {/* Excerpt */}
          {citation.excerpt && (
            <div className="text-sm">
              <div className="font-medium text-ink-800 mb-1">Excerpt:</div>
              <div className="text-ink-600 bg-ink-50 p-2 rounded border-l-2 border-ink-300">
                {citation.excerpt}
              </div>
            </div>
          )}

          {/* Availability status */}
          {!citation.fileMetadata && (
            <div className="text-sm text-ink-500 italic">
              Source file information not available
            </div>
          )}
        </div>
      )}

      {/* Status indicators */}
      <div className="flex items-center gap-2 mt-2">
        {citation.fileMetadata ? (
          citation.isFileAvailable ? (
            <span className="inline-flex items-center gap-1 text-xs text-green-700">
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              File available
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-xs text-orange-700">
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              File unavailable
            </span>
          )
        ) : (
          <span className="inline-flex items-center gap-1 text-xs text-ink-500">
            <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            No file linked
          </span>
        )}
      </div>
    </div>
  );
}