import FileOperationErrorBoundary from '../FileOperationErrorBoundary';
import { useFileStorage } from '../../hooks/useFileStorage';
import {
  formatFileSize,
  formatDate,
  getRelativeTime,
  DOCUMENT_TYPE_ICONS,
  DOCUMENT_TYPE_LABELS,
  FILE_STATUS_LABELS,
  FILE_STATUS_COLORS
} from '../../types/fileStorage';
import { formatDateTime } from '../../lib/dateUtils';
import { useFileStorageStore } from '../../stores/fileStorageStore';
import { ingestionService } from '../../services/ingestionService';

interface FileManagerProps {
  onViewIngestion?: () => void;
  onFileDownloaded?: (fileId: string, filename: string) => void;
}

const DEFAULT_PAGE_SIZE = 10;

export default function FileManager({ 
  onViewIngestion,
  onFileDownloaded 
}: FileManagerProps) {
  const {
    files,
    fileStats,
    loading,
    error,
    selectedStatus,
    currentPage,
    totalPages,
    setStatusFilter,
    setCurrentPage,
    downloadFile,
  } = useFileStorage({ autoLoad: true, pageSize: DEFAULT_PAGE_SIZE });
  const setFileError = useFileStorageStore((state) => state.setError);

  const handleDownloadFile = async (fileId: string, filename: string) => {
    try {
      await downloadFile(fileId, filename);
      onFileDownloaded?.(fileId, filename);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to download file';
      setFileError(message);
      console.error('Failed to download file:', err);
    }
  };

  const statusOptions = [
    { value: 'all', label: 'All Files', count: fileStats?.total_files || 0 },
    { value: 'completed', label: 'Completed', count: fileStats?.completed_files || 0 },
    { value: 'processing', label: 'Processing', count: fileStats?.processing_files || 0 },
    { value: 'uploaded', label: 'Uploaded', count: fileStats?.uploaded_files || 0 },
    { value: 'error', label: 'Errors', count: fileStats?.error_files || 0 },
  ];

  return (
    <FileOperationErrorBoundary
      onFileError={(error, operation) => {
        console.error(`FileManager file operation error in ${operation}:`, error);
        setFileError(`Failed to ${operation}: ${error.message}`);
      }}
    >
      <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
        <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-ink-800">File Manager</h2>
          <p className="text-ink-600 mt-1">
            Manage and download uploaded documents
          </p>
        </div>
        {onViewIngestion && (
          <button
            onClick={onViewIngestion}
            className="px-4 py-2 bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700"
          >
            Upload New Document
          </button>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-parchment-300 border border-ink-500 rounded-md p-4">
          <div className="flex">
            <svg className="h-5 w-5 text-ink-700 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-ink-800">{error}</p>
          </div>
        </div>
      )}

      {/* Statistics Overview */}
      {fileStats && (
        <div className="workspace-card rounded-lg p-6">
          <h3 className="text-lg font-semibold text-ink-800 mb-4">Storage Overview</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-ink-700">{fileStats.total_files}</div>
              <div className="text-sm text-ink-600">Total Files</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-ink-700">{formatFileSize(fileStats.total_bytes)}</div>
              <div className="text-sm text-ink-600">Storage Used</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-700">{fileStats.completed_files}</div>
              <div className="text-sm text-ink-600">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-700">{fileStats.processing_files}</div>
              <div className="text-sm text-ink-600">Processing</div>
            </div>
          </div>
          
          {/* File Types */}
          {Object.keys(fileStats.files_by_type).length > 0 && (
            <div className="mt-6 pt-6 border-t border-ink-200">
              <h4 className="text-sm font-semibold text-ink-800 mb-3">Files by Type</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                {Object.entries(fileStats.files_by_type).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-ink-600">{type}</span>
                    <span className="font-medium text-ink-800">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Status Filter */}
      <div className="workspace-card rounded-lg p-4">
        <div className="flex flex-wrap gap-2">
          {statusOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => {
                setStatusFilter(option.value);
                setCurrentPage(0);
              }}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                selectedStatus === option.value
                  ? 'bg-ink-600 text-parchment-100'
                  : 'bg-parchment-200 text-ink-700 hover:bg-parchment-300'
              }`}
            >
              {option.label} ({option.count})
            </button>
          ))}
        </div>
      </div>

      {/* Files List */}
      <div className="workspace-card rounded-lg p-6">
        <h3 className="text-lg font-semibold text-ink-800 mb-4">
          {selectedStatus === 'all' ? 'All Files' : FILE_STATUS_LABELS[selectedStatus as keyof typeof FILE_STATUS_LABELS]} Files
        </h3>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ink-600 mx-auto mb-4"></div>
            <p className="text-ink-600">Loading files...</p>
          </div>
        ) : files.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-ink-600">No files found</p>
          </div>
        ) : (
          <div className="space-y-4">
            {files.map((file) => (
              <div key={file.id} className="border border-ink-200 rounded-lg p-4 bg-parchment-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">
                        {file.document_type ? DOCUMENT_TYPE_ICONS[file.document_type as keyof typeof DOCUMENT_TYPE_ICONS] || '📄' : '📄'}
                      </span>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-ink-800 truncate">
                          {file.original_filename}
                        </h4>
                        <p className="text-xs text-ink-600">
                          {file.document_type ? DOCUMENT_TYPE_LABELS[file.document_type as keyof typeof DOCUMENT_TYPE_LABELS] || 'Unknown Document' : 'Unknown Document'}
                        </p>
                      </div>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full border ${FILE_STATUS_COLORS[file.ingestion_status]}`}>
                        {FILE_STATUS_LABELS[file.ingestion_status]}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-ink-600 mb-3">
                      <div>
                        <span className="block font-medium">Size</span>
                        {formatFileSize(file.file_size)}
                      </div>
                      <div>
                        <span className="block font-medium">Uploaded</span>
                        {formatDateTime(file.created_at)}
                      </div>
                      <div>
                        <span className="block font-medium">File ID</span>
                        <code className="text-xs">{file.file_id.substring(0, 8)}...</code>
                      </div>
                      <div>
                        <span className="block font-medium">Last Updated</span>
                        {getRelativeTime(file.updated_at)}
                      </div>
                    </div>
                    
                    {file.error_message && (
                      <div className="bg-red-50 border border-red-200 rounded-md p-2 mb-3">
                        <p className="text-xs text-red-800">{file.error_message}</p>
                      </div>
                    )}
                    
                    {file.metadata && Object.keys(file.metadata).length > 0 && (
                      <div className="text-xs text-ink-600">
                        <span className="font-medium">Metadata:</span>
                        <pre className="mt-1 p-2 bg-parchment-200 rounded text-xs overflow-x-auto">
                          {JSON.stringify(file.metadata, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex flex-col gap-2 ml-4">
                    {file.ingestion_status === 'completed' && (
                      <button
                        onClick={() => handleDownloadFile(file.file_id, file.original_filename)}
                        className="px-3 py-1 text-xs bg-ink-600 text-parchment-100 rounded hover:bg-ink-700"
                      >
                        Download
                      </button>
                    )}
                    <button
                      onClick={() => ingestionService.getFileMetadata(file.id)}
                      className="px-3 py-1 text-xs border border-ink-300 text-ink-700 rounded hover:bg-parchment-200"
                    >
                      Details
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {/* Pagination */}
        {!loading && files.length > 0 && (
          <div className="flex items-center justify-between mt-6 pt-6 border-t border-ink-200">
            <div className="text-sm text-ink-600">
              Showing {currentPage * DEFAULT_PAGE_SIZE + 1} to {Math.min((currentPage + 1) * DEFAULT_PAGE_SIZE, files.length)} of {files.length} files
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                disabled={currentPage === 0}
                className="px-3 py-1 text-xs border border-ink-300 rounded hover:bg-parchment-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={files.length < DEFAULT_PAGE_SIZE}
                className="px-3 py-1 text-xs border border-ink-300 rounded hover:bg-parchment-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
    </FileOperationErrorBoundary>
  );
}
