import type { FileMetadata, FileStats } from '../../types/fileStorage';
import { formatFileSize, getRelativeTime, DOCUMENT_TYPE_ICONS, FILE_STATUS_LABELS, FILE_STATUS_COLORS } from '../../types/fileStorage';

interface FileStoragePanelProps {
  recentFiles?: FileMetadata[];
  fileStats?: FileStats;
  onViewRecentFiles?: () => void;
  onDownloadFile?: (fileId: string, filename: string) => void;
}

export default function FileStoragePanel({
  recentFiles = [],
  fileStats,
  onViewRecentFiles,
  onDownloadFile,
}: FileStoragePanelProps) {
  if (recentFiles.length === 0 && !fileStats) {
    return null;
  }

  return (
    <div className="workspace-card p-4 space-y-3">
      <div>
        <p className="text-xs uppercase tracking-wider text-ink-600 mb-2">File Storage</p>
        
        {/* File Statistics */}
        {fileStats && (
          <div className="mb-4">
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div className="text-center">
                <div className="text-lg font-bold text-ink-700">{fileStats.total_files}</div>
                <div className="text-xs text-ink-600">Total Files</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-ink-700">{formatFileSize(fileStats.total_bytes)}</div>
                <div className="text-xs text-ink-600">Storage Used</div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="text-center">
                <div className="text-sm font-semibold text-green-700">{fileStats.completed_files}</div>
                <div className="text-ink-600">Completed</div>
              </div>
              <div className="text-center">
                <div className="text-sm font-semibold text-blue-700">{fileStats.processing_files}</div>
                <div className="text-ink-600">Processing</div>
              </div>
            </div>
            {fileStats.error_files > 0 && (
              <div className="mt-2 text-center">
                <div className="text-sm font-semibold text-red-700">{fileStats.error_files}</div>
                <div className="text-ink-600">Errors</div>
              </div>
            )}
          </div>
        )}

        {/* Recent Files */}
        {recentFiles.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-ink-800 text-xs">Recent Files</h3>
              {onViewRecentFiles && (
                <button
                  onClick={onViewRecentFiles}
                  className="text-xs text-ink-600 hover:text-ink-800"
                >
                  View All
                </button>
              )}
            </div>
            <div className="space-y-2">
              {recentFiles.slice(0, 3).map((file) => (
                <div key={file.id} className="bg-parchment-100 rounded-lg p-2 border border-ink-200">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-1 flex-1 min-w-0">
                      <span className="text-sm">
                        {file.document_type ? DOCUMENT_TYPE_ICONS[file.document_type as keyof typeof DOCUMENT_TYPE_ICONS] || '📄' : '📄'}
                      </span>
                      <span className="text-xs font-medium text-ink-800 truncate">
                        {file.original_filename}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <span className={`text-xs px-1.5 py-0.5 rounded-full border ${FILE_STATUS_COLORS[file.ingestion_status]}`}>
                        {FILE_STATUS_LABELS[file.ingestion_status]}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs text-ink-600">
                    <span className="truncate">{formatFileSize(file.file_size)}</span>
                    <span className="flex-shrink-0">{getRelativeTime(file.created_at)}</span>
                  </div>
                  {onDownloadFile && file.ingestion_status === 'completed' && (
                    <button
                      onClick={() => onDownloadFile(file.file_id, file.original_filename)}
                      className="mt-1 text-xs text-ink-600 hover:text-ink-800 flex items-center gap-1"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Download
                    </button>
                  )}
                  {file.error_message && (
                    <div className="mt-1 text-xs text-red-600 truncate" title={file.error_message}>
                      ⚠️ {file.error_message}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}