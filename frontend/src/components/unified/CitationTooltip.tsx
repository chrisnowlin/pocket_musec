import { useRef, useState, useEffect } from 'react';
import type { EnhancedCitation } from '../../types/fileStorage';
import { getCitationIcon, getCitationTypeLabel, formatFileSize } from '../../types/fileStorage';

interface CitationTooltipProps {
  citation: EnhancedCitation;
  children: React.ReactNode;
  onDownload?: (fileId: string, filename: string) => void;
  isDownloading?: boolean;
}

export default function CitationTooltip({
  citation,
  children,
  onDownload,
  isDownloading = false
}: CitationTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLSpanElement>(null);

  const handleMouseEnter = () => {
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const viewportWidth = window.innerWidth;
      
      // Default position (below the trigger)
      let top = rect.bottom + 8;
      let left = rect.left;
      
      // Check if tooltip would go below viewport
      const tooltipHeight = 300; // Estimated max height
      if (top + tooltipHeight > viewportHeight) {
        // Position above the trigger instead
        top = rect.top - tooltipHeight - 8;
      }
      
      // Check if tooltip would go beyond right edge
      const tooltipWidth = 320; // Estimated max width
      if (left + tooltipWidth > viewportWidth) {
        // Align to right edge of trigger
        left = rect.right - tooltipWidth;
      }
      
      // Ensure tooltip doesn't go beyond left edge
      if (left < 0) {
        left = 8;
      }
      
      setPosition({ top, left });
    }
    setIsVisible(true);
  };

  const handleMouseLeave = () => {
    setIsVisible(false);
  };

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDownload && citation.fileMetadata && citation.canDownload) {
      onDownload(citation.fileMetadata.fileId, citation.fileMetadata.originalFilename);
    }
  };

  const icon = getCitationIcon(citation);
  const typeLabel = getCitationTypeLabel(citation);

  return (
    <>
      <span
        ref={triggerRef}
        className="inline-flex items-center gap-1 text-ink-600 hover:text-ink-800 cursor-help underline decoration-ink-400 decoration-dotted underline-offset-2"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {children}
      </span>

      {isVisible && (
        <div
          className="fixed z-50 w-80 max-h-80 overflow-hidden bg-white border border-ink-200 rounded-lg shadow-lg p-4"
          style={{
            top: `${position.top}px`,
            left: `${position.left}px`,
          }}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          {/* Tooltip header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-lg">{icon}</span>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-ink-800 text-sm">[{citation.citationNumber}]</span>
                  <span className="text-xs text-ink-600 bg-ink-100 px-1.5 py-0.5 rounded">
                    {typeLabel}
                  </span>
                </div>
                <h4 className="font-medium text-ink-900 text-sm mt-0.5 line-clamp-2">
                  {citation.sourceTitle}
                </h4>
              </div>
            </div>
          </div>

          {/* Citation text */}
          {citation.citationText && (
            <p className="text-xs text-ink-700 mb-3 italic line-clamp-3">
              {citation.citationText}
            </p>
          )}

          {/* File information */}
          {citation.fileMetadata && (
            <div className="space-y-2 mb-3 pb-3 border-b border-ink-200">
              <div className="text-xs">
                <div className="font-medium text-ink-800 mb-1">Source File:</div>
                <div className="grid grid-cols-1 gap-0.5 text-ink-600">
                  <div className="truncate" title={citation.fileMetadata.originalFilename}>
                    • {citation.fileMetadata.originalFilename}
                  </div>
                  <div>• Size: {formatFileSize(citation.fileMetadata.fileSize)}</div>
                  {citation.fileMetadata.documentType && (
                    <div>• Type: {citation.fileMetadata.documentType}</div>
                  )}
                </div>
              </div>

              {citation.pageNumber && (
                <div className="text-xs">
                  <span className="font-medium text-ink-800">Page:</span>
                  <span className="text-ink-600 ml-1">{citation.pageNumber}</span>
                </div>
              )}

              {/* Status */}
              <div className="flex items-center gap-1">
                {citation.isFileAvailable ? (
                  <span className="inline-flex items-center gap-1 text-xs text-green-700">
                    <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {citation.canDownload ? 'Available for download' : 'Processing'}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs text-orange-700">
                    <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    File unavailable
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Excerpt preview */}
          {citation.excerpt && (
            <div className="mb-3">
              <div className="font-medium text-ink-800 text-xs mb-1">Excerpt:</div>
              <div className="text-xs text-ink-600 bg-ink-50 p-2 rounded border-l-2 border-ink-300 line-clamp-3">
                {citation.excerpt}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between">
            {citation.fileMetadata && citation.canDownload && (
              <button
                onClick={handleDownload}
                disabled={isDownloading}
                className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-white bg-ink-600 hover:bg-ink-700 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isDownloading ? (
                  <>
                    <svg className="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Downloading...
                  </>
                ) : (
                  <>
                    <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Download
                  </>
                )}
              </button>
            )}
            
            {!citation.fileMetadata && (
              <span className="text-xs text-ink-500 italic">
                No file linked to this citation
              </span>
            )}
          </div>
        </div>
      )}
    </>
  );
}