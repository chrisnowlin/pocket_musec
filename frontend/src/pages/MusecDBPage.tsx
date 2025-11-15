import { useState, useEffect, useCallback, useMemo } from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import FileOperationErrorBoundary from '../components/FileOperationErrorBoundary';
import { useResizing } from '../hooks/useResizing';
import { useFileStorage, useFileValidation } from '../hooks/useFileStorage';
import { useDrafts } from '../hooks/useDrafts';
import { useLessons } from '../hooks/useLessons';
import Sidebar from '../components/unified/Sidebar';
import FileStoragePanel from '../components/unified/FileStoragePanel';
import FileManager from '../components/unified/FileManager';
import IngestionStatus from '../components/IngestionStatus';
import LessonEditor from '../components/unified/LessonEditor';
import DraftPreview from '../components/unified/DraftPreview';
import ExportModal from '../components/unified/ExportModal';
import VersionComparisonModal from '../components/unified/VersionComparisonModal';
import type { StandardRecord } from '../lib/types';
import api from '../lib/api';
import { ingestionService } from '../services/ingestionService';
import {
  formatFileSize,
  formatDate,
  DOCUMENT_TYPE_ICONS,
  DOCUMENT_TYPE_LABELS
} from '../types/fileStorage';
import { formatDateTime } from '../lib/dateUtils';
import { gradeOptions, strandOptions } from '../constants/unified';
import { frontendToBackendGrade, frontendToBackendStrand } from '../lib/gradeUtils';

