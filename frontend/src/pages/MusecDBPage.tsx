import { useState, useEffect, useCallback, useMemo } from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import FileOperationErrorBoundary from '../components/FileOperationErrorBoundary';
import { useResizing } from '../hooks/useResizing';
import { useFileStorage, useFileValidation } from '../hooks/useFileStorage';
import Sidebar from '../components/unified/Sidebar';
import FileStoragePanel from '../components/unified/FileStoragePanel';
import FileManager from '../components/unified/FileManager';
import IngestionStatus from '../components/IngestionStatus';
import type { StandardRecord } from '../lib/types';
import api from '../lib/api';
import { ingestionService } from '../services/ingestionService';
import {
  formatFileSize,
  formatDate,
  DOCUMENT_TYPE_ICONS,
  DOCUMENT_TYPE_LABELS
} from '../types/fileStorage';
import { gradeOptions, strandOptions } from '../constants/unified';
import { frontendToBackendGrade, frontendToBackendStrand } from '../lib/gradeUtils';

type TabType = 'database' | 'files' | 'upload' | 'statistics';

interface EnhancedStandardRecord extends StandardRecord {
  source_file?: {
    id: string;
    file_id: string;
    original_filename: string;
    file_size: number;
    created_at: string;
    document_type?: string;
  };
}

