import { useState } from 'react';
import { useFileStorage, useFileValidation } from '../../hooks/useFileStorage';
import FileStoragePanel from './FileStoragePanel';
import FileManager from './FileManager';
import DocumentIngestion from '../DocumentIngestion';
import { ingestionService, IngestionResponse } from '../../services/ingestionService';

/**
 * Example component demonstrating file storage integration
 * This shows how to use the new file storage features in a real application
 */
export default function FileStorageExample() {
  const [activeView, setActiveView] = useState<'ingestion' | 'manager' | 'panel'>('ingestion');
  
  // Use the file storage hook for managing files
  const {
    files,
    fileStats,
    loading,
    error,
    downloadFile,
    recentlyUploaded,
    hasFiles,
    refresh,
  } = useFileStorage({ pageSize: 5 });

  // Use the validation hook for file uploads
  const { validateFile, validateMultipleFiles } = useFileValidation();

  const handleIngestionComplete = (response: IngestionResponse) => {
    console.log('Ingestion completed:', response);
    
    if (response.duplicate) {
      alert(`Duplicate file detected: ${response.existing_file?.filename}`);
    } else if (response.file_metadata) {
      alert(`File successfully stored: ${response.file_metadata.original_filename}`);
      refresh(); // Refresh the file list
    }
  };

  const handleFileDownloaded = (fileId: string, filename: string) => {
    console.log(`File downloaded: ${filename}`);
    // You could show a success notification here
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = Array.from(event.target.files || []);
    
    if (uploadedFiles.length === 0) return;

    const { valid, invalid } = validateMultipleFiles(uploadedFiles);
    
    if (invalid.length > 0) {
      const errorMessages = invalid.map(({ file, error }) => `${file.name}: ${error}`).join('\n');
      alert(`Invalid files:\n${errorMessages}`);
    }

    if (valid.length > 0) {
      console.log('Valid files for upload:', valid);
      // Proceed with upload using the ingestion service
      valid.forEach(file => {
        ingestionService.uploadAndIngest(file)
          .then(handleIngestionComplete)
          .catch(error => {
            console.error('Upload failed:', error);
            alert(`Upload failed: ${error.message}`);
          });
      });
    }

    // Reset the file input
    event.target.value = '';
  };

  const renderStatusBar = () => (
    <div className="bg-parchment-100 border border-ink-200 rounded-lg p-4 mb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-sm text-ink-600">
            Total Files: <strong>{fileStats?.total_files || 0}</strong>
          </span>
          <span className="text-sm text-ink-600">
            Storage Used: <strong>{fileStats ? Math.round(fileStats.total_mb) : 0} MB</strong>
          </span>
          <span className="text-sm text-ink-600">
            Processing: <strong>{fileStats?.processing_files || 0}</strong>
          </span>
        </div>
        <button
          onClick={refresh}
          disabled={loading}
          className="px-3 py-1 text-sm border border-ink-300 rounded hover:bg-parchment-200 disabled:opacity-50"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
      {error && (
        <div className="mt-2 text-sm text-red-600">
          Error: {error}
        </div>
      )}
    </div>
  );

  const renderNavigation = () => (
    <div className="flex gap-2 mb-6">
      <button
        onClick={() => setActiveView('ingestion')}
        className={`px-4 py-2 rounded-md font-medium transition-colors ${
          activeView === 'ingestion'
            ? 'bg-ink-600 text-parchment-100'
            : 'bg-parchment-200 text-ink-700 hover:bg-parchment-300'
        }`}
      >
        Upload Document
      </button>
      <button
        onClick={() => setActiveView('manager')}
        className={`px-4 py-2 rounded-md font-medium transition-colors ${
          activeView === 'manager'
            ? 'bg-ink-600 text-parchment-100'
            : 'bg-parchment-200 text-ink-700 hover:bg-parchment-300'
        }`}
      >
        File Manager
      </button>
      <button
        onClick={() => setActiveView('panel')}
        className={`px-4 py-2 rounded-md font-medium transition-colors ${
          activeView === 'panel'
            ? 'bg-ink-600 text-parchment-100'
            : 'bg-parchment-200 text-ink-700 hover:bg-parchment-300'
        }`}
      >
        Panel View
      </button>
    </div>
  );

  const renderQuickUpload = () => (
    <div className="workspace-card rounded-lg p-4 mb-6">
      <h3 className="text-lg font-semibold text-ink-800 mb-4">Quick Upload</h3>
      <div className="border-2 border-dashed border-ink-300 rounded-lg p-6 text-center">
        <svg className="mx-auto h-12 w-12 text-ink-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p className="text-ink-700 mb-2">Drop files here or click to browse</p>
        <p className="text-sm text-ink-600 mb-4">PDF, TXT, DOC, DOCX (Max 10MB)</p>
        <input
          type="file"
          multiple
          accept=".pdf,.txt,.doc,.docx"
          onChange={handleFileUpload}
          className="hidden"
          id="quick-upload"
        />
        <label
          htmlFor="quick-upload"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-parchment-100 bg-ink-600 hover:bg-ink-700 cursor-pointer"
        >
          Select Files
        </label>
      </div>
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-ink-800 mb-2">File Storage Integration Demo</h1>
        <p className="text-ink-600">
          Demonstrating the new file storage system with permanent storage, duplicate detection, and metadata tracking
        </p>
      </div>

      {renderStatusBar()}
      {renderNavigation()}

      {/* Quick Upload - available in all views */}
      {renderQuickUpload()}

      {/* Main Content Area */}
      <div className="workspace-card rounded-lg p-6">
        {activeView === 'ingestion' && (
          <div>
            <h2 className="text-xl font-semibold text-ink-800 mb-4">Document Ingestion</h2>
            <DocumentIngestion onIngestionComplete={handleIngestionComplete} />
          </div>
        )}

        {activeView === 'manager' && (
          <div>
            <h2 className="text-xl font-semibold text-ink-800 mb-4">File Manager</h2>
            <FileManager
              onViewIngestion={() => setActiveView('ingestion')}
              onFileDownloaded={handleFileDownloaded}
            />
          </div>
        )}

        {activeView === 'panel' && (
          <div>
            <h2 className="text-xl font-semibold text-ink-800 mb-4">File Storage Panel</h2>
            <p className="text-ink-600 mb-4">
              Compact view suitable for sidebars or right panels
            </p>
            {hasFiles ? (
              <FileStoragePanel
                recentFiles={recentlyUploaded}
                fileStats={fileStats || undefined}
                onDownloadFile={downloadFile}
                onViewRecentFiles={() => setActiveView('manager')}
              />
            ) : (
              <div className="text-center py-8 text-ink-600">
                No files uploaded yet. Use the quick upload above or the document ingestion form.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Debug Information */}
      <div className="bg-parchment-100 border border-ink-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-ink-800 mb-2">Debug Information</h3>
        <div className="text-xs text-ink-600 space-y-1">
          <p>Files loaded: {files.length}</p>
          <p>Recently uploaded: {recentlyUploaded.length}</p>
          <p>Current view: {activeView}</p>
          <p>Loading: {loading.toString()}</p>
          <p>Error: {error || 'None'}</p>
          <p>File Stats: {fileStats ? JSON.stringify(fileStats, null, 2) : 'Not loaded'}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * Usage Examples:
 * 
 * 1. Basic File Storage Panel Integration:
 *    <FileStoragePanel
 *      recentFiles={recentlyUploaded}
 *      fileStats={fileStats}
 *      onDownloadFile={downloadFile}
 *      onViewRecentFiles={() => navigate('/files')}
 *    />
 * 
 * 2. Full File Manager:
 *    <FileManager
 *      onViewIngestion={() => navigate('/ingestion')}
 *      onFileDownloaded={(fileId, filename) => showSuccessNotification(`Downloaded ${filename}`)}
 *    />
 * 
 * 3. Enhanced Document Ingestion:
 *    <DocumentIngestion
 *      onIngestionComplete={(response) => {
 *        if (response.duplicate) {
 *          showWarningNotification('Duplicate file detected');
 *        } else {
 *          showSuccessNotification('File processed successfully');
 *        }
 *      }}
 *    />
 * 
 * 4. Custom File Validation:
 *    const { validateFile, validateMultipleFiles } = useFileValidation();
 *    
 *    const handleFileSelect = (file: File) => {
 *      const error = validateFile(file);
 *      if (error) {
 *        showErrorNotification(error);
 *        return;
 *      }
 *      // Proceed with upload
 *    };
 */