type TabType = 'drafts' | 'lessons' | 'database' | 'files' | 'upload' | 'statistics';

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
  const [activeTab, setActiveTab] = useState<TabType>('drafts');

  // Preview panel resize state
  const [previewWidth, setPreviewWidth] = useState(384); // 96 * 4 = 384px (w-96)
  const [isResizingPreview, setIsResizingPreview] = useState(false);
  
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
  
  // Drafts state
  const [searchQueryDrafts, setSearchQueryDrafts] = useState('');
  const [selectedGradeDrafts, setSelectedGradeDrafts] = useState('');
  const [selectedStrandDrafts, setSelectedStrandDrafts] = useState('');
  const [selectedDraft, setSelectedDraft] = useState<any>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editingDraft, setEditingDraft] = useState<any>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [exportingDraft, setExportingDraft] = useState<any>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [isVersionModalOpen, setIsVersionModalOpen] = useState(false);
  const [comparingDraft, setComparingDraft] = useState<any>(null);
  
  // Draft management
  const {
    drafts,
    isLoading: isLoadingDrafts,
    draftCount,
    getDraft,
    deleteDraft,
    updateDraft,
  } = useDrafts();

  // Lessons management
  const {
    lessons,
    isLoading: isLoadingLessons,
    lessonCount,
    deleteLesson,
    promoteFromDraft,
    demoteToLesson,
  } = useLessons();
  
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
        strand_code: strandParam,
        limit: 200 // Request all standards (default is 50, but we have 112+ standards)
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
  const handleBrowseStandards = () => {
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

  const handleOpenDraft = async (draftId: string) => {
    const draft = await getDraft(draftId);
    if (draft) {
      // Navigate to the unified page to continue working on the draft
      window.location.href = '/unified';
    }
  };

  const handleDeleteDraft = async (draftId: string) => {
    const success = await deleteDraft(draftId);
    if (success) {
      // Draft is automatically removed from the list by the hook
      if (selectedDraft?.id === draftId) {
        setSelectedDraft(null);
      }
    }
  };

  const handleEditDraft = (draft: any) => {
    setEditingDraft(draft);
    setIsEditing(true);
  };

  const handleSaveEditedDraft = async (content: string) => {
    if (!editingDraft) return;

    setIsSaving(true);
    try {
      const updatedDraft = await updateDraft(editingDraft.id, {
        content,
        title: editingDraft.title,
      });

      if (updatedDraft) {
        setIsEditing(false);
        setEditingDraft(null);
        if (selectedDraft?.id === editingDraft.id) {
          setSelectedDraft(updatedDraft);
        }
      }
    } catch (error) {
      console.error('Failed to save draft:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      alert(`Failed to save draft: ${errorMessage}. Please try again.`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditingDraft(null);
  };

  const handleExportDraft = async (format: 'markdown' | 'pdf' | 'docx') => {
    if (!exportingDraft) return;

    setIsExporting(true);
    try {
      const metadata = {
        title: exportingDraft.title || 'Untitled Draft',
        grade: exportingDraft.grade,
        strand: exportingDraft.strand,
        createdAt: formatDateTime(exportingDraft.createdAt),
        updatedAt: formatDateTime(exportingDraft.updatedAt),
      };

      switch (format) {
        case 'markdown':
          const markdownContent = `# ${metadata.title}

${metadata.grade ? `**Grade:** ${metadata.grade}` : ''}
${metadata.strand ? `**Strand:** ${metadata.strand}` : ''}
**Created:** ${metadata.createdAt}
**Last Updated:** ${metadata.updatedAt}

---

${exportingDraft.content}`;

          const blob = new Blob([markdownContent], { type: 'text/markdown' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${metadata.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.md`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          break;

        case 'pdf':
          const printWindow = window.open('', '_blank');
          if (printWindow) {
            printWindow.document.write(`
              <html>
                <head>
                  <title>${metadata.title}</title>
                  <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }
                    h1 { color: #333; }
                    .metadata { color: #666; margin-bottom: 20px; }
                    .metadata span { margin-right: 20px; }
                  </style>
                </head>
                <body>
                  <h1>${metadata.title}</h1>
                  <div class="metadata">
                    ${metadata.grade ? `<span><strong>Grade:</strong> ${metadata.grade}</span>` : ''}
                    ${metadata.strand ? `<span><strong>Strand:</strong> ${metadata.strand}</span>` : ''}
                    <span><strong>Created:</strong> ${metadata.createdAt}</span>
                    <span><strong>Last Updated:</strong> ${metadata.updatedAt}</span>
                  </div>
                  <hr>
                  <div>${exportingDraft.content.replace(/\n/g, '<br>')}</div>
                </body>
              </html>
            `);
            printWindow.document.close();
            printWindow.print();
          }
          break;

        case 'docx':
          const plainTextContent = `${metadata.title}

Grade: ${metadata.grade || 'N/A'}
Strand: ${metadata.strand || 'N/A'}
Created: ${metadata.createdAt}
Last Updated: ${metadata.updatedAt}

${exportingDraft.content}`;

          const plainTextBlob = new Blob([plainTextContent], { type: 'text/plain' });
          const plainTextUrl = URL.createObjectURL(plainTextBlob);
          const plainTextA = document.createElement('a');
          plainTextA.href = plainTextUrl;
          plainTextA.download = `${metadata.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.txt`;
          document.body.appendChild(plainTextA);
          plainTextA.click();
          document.body.removeChild(plainTextA);
          URL.revokeObjectURL(plainTextUrl);
          break;
      }

      setIsExportModalOpen(false);
      setExportingDraft(null);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const handleViewVersionComparison = (draft: any) => {
    setComparingDraft(draft);
    setIsVersionModalOpen(true);
  };

  const truncateContent = (content: string, maxLength: number = 100) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength).trim() + '...';
  };

  const { uniqueGrades, uniqueStrands } = useMemo(() => {
    const grades = new Set<string>();
    const strands = new Set<string>();

    drafts.forEach(draft => {
      if (draft.grade) grades.add(draft.grade);
      if (draft.strand) strands.add(draft.strand);
    });

    return {
      uniqueGrades: Array.from(grades).sort(),
      uniqueStrands: Array.from(strands).sort(),
    };
  }, [drafts]);

  const filteredDrafts = useMemo(() => {
    return drafts.filter(draft => {
      const matchesSearch = searchQueryDrafts === '' ||
        draft.title.toLowerCase().includes(searchQueryDrafts.toLowerCase()) ||
        draft.content.toLowerCase().includes(searchQueryDrafts.toLowerCase());

      const matchesGrade = selectedGradeDrafts === '' || draft.grade === selectedGradeDrafts;
      const matchesStrand = selectedStrandDrafts === '' || draft.strand === selectedStrandDrafts;

      return matchesSearch && matchesGrade && matchesStrand;
    });
  }, [drafts, searchQueryDrafts, selectedGradeDrafts, selectedStrandDrafts]);

  const clearDraftFilters = () => {
    setSearchQueryDrafts('');
    setSelectedGradeDrafts('');
    setSelectedStrandDrafts('');
  };

  // Lessons-specific state
  const [searchQueryLessons, setSearchQueryLessons] = useState('');
  const [selectedGradeLessons, setSelectedGradeLessons] = useState('');
  const [selectedStrandLessons, setSelectedStrandLessons] = useState('');
  const [selectedLesson, setSelectedLesson] = useState<any>(null);
  const [lessonPreviewWidth, setLessonPreviewWidth] = useState(384);
  const [isResizingLessonPreview, setIsResizingLessonPreview] = useState(false);

  const { uniqueGradesLessons, uniqueStrandsLessons } = useMemo(() => {
    const grades = new Set<string>();
    const strands = new Set<string>();

    lessons.forEach(lesson => {
      if (lesson.grade) grades.add(lesson.grade);
      if (lesson.strand) strands.add(lesson.strand);
    });

    return {
      uniqueGradesLessons: Array.from(grades).sort(),
      uniqueStrandsLessons: Array.from(strands).sort(),
    };
  }, [lessons]);

  const filteredLessons = useMemo(() => {
    return lessons.filter(lesson => {
      const matchesSearch = searchQueryLessons === '' ||
        lesson.title.toLowerCase().includes(searchQueryLessons.toLowerCase()) ||
        lesson.content.toLowerCase().includes(searchQueryLessons.toLowerCase());

      const matchesGrade = selectedGradeLessons === '' || lesson.grade === selectedGradeLessons;
      const matchesStrand = selectedStrandLessons === '' || lesson.strand === selectedStrandLessons;

      return matchesSearch && matchesGrade && matchesStrand;
    });
  }, [lessons, searchQueryLessons, selectedGradeLessons, selectedStrandLessons]);

  const clearLessonFilters = () => {
    setSearchQueryLessons('');
    setSelectedGradeLessons('');
    setSelectedStrandLessons('');
  };

  const handlePromoteDraft = async (draftId: string) => {
    const result = await promoteFromDraft(draftId);
    if (result) {
      // Remove from drafts list
      if (drafts.length > 0) {
        // Trigger reload of drafts
        const updatedDrafts = drafts.filter(d => d.id !== draftId);
        console.log('Draft promoted successfully');
      }
    }
  };

  const handleDemoteLesson = async (lessonId: string) => {
    const result = await demoteToLesson(lessonId);
    if (result) {
      setSelectedLesson(null);
      console.log('Lesson demoted successfully');
    }
  };

  const handleDeleteLesson = async (lessonId: string) => {
    const success = await deleteLesson(lessonId);
    if (success) {
      if (selectedLesson?.id === lessonId) {
        setSelectedLesson(null);
      }
    }
  };

  // Preview panel resize handlers for lessons
  const handleLessonPreviewResizerMouseDown = (event: React.MouseEvent) => {
    event.preventDefault();
    setIsResizingLessonPreview(true);

    const startX = event.clientX;
    const startWidth = lessonPreviewWidth;

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = startX - e.clientX;
      const newWidth = Math.max(280, Math.min(800, startWidth + deltaX));
      setLessonPreviewWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizingLessonPreview(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  // Preview panel resize handlers
  const handlePreviewResizerMouseDown = (event: React.MouseEvent) => {
    event.preventDefault();
    setIsResizingPreview(true);

    const startX = event.clientX;
    const startWidth = previewWidth;

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = startX - e.clientX; // Reversed because panel is on the right
      const newWidth = Math.max(280, Math.min(800, startWidth + deltaX));
      setPreviewWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizingPreview(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
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
          onBrowseStandards={handleBrowseStandards}
          onUploadDocuments={() => {}}
          onUploadImages={() => {}}
          onOpenSettings={() => {}}
          conversationGroups={[]}
          onSelectConversation={handleSelectConversation}
          isLoadingSessions={false}
          onOpenDraftsModal={() => setActiveTab('drafts')}
          draftCount={draftCount}
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
                  onClick={() => setActiveTab('drafts')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'drafts'
                      ? 'text-parchment-100 border-parchment-300'
                      : 'text-parchment-400 border-transparent hover:text-parchment-200'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    💾 Saved Drafts
                    {draftCount > 0 && (
                      <span className="ml-1 px-2 py-0.5 text-xs bg-ink-600 text-parchment-100 rounded-full">
                        {draftCount}
                      </span>
                    )}
                  </span>
                </button>
                <button
                  onClick={() => setActiveTab('lessons')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'lessons'
                      ? 'text-parchment-100 border-parchment-300'
                      : 'text-parchment-400 border-transparent hover:text-parchment-200'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    📚 My Lessons
                    {lessonCount > 0 && (
                      <span className="ml-1 px-2 py-0.5 text-xs bg-ink-600 text-parchment-100 rounded-full">
                        {lessonCount}
                      </span>
                    )}
                  </span>
                </button>
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
              {/* Saved Drafts Tab */}
              {activeTab === 'drafts' && (
                <div className="h-full flex flex-col">
                  {/* If editing, show the lesson editor */}
                  {isEditing && editingDraft ? (
                    <div className="flex-1 flex flex-col">
                      {isSaving && (
                        <div className="bg-blue-900 border border-blue-700 rounded-md p-3 mx-6 mt-4">
                          <div className="flex items-center gap-2 text-blue-200">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
                            Saving draft...
                          </div>
                        </div>
                      )}
                      <div className="flex-1 overflow-hidden">
                        <ErrorBoundary>
                          <LessonEditor
                            content={editingDraft.content}
                            onSave={handleSaveEditedDraft}
                            onCancel={handleCancelEdit}
                            autoSave={false}
                          />
                        </ErrorBoundary>
                      </div>
                    </div>
                  ) : (
                    <>
                      {/* Search and Filters */}
                      <div className="bg-ink-800 px-6 py-3 border-b border-ink-700">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="flex-1 relative">
                            <input
                              type="text"
                              placeholder="Search drafts by title or content..."
                              value={searchQueryDrafts}
                              onChange={(e) => setSearchQueryDrafts(e.target.value)}
                              className="w-full pl-10 pr-4 py-2 border border-ink-600 rounded-lg bg-ink-700 text-parchment-100 placeholder-ink-400 focus:outline-none focus:ring-2 focus:ring-ink-500"
                            />
                            <svg
                              className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-ink-400"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                              />
                            </svg>
                          </div>
                          <button
                            onClick={clearDraftFilters}
                            className="px-4 py-2 bg-ink-600 text-parchment-100 rounded-lg hover:bg-ink-500 transition-colors text-sm"
                          >
                            Clear Filters
                          </button>
                        </div>

                        <div className="flex items-center gap-3">
                          <select
                            value={selectedGradeDrafts}
                            onChange={(e) => setSelectedGradeDrafts(e.target.value)}
                            className="px-3 py-2 border border-ink-600 rounded-lg bg-ink-700 text-parchment-100 focus:outline-none focus:ring-2 focus:ring-ink-500"
                          >
                            <option value="">All Grades</option>
                            {uniqueGrades.map(grade => (
                              <option key={grade} value={grade}>{grade}</option>
                            ))}
                          </select>

                          <select
                            value={selectedStrandDrafts}
                            onChange={(e) => setSelectedStrandDrafts(e.target.value)}
                            className="px-3 py-2 border border-ink-600 rounded-lg bg-ink-700 text-parchment-100 focus:outline-none focus:ring-2 focus:ring-ink-500"
                          >
                            <option value="">All Strands</option>
                            {uniqueStrands.map(strand => (
                              <option key={strand} value={strand}>{strand}</option>
                            ))}
                          </select>

                          <div className="flex-1 text-right">
                            <span className="text-sm text-parchment-400">
                              {filteredDrafts.length} of {drafts.length} drafts
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Main Content - Draft List and Preview */}
                      <div className="flex-1 flex gap-4 overflow-hidden p-4">
                        {/* Draft List */}
                        <div className="flex-1 overflow-y-auto min-w-0">
                          {isLoadingDrafts ? (
                            <div className="flex items-center justify-center py-12">
                              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-parchment-300"></div>
                              <span className="ml-3 text-parchment-300">Loading drafts...</span>
                            </div>
                          ) : filteredDrafts.length === 0 ? (
                            <div className="text-center py-12">
                              <svg
                                className="mx-auto h-12 w-12 text-parchment-400"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                />
                              </svg>
                              <p className="mt-4 text-lg text-parchment-300">
                                {drafts.length === 0 ? 'No saved drafts' : 'No drafts match your filters'}
                              </p>
                              <p className="mt-2 text-sm text-parchment-400">
                                {drafts.length === 0
                                  ? 'Start creating a lesson and save it as a draft to see it here.'
                                  : 'Try adjusting your search or filters to find what you\'re looking for.'}
                              </p>
                            </div>
                          ) : (
                            <div className="space-y-3">
                              {filteredDrafts.map((draft) => (
                                <div
                                  key={draft.id}
                                  className={`border rounded-lg p-4 transition-colors cursor-pointer ${
                                    selectedDraft?.id === draft.id
                                      ? 'border-parchment-300 bg-ink-700'
                                      : 'border-ink-700 hover:bg-ink-750'
                                  }`}
                                  onClick={() => setSelectedDraft(draft)}
                                >
                                  <div className="flex items-start justify-between">
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center gap-2 mb-2">
                                        <h4 className="font-medium text-parchment-100 truncate">
                                          {draft.title || 'Untitled Draft'}
                                        </h4>
                                        {(draft.grade || draft.strand) && (
                                          <div className="flex items-center gap-1 text-xs text-parchment-400">
                                            {draft.grade && <span>{draft.grade}</span>}
                                            {draft.grade && draft.strand && <span>•</span>}
                                            {draft.strand && <span>{draft.strand}</span>}
                                          </div>
                                        )}
                                      </div>
                                      <p className="text-sm text-parchment-300 mb-2">
                                        {truncateContent(draft.content)}
                                      </p>
                                      <p className="text-xs text-parchment-400">
                                        Last updated {formatDateTime(draft.updatedAt)}
                                      </p>
                                    </div>
                                    <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                                      {draft.originalContent && draft.originalContent !== draft.content && (
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleViewVersionComparison(draft);
                                          }}
                                          className="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
                                          title="View changes made to this draft"
                                        >
                                          Changes
                                        </button>
                                      )}
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handlePromoteDraft(draft.id);
                                        }}
                                        className="px-3 py-1.5 text-sm bg-amber-600 text-white rounded-md hover:bg-amber-700 transition-colors"
                                        title="Promote this draft to a permanent lesson"
                                      >
                                        Promote
                                      </button>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleEditDraft(draft);
                                        }}
                                        className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                                        title="Edit this draft"
                                      >
                                        Edit
                                      </button>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          setExportingDraft(draft);
                                          setIsExportModalOpen(true);
                                        }}
                                        className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                                        title="Export this draft"
                                      >
                                        Export
                                      </button>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleOpenDraft(draft.id);
                                        }}
                                        className="px-3 py-1.5 text-sm bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-500 transition-colors"
                                        title="Continue editing this draft"
                                      >
                                        Open
                                      </button>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleDeleteDraft(draft.id);
                                        }}
                                        className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                                        title="Delete this draft"
                                      >
                                        Delete
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Preview Panel Resizer */}
                        <div
                          className={`resizer ${isResizingPreview ? 'resizing' : ''}`}
                          onMouseDown={handlePreviewResizerMouseDown}
                          style={{ cursor: 'col-resize' }}
                        />

                        {/* Preview Pane */}
                        <div
                          className="flex-shrink-0"
                          style={{ width: `${previewWidth}px` }}
                        >
                          <DraftPreview draft={selectedDraft} />
                        </div>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* My Lessons Tab */}
              {activeTab === 'lessons' && (
                <div className="h-full flex flex-col">
                  {/* Search and Filters */}
                  <div className="bg-ink-800 px-6 py-3 border-b border-ink-700">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="flex-1 relative">
                        <input
                          type="text"
                          placeholder="Search lessons by title or content..."
                          value={searchQueryLessons}
                          onChange={(e) => setSearchQueryLessons(e.target.value)}
                          className="w-full pl-10 pr-4 py-2 border border-ink-600 rounded-lg bg-ink-700 text-parchment-100 placeholder-ink-400 focus:outline-none focus:ring-2 focus:ring-ink-500"
                        />
                        <svg
                          className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-ink-400"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                          />
                        </svg>
                      </div>
                      <button
                        onClick={clearLessonFilters}
                        className="px-4 py-2 bg-ink-600 text-parchment-100 rounded-lg hover:bg-ink-500 transition-colors text-sm"
                      >
                        Clear Filters
                      </button>
                    </div>

                    <div className="flex items-center gap-3">
                      <select
                        value={selectedGradeLessons}
                        onChange={(e) => setSelectedGradeLessons(e.target.value)}
                        className="px-3 py-2 border border-ink-600 rounded-lg bg-ink-700 text-parchment-100 focus:outline-none focus:ring-2 focus:ring-ink-500"
                      >
                        <option value="">All Grades</option>
                        {uniqueGradesLessons.map(grade => (
                          <option key={grade} value={grade}>{grade}</option>
                        ))}
                      </select>

                      <select
                        value={selectedStrandLessons}
                        onChange={(e) => setSelectedStrandLessons(e.target.value)}
                        className="px-3 py-2 border border-ink-600 rounded-lg bg-ink-700 text-parchment-100 focus:outline-none focus:ring-2 focus:ring-ink-500"
                      >
                        <option value="">All Strands</option>
                        {uniqueStrandsLessons.map(strand => (
                          <option key={strand} value={strand}>{strand}</option>
                        ))}
                      </select>

                      <div className="flex-1 text-right">
                        <span className="text-sm text-parchment-400">
                          {filteredLessons.length} of {lessons.length} lessons
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Main Content - Lessons List and Preview */}
                  <div className="flex-1 flex gap-4 overflow-hidden p-4">
                    {/* Lessons List */}
                    <div className="flex-1 overflow-y-auto min-w-0">
                      {isLoadingLessons ? (
                        <div className="flex items-center justify-center py-12">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-parchment-300"></div>
                          <span className="ml-3 text-parchment-300">Loading lessons...</span>
                        </div>
                      ) : filteredLessons.length === 0 ? (
                        <div className="text-center py-12">
                          <svg
                            className="mx-auto h-12 w-12 text-parchment-400"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                            />
                          </svg>
                          <p className="mt-4 text-lg text-parchment-300">
                            {lessons.length === 0 ? 'No permanent lessons' : 'No lessons match your filters'}
                          </p>
                          <p className="mt-2 text-sm text-parchment-400">
                            {lessons.length === 0
                              ? 'Promote a draft to create your first lesson.'
                              : 'Try adjusting your search or filters to find what you\'re looking for.'}
                          </p>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {filteredLessons.map((lesson) => (
                            <div
                              key={lesson.id}
                              className={`border rounded-lg p-4 transition-colors cursor-pointer ${
                                selectedLesson?.id === lesson.id
                                  ? 'border-parchment-300 bg-ink-700'
                                  : 'border-ink-700 hover:bg-ink-750'
                              }`}
                              onClick={() => setSelectedLesson(lesson)}
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-2">
                                    <h4 className="font-medium text-parchment-100 truncate">
                                      {lesson.title || 'Untitled Lesson'}
                                    </h4>
                                    {(lesson.grade || lesson.strand) && (
                                      <div className="flex items-center gap-1 text-xs text-parchment-400">
                                        {lesson.grade && <span>{lesson.grade}</span>}
                                        {lesson.grade && lesson.strand && <span>•</span>}
                                        {lesson.strand && <span>{lesson.strand}</span>}
                                      </div>
                                    )}
                                  </div>
                                  <p className="text-sm text-parchment-300 mb-2">
                                    {truncateContent(lesson.content)}
                                  </p>
                                  <p className="text-xs text-parchment-400">
                                    Last updated {formatDateTime(lesson.updatedAt)}
                                  </p>
                                </div>
                                <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setExportingDraft(lesson);
                                      setIsExportModalOpen(true);
                                    }}
                                    className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                                    title="Export this lesson"
                                  >
                                    Export
                                  </button>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleDemoteLesson(lesson.id);
                                    }}
                                    className="px-3 py-1.5 text-sm bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors"
                                    title="Move this lesson back to drafts"
                                  >
                                    Move to Drafts
                                  </button>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleDeleteLesson(lesson.id);
                                    }}
                                    className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                                    title="Delete this lesson"
                                  >
                                    Delete
                                  </button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Preview Panel Resizer */}
                    <div
                      className={`resizer ${isResizingLessonPreview ? 'resizing' : ''}`}
                      onMouseDown={handleLessonPreviewResizerMouseDown}
                      style={{ cursor: 'col-resize' }}
                    />

                    {/* Preview Pane */}
                    <div
                      className="flex-shrink-0"
                      style={{ width: `${lessonPreviewWidth}px` }}
                    >
                      <DraftPreview draft={selectedLesson} />
                    </div>
                  </div>
                </div>
              )}

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
                                        🕐 {formatDateTime(standard.source_file.created_at)}
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

      {/* Export Modal */}
      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        draft={exportingDraft}
        onExport={handleExportDraft}
        isLoading={isExporting}
      />

      {/* Version Comparison Modal */}
      <VersionComparisonModal
        isOpen={isVersionModalOpen}
        onClose={() => setIsVersionModalOpen(false)}
        draft={comparingDraft}
        originalContent={comparingDraft?.originalContent}
      />
      </FileOperationErrorBoundary>
    </ErrorBoundary>
  );
}