export default function MusecDBPage() {
  const { sidebarWidth, resizingPanel, handleResizerMouseDown } = useResizing(280, 384);
  
  // Tab management
  const [activeTab, setActiveTab] = useState<TabType>('database');
  
  // Database state
  const [standards, setStandards] = useState<EnhancedStandardRecord[]>([]);
  const [selectedGrade, setSelectedGrade] = useState('All Grades');
  const [selectedStrand, setSelectedStrand] = useState('All Strands');
  const [selectedStandard, setSelectedStandard] = useState<EnhancedStandardRecord | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFileFilter, setSelectedFileFilter] = useState('all');
  const [loadingDatabase, setLoadingDatabase] = useState(false);
  const [databaseError, setDatabaseError] = useState('');
  
  // File storage state
  const {
    files,
    fileStats,
    loading: loadingFiles,
    error: fileError,
    recentlyUploaded,
    downloadFile,
    refresh: refreshFiles,
  } = useFileStorage({ autoLoad: true });
  
  const { validateMultipleFiles } = useFileValidation();
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');
  
  // File filter options
  const fileFilterOptions = useMemo(() => {
    const fileMap = new Map<string, { id: string; filename: string; type: string }>();
    files.forEach(file => {
      if (file.ingestion_status === 'completed') {
        fileMap.set(file.file_id, {
          id: file.file_id,
          filename: file.original_filename,
          type: file.document_type || 'unknown'
        });
      }
    });
    return Array.from(fileMap.values());
  }, [files]);

  // Load database content
  const loadDatabaseContent = useCallback(async () => {
    setLoadingDatabase(true);
    setDatabaseError('');
    try {
      const gradeParam = selectedGrade === 'All Grades' ? undefined : frontendToBackendGrade(selectedGrade);
      const strandParam = selectedStrand === 'All Strands' ? undefined : frontendToBackendStrand(selectedStrand);
      
      const response = await api.listStandards({
        grade_level: gradeParam,
        strand_code: strandParam
      });
      
      if (response.ok && response.data && Array.isArray(response.data)) {
        // Get unique file IDs from standards
        const fileIds = [...new Set(response.data.map((standard: StandardRecord) => standard.file_id).filter(Boolean))];
        
        // Fetch file metadata in bulk
        let fileMetadataMap: Record<string, any> = {};
        if (fileIds.length > 0) {
          try {
            const bulkFileResponse = await fetch(`/api/ingestion/files/bulk?file_ids=${fileIds.join(',')}`);
            if (bulkFileResponse.ok) {
              const bulkFileData = await bulkFileResponse.json();
              if (bulkFileData.success && bulkFileData.files) {
                fileMetadataMap = bulkFileData.files.reduce((acc: any, file: any) => {
                  acc[file.file_id] = file;
                  return acc;
                }, {});
              }
            }
          } catch (error) {
            console.warn('Failed to fetch bulk file metadata:', error);
          }
        }
        
        // Enhance standards with file information from bulk response
        const enhancedStandards = response.data.map((standard: StandardRecord) => {
          if (standard.file_id && fileMetadataMap[standard.file_id]) {
            return {
              ...standard,
              source_file: fileMetadataMap[standard.file_id]
            };
          }
          return standard;
        });
        
        setStandards(enhancedStandards as EnhancedStandardRecord[]);
      }
    } catch (error) {
      setDatabaseError(error instanceof Error ? error.message : 'Failed to load database content');
    } finally {
      setLoadingDatabase(false);
    }
  }, [selectedGrade, selectedStrand]);

  // Filter database content
  const filteredStandards = useMemo(() => {
    return standards.filter((standard) => {
      // Filter by search query
      const matchesSearch = searchQuery
        ? standard.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          standard.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
          standard.code.toLowerCase().includes(searchQuery.toLowerCase())
        : true;
      
      // Filter by source file
      const matchesFile = selectedFileFilter === 'all' || 
        (standard.source_file && standard.source_file.file_id === selectedFileFilter);
      
      return matchesSearch && matchesFile;
    });
  }, [standards, searchQuery, selectedFileFilter]);

  // Handle file upload
  const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = Array.from(event.target.files || []);
    if (uploadedFiles.length === 0) return;
    
    setUploading(true);
    setUploadError('');
    setUploadSuccess('');
    
    try {
      const validation = validateMultipleFiles(uploadedFiles);
      
      if (validation.invalid.length > 0) {
        setUploadError(`Invalid files: ${validation.invalid.map(v => v.file.name).join(', ')}`);
        return;
      }
      
      // Process first valid file (can be extended to handle multiple)
      const file = validation.valid[0];
      
      const result = await ingestionService.uploadAndIngest(file);
      
      if (result.success) {
        setUploadSuccess(`Successfully uploaded ${file.name}`);
        await refreshFiles();
      } else {
        setUploadError(result.error || 'Upload failed');
      }
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setUploading(false);
      // Reset file input
      event.target.value = '';
    }
  }, [validateMultipleFiles, refreshFiles]);

  // Load database content on mount and filter changes
  useEffect(() => {
    loadDatabaseContent();
  }, [loadDatabaseContent]);

  // Dummy handlers for sidebar
  const handleNewConversation = () => {
    // Placeholder
  };

  const handleSelectConversation = async (_sessionId: string) => {
    // Placeholder
  };

  const handleDeleteConversation = (_sessionId: string) => {
    // Placeholder
  };

  const handleOpenConversationEditor = (_sessionId: string) => {
    // Placeholder
  };

  const handleOpenDraftsModal = () => {
    // Placeholder
  };

  const fileInputId = 'musec-db-file-upload';

  return (
    <ErrorBoundary
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-ink-900">
          <div className="text-center text-parchment-300">
            <h2 className="text-2xl font-semibold mb-4">Database Interface Unavailable</h2>
            <p className="mb-6">The MusecDB component encountered an error and is temporarily unavailable.</p>
            <button
              onClick={() => window.location.href = '/'}
              className="px-6 py-3 bg-ink-600 rounded-lg hover:bg-ink-500 transition-colors"
            >
              Return to Home
            </button>
          </div>
        </div>
      }
      onError={(error, errorInfo) => {
        console.error('MusecDBPage error:', error, errorInfo);
        setDatabaseError(`Database error: ${error.message}`);
      }}
    >
      <FileOperationErrorBoundary
        onFileError={(error, operation) => {
          console.error(`MusecDBPage file operation error in ${operation}:`, error);
          setUploadError(`File operation failed during ${operation}: ${error.message}`);
        }}
      >
        <div className="flex h-screen">
        {/* Sidebar */}
        <Sidebar
          width={sidebarWidth}
          mode="chat"
          onModeChange={() => {}}
          onNewConversation={handleNewConversation}
          onUploadDocuments={() => {}}
          onUploadImages={() => {}}
          onOpenSettings={() => {}}
          conversationGroups={[]}
          onSelectConversation={handleSelectConversation}
          isLoadingSessions={false}
          onOpenDraftsModal={handleOpenDraftsModal}
          draftCount={0}
          onDeleteConversation={handleDeleteConversation}
          onOpenConversationEditor={handleOpenConversationEditor}
        />

        <div
          id="sidebarResizer"
          className={`resizer ${resizingPanel === 'sidebar' ? 'resizing' : ''}`}
          onMouseDown={(event) => handleResizerMouseDown('sidebar', event)}
        />

        {/* Main Content */}
        <section className="flex-1 flex flex-col panel workspace-panel-glass">
          <div className="flex-1 flex flex-col bg-ink-900">
            {/* Header */}
            <div className="bg-ink-800 border-b border-ink-700 px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-bold text-parchment-100">MusecDB</h1>
                  <p className="text-parchment-300 text-sm mt-1">
                    Comprehensive database and file management interface
                  </p>
                </div>
                
                {/* Quick Stats */}
                {fileStats && (
                  <div className="flex items-center gap-6 text-sm">
                    <div className="text-center">
                      <div className="text-lg font-bold text-parchment-100">{fileStats.total_files}</div>
                      <div className="text-parchment-400">Total Files</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-parchment-100">{formatFileSize(fileStats.total_bytes)}</div>
                      <div className="text-parchment-400">Storage Used</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-green-400">{fileStats.completed_files}</div>
                      <div className="text-parchment-400">Completed</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-parchment-100">{standards.length}</div>
                      <div className="text-parchment-400">Database Items</div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="bg-ink-700 border-b border-ink-600">
              <div className="flex space-x-1 px-6">
                <button
                  onClick={() => setActiveTab('database')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'database'
                      ? 'text-parchment-100 border-parchment-300'
                      : 'text-parchment-400 border-transparent hover:text-parchment-200'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    📋 Database Browser
                  </span>
                </button>
                <button
                  onClick={() => setActiveTab('files')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'files'
                      ? 'text-parchment-100 border-parchment-300'
                      : 'text-parchment-400 border-transparent hover:text-parchment-200'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    📁 File Manager
                  </span>
                </button>
                <button
                  onClick={() => setActiveTab('upload')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'upload'
                      ? 'text-parchment-100 border-parchment-300'
                      : 'text-parchment-400 border-transparent hover:text-parchment-200'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    ⬆️ Upload Documents
                  </span>
                </button>
                <button
                  onClick={() => setActiveTab('statistics')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'statistics'
                      ? 'text-parchment-100 border-parchment-300'
                      : 'text-parchment-400 border-transparent hover:text-parchment-200'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    📊 Statistics
                  </span>
                </button>
              </div>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-hidden">
              {/* Database Browser Tab */}
              {activeTab === 'database' && (
                <div className="h-full flex flex-col">
                  {/* Database Filters */}
                  <div className="bg-ink-800 px-6 py-3 border-b border-ink-700">
                    <div className="flex flex-wrap gap-3 items-center">
                      <div className="flex-1 min-w-[200px]">
                        <input
                          type="text"
                          placeholder="Search standards, objectives, or topics..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="w-full border border-ink-600 rounded-lg px-3 py-2 text-sm bg-ink-700 text-parchment-100 placeholder-ink-400 focus:outline-none focus:ring-2 focus:ring-ink-500"
                        />
                      </div>
                      
                      <select
                        value={selectedGrade}
                        onChange={(e) => setSelectedGrade(e.target.value)}
                        className="border border-ink-600 rounded-lg px-3 py-2 text-sm bg-ink-700 text-parchment-100 focus:outline-none focus:ring-2 focus:ring-ink-500"
                      >
                        <option value="All Grades">All Grades</option>
                        {gradeOptions.map((grade) => (
                          <option key={grade} value={grade}>{grade}</option>
                        ))}
                      </select>
                      
                      <select
                        value={selectedStrand}
                        onChange={(e) => setSelectedStrand(e.target.value)}
                        className="border border-ink-600 rounded-lg px-3 py-2 text-sm bg-ink-700 text-parchment-100 focus:outline-none focus:ring-2 focus:ring-ink-500"
                      >
                        <option value="All Strands">All Strands</option>
                        {strandOptions.map((strand) => (
                          <option key={strand} value={strand}>{strand}</option>
                        ))}
                      </select>
                      
                      <select
                        value={selectedFileFilter}
                        onChange={(e) => setSelectedFileFilter(e.target.value)}
                        className="border border-ink-600 rounded-lg px-3 py-2 text-sm bg-ink-700 text-parchment-100 focus:outline-none focus:ring-2 focus:ring-500"
                      >
                        <option value="all">All Source Files</option>
                        {fileFilterOptions.map((file) => (
                          <option key={file.id} value={file.id}>
                            {file.filename} ({file.type})
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Database Content */}
                  <div className="flex-1 overflow-y-auto px-6 py-4">
                    {databaseError && (
                      <div className="bg-red-900 border border-red-700 rounded-md p-4 mb-4">
                        <p className="text-red-200">{databaseError}</p>
                      </div>
                    )}
                    
                    {loadingDatabase ? (
                      <div className="flex items-center justify-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-parchment-300"></div>
                        <span className="ml-3 text-parchment-300">Loading database content...</span>
                      </div>
                    ) : filteredStandards.length === 0 ? (
                      <div className="text-center py-8">
                        <p className="text-parchment-400">No database content found matching your filters</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-lg font-semibold text-parchment-100">
                            Database Content
                          </h3>
                          <span className="text-parchment-400">
                            {filteredStandards.length} items found
                          </span>
                        </div>
                        
                        {filteredStandards.map((standard) => (
                          <div
                            key={standard.id}
                            className="bg-ink-800 border border-ink-700 rounded-lg p-4 hover:bg-ink-750 transition-colors"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                  <span className="text-xs font-mono font-semibold text-parchment-300 bg-ink-700 px-2 py-1 rounded">
                                    {standard.code}
                                  </span>
                                  <span className="text-xs text-parchment-400">{standard.strand_name} Strand</span>
                                  {standard.source_file && (
                                    <span className="text-xs text-parchment-400 flex items-center gap-1">
                                      📄 Source: {standard.source_file.original_filename}
                                    </span>
                                  )}
                                </div>
                                
                                <h4 className="font-medium text-parchment-100 mb-2">{standard.title}</h4>
                                <p className="text-sm text-parchment-300 mb-3">{standard.description}</p>
                                
                                <div className="flex items-center gap-4 text-sm text-parchment-400">
                                  <span className="flex items-center gap-1">
                                    🎯 {standard.objectives} objectives
                                  </span>
                                  <span className="flex items-center gap-1">
                                    📅 {standard.last_used ?? 'Recently used'}
                                  </span>
                                  {standard.source_file && (
                                    <>
                                      <span className="flex items-center gap-1">
                                        💾 {formatFileSize(standard.source_file.file_size)}
                                      </span>
                                      <span className="flex items-center gap-1">
                                        🕐 {formatDate(standard.source_file.created_at)}
                                      </span>
                                    </>
                                  )}
                                </div>
                              </div>
                              
                              <div className="flex flex-col gap-2 ml-4">
                                {standard.source_file && (
                                  <button
                                    onClick={() => downloadFile(standard.source_file!.file_id, standard.source_file!.original_filename)}
                                    className="px-3 py-1 text-xs bg-ink-600 text-parchment-100 rounded hover:bg-ink-500 transition-colors"
                                  >
                                    📥 Download Source
                                  </button>
                                )}
                                <button
                                  onClick={() => setSelectedStandard(standard)}
                                  className="px-3 py-1 text-xs border border-ink-600 text-parchment-200 rounded hover:bg-ink-700 transition-colors"
                                >
                                  View Details
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* File Manager Tab */}
              {activeTab === 'files' && (
                <div className="h-full overflow-y-auto">
                  {fileError && (
                    <div className="bg-red-900 border border-red-700 rounded-md p-4 m-4">
                      <p className="text-red-200">{fileError}</p>
                    </div>
                  )}
                  
                  {loadingFiles ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-parchment-300"></div>
                      <span className="ml-3 text-parchment-300">Loading files...</span>
                    </div>
                  ) : (
                    <div className="p-4">
                      <FileManager 
                        onFileDownloaded={(_fileId, filename) => {
                          console.log(`Downloaded file: ${filename}`);
                        }}
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Upload Tab */}
              {activeTab === 'upload' && (
                <div className="h-full flex flex-col items-center justify-center p-6">
                  <div className="max-w-2xl w-full">
                    <div className="bg-ink-800 border border-ink-700 rounded-lg p-8 text-center">
                      <div className="text-4xl mb-4">📤</div>
                      <h2 className="text-xl font-semibold text-parchment-100 mb-2">Upload Documents</h2>
                      <p className="text-parchment-300 mb-6">
                        Upload PDF, TXT, DOC, or DOCX files to add to your database
                      </p>
                      
                      {uploadError && (
                        <div className="bg-red-900 border border-red-700 rounded-md p-3 mb-4">
                          <p className="text-red-200 text-sm">{uploadError}</p>
                        </div>
                      )}
                      
                      {uploadSuccess && (
                        <div className="bg-green-900 border border-green-700 rounded-md p-3 mb-4">
                          <p className="text-green-200 text-sm">{uploadSuccess}</p>
                        </div>
                      )}
                      
                      <label
                        htmlFor={fileInputId}
                        className={`inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-ink-600 hover:bg-ink-500 cursor-pointer transition-colors ${
                          uploading ? 'opacity-50 cursor-not-allowed' : ''
                        }`}
                      >
                        {uploading ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Uploading...
                          </>
                        ) : (
                          <>
                            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                            Choose Files to Upload
                          </>
                        )}
                      </label>
                      
                      <input
                        id={fileInputId}
                        type="file"
                        multiple
                        accept=".pdf,.txt,.doc,.docx"
                        onChange={handleFileUpload}
                        className="hidden"
                        disabled={uploading}
                      />
                      
                      <div className="mt-6 text-sm text-parchment-400">
                        <p>Supported formats: PDF, TXT, DOC, DOCX</p>
                        <p>Maximum file size: 10MB</p>
                      </div>
                    </div>
                    
                    {/* Recent Files Panel */}
                    {recentlyUploaded.length > 0 && (
                      <div className="mt-6">
                        <FileStoragePanel
                          recentFiles={recentlyUploaded}
                          fileStats={fileStats || undefined}
                          onDownloadFile={downloadFile}
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Statistics Tab */}
              {activeTab === 'statistics' && (
                <div className="h-full overflow-y-auto p-6">
                  <IngestionStatus ref={undefined} />
                  
                  {fileStats && (
                    <div className="mt-6 workspace-card rounded-lg p-6">
                      <h3 className="text-lg font-semibold text-ink-800 mb-4">File Storage Statistics</h3>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-ink-700">{fileStats.total_files}</div>
                          <div className="text-sm text-ink-600">Total Files</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-ink-700">{formatFileSize(fileStats.total_bytes)}</div>
                          <div className="text-sm text-ink-600">Total Storage</div>
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
                      
                      {Object.keys(fileStats.files_by_type).length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold text-ink-800 mb-3">Files by Document Type</h4>
                          <div className="space-y-2">
                            {Object.entries(fileStats.files_by_type).map(([type, count]) => (
                              <div key={type} className="flex items-center justify-between p-2 bg-parchment-50 rounded">
                                <span className="flex items-center gap-2 text-ink-700">
                                  {DOCUMENT_TYPE_ICONS[type as keyof typeof DOCUMENT_TYPE_ICONS] || '📄'}
                                  {DOCUMENT_TYPE_LABELS[type as keyof typeof DOCUMENT_TYPE_LABELS] || type}
                                </span>
                                <span className="font-medium text-ink-800">{count}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
      </FileOperationErrorBoundary>
    </ErrorBoundary>
  );
}
