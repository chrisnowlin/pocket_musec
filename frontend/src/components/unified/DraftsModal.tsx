import { useState, useMemo, useCallback } from 'react';
import LessonEditor from './LessonEditor';
import DraftPreview from './DraftPreview';
import ExportModal from './ExportModal';
import ErrorBoundary from '../ErrorBoundary';
import type { DraftsModalProps, ExportFormat, DraftItem } from '../../types/unified';

export default function DraftsModal({
  isOpen,
  onClose,
  drafts,
  isLoading,
  onOpenDraft,
  onDeleteDraft,
  onUpdateDraft,
}: DraftsModalProps) {
  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGrade, setSelectedGrade] = useState('');
  const [selectedStrand, setSelectedStrand] = useState('');
  const [selectedDraft, setSelectedDraft] = useState<DraftItem | null>(null);
  
  // Editor state
  const [isEditing, setIsEditing] = useState(false);
  const [editingDraft, setEditingDraft] = useState<DraftItem | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  
  // Export state
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [exportingDraft, setExportingDraft] = useState<DraftItem | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  // Helper functions - must be hooks (useCallback)
  const formatDate = useCallback((dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }, []);

  const truncateContent = useCallback((content: string, maxLength: number = 100) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength).trim() + '...';
  }, []);

  // Get unique grades and strands for filters
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

  // Filter drafts based on search and filters
  const filteredDrafts = useMemo(() => {
    return drafts.filter(draft => {
      const matchesSearch = searchQuery === '' ||
        draft.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        draft.content.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesGrade = selectedGrade === '' || draft.grade === selectedGrade;
      const matchesStrand = selectedStrand === '' || draft.strand === selectedStrand;
      
      return matchesSearch && matchesGrade && matchesStrand;
    });
  }, [drafts, searchQuery, selectedGrade, selectedStrand]);

  // Clear all filters
  const clearFilters = useCallback(() => {
    setSearchQuery('');
    setSelectedGrade('');
    setSelectedStrand('');
  }, []);

  // Handle edit draft
  const handleEditDraft = useCallback((draft: DraftItem) => {
    setEditingDraft(draft);
    setIsEditing(true);
  }, []);

  // Handle save edited draft
  const handleSaveEditedDraft = useCallback(async (content: string) => {
    if (!editingDraft || !onUpdateDraft) return;
    
    setIsSaving(true);
    try {
      const updatedDraft = await onUpdateDraft(editingDraft.id, {
        content,
        title: editingDraft.title,
      });
      
      if (updatedDraft) {
        setIsEditing(false);
        setEditingDraft(null);
        // Update selected draft if it's the one being edited
        if (selectedDraft?.id === editingDraft.id) {
          setSelectedDraft(updatedDraft);
        }
      }
    } catch (error) {
      console.error('Failed to save draft:', error);
    } finally {
      setIsSaving(false);
    }
  }, [editingDraft, onUpdateDraft, selectedDraft]);

  // Handle cancel edit
  const handleCancelEdit = useCallback(() => {
    setIsEditing(false);
    setEditingDraft(null);
  }, []);

  // Handle export draft
  const handleExportDraft = useCallback(async (format: ExportFormat) => {
    if (!exportingDraft) return;
    
    setIsExporting(true);
    try {
      const metadata = {
        title: exportingDraft.title || 'Untitled Draft',
        grade: exportingDraft.grade,
        strand: exportingDraft.strand,
        createdAt: formatDate(exportingDraft.createdAt),
        updatedAt: formatDate(exportingDraft.updatedAt),
      };
      
      switch (format) {
        case 'markdown':
          // Create markdown content with metadata
          const markdownContent = `# ${metadata.title}

${metadata.grade ? `**Grade:** ${metadata.grade}` : ''}
${metadata.strand ? `**Strand:** ${metadata.strand}` : ''}
**Created:** ${metadata.createdAt}
**Last Updated:** ${metadata.updatedAt}

---

${exportingDraft.content}`;
          
          // Download as markdown file
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
          // Open print dialog for PDF export
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
          // Plain text export (replacing invalid DOCX implementation)
          // Note: This exports as .txt to ensure compatibility and validity
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
  }, [exportingDraft, formatDate]);

  // Early return AFTER all hooks
  if (!isOpen) return null;

  // If editing, show the lesson editor
  if (isEditing && editingDraft) {
    return (
      <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/60 p-4">
        <div className="w-full h-full max-h-[90vh] flex flex-col">
          {isSaving && (
            <div className="absolute top-4 right-4 z-90 bg-blue-100 text-blue-800 px-3 py-2 rounded-md text-sm flex items-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              Saving draft...
            </div>
          )}
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
    );
  }

  return (
    <>
      <div
        className="fixed inset-0 z-[70] flex items-center justify-center bg-black/60 p-4"
        onClick={onClose}
      >
        <div
          className="workspace-card rounded-2xl max-w-6xl w-full max-h-[85vh] p-6 shadow-xl space-y-4 flex flex-col"
          onClick={(event) => event.stopPropagation()}
        >
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-ink-800">Saved Drafts</h3>
            <button onClick={onClose} className="text-ink-500 hover:text-ink-700">
              ✕
            </button>
          </div>

          {/* Search and Filters */}
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="flex-1 relative">
                <input
                  type="text"
                  placeholder="Search drafts by title or content..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-ink-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-ink-500 focus:border-transparent"
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
                onClick={clearFilters}
                className="px-4 py-2 bg-parchment-200 text-ink-700 rounded-md hover:bg-parchment-300 transition-colors text-sm"
              >
                Clear Filters
              </button>
            </div>
            
            <div className="flex items-center gap-3">
              <select
                value={selectedGrade}
                onChange={(e) => setSelectedGrade(e.target.value)}
                className="px-3 py-2 border border-ink-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-ink-500 focus:border-transparent"
              >
                <option value="">All Grades</option>
                {uniqueGrades.map(grade => (
                  <option key={grade} value={grade}>{grade}</option>
                ))}
              </select>
              
              <select
                value={selectedStrand}
                onChange={(e) => setSelectedStrand(e.target.value)}
                className="px-3 py-2 border border-ink-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-500 focus:border-transparent"
              >
                <option value="">All Strands</option>
                {uniqueStrands.map(strand => (
                  <option key={strand} value={strand}>{strand}</option>
                ))}
              </select>
              
              <div className="flex-1 text-right">
                <span className="text-sm text-ink-500">
                  {filteredDrafts.length} of {drafts.length} drafts
                </span>
              </div>
            </div>
          </div>

          {/* Main Content - Draft List and Preview */}
          <div className="flex-1 flex gap-4 overflow-hidden">
            {/* Draft List */}
            <div className="flex-1 overflow-y-auto min-w-0">
              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ink-600"></div>
                  <span className="ml-3 text-ink-600">Loading drafts...</span>
                </div>
              ) : filteredDrafts.length === 0 ? (
                <div className="text-center py-12">
                  <svg
                    className="mx-auto h-12 w-12 text-ink-400"
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
                  <p className="mt-4 text-lg text-ink-600">
                    {drafts.length === 0 ? 'No saved drafts' : 'No drafts match your filters'}
                  </p>
                  <p className="mt-2 text-sm text-ink-500">
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
                          ? 'border-ink-400 bg-parchment-50'
                          : 'border-ink-200 hover:bg-parchment-50'
                      }`}
                      onClick={() => setSelectedDraft(draft)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2">
                            <h4 className="font-medium text-ink-800 truncate">
                              {draft.title || 'Untitled Draft'}
                            </h4>
                            {(draft.grade || draft.strand) && (
                              <div className="flex items-center gap-1 text-xs text-ink-500">
                                {draft.grade && <span>{draft.grade}</span>}
                                {draft.grade && draft.strand && <span>•</span>}
                                {draft.strand && <span>{draft.strand}</span>}
                              </div>
                            )}
                          </div>
                          <p className="text-sm text-ink-600 mb-2">
                            {truncateContent(draft.content)}
                          </p>
                          <p className="text-xs text-ink-500">
                            Last updated {formatDate(draft.updatedAt)}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 ml-4 flex-shrink-0">
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
                              onOpenDraft(draft.id);
                            }}
                            className="px-3 py-1.5 text-sm bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700 transition-colors"
                            title="Continue editing this draft"
                          >
                            Open
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onDeleteDraft(draft.id);
                            }}
                            className="px-3 py-1.5 text-sm bg-parchment-200 text-ink-700 rounded-md hover:bg-parchment-300 transition-colors"
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

            {/* Preview Pane */}
            <div className="w-96 flex-shrink-0">
              <DraftPreview draft={selectedDraft} />
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end pt-4 border-t border-ink-200">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-parchment-200 text-ink-700 rounded-md hover:bg-parchment-300 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>

      {/* Export Modal */}
      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        draft={exportingDraft}
        onExport={handleExportDraft}
        isLoading={isExporting}
      />
    </>
  );
}
