import { useState } from 'react';
import type { ExportModalProps, ExportFormat } from '../../types/unified';

export default function ExportModal({
  isOpen,
  onClose,
  draft,
  onExport,
  isLoading,
}: ExportModalProps) {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('markdown');

  if (!isOpen || !draft) return null;

  const handleExport = () => {
    onExport(selectedFormat);
  };

  const formatOptions: { value: ExportFormat; label: string; description: string }[] = [
    {
      value: 'markdown',
      label: 'Markdown',
      description: 'Plain text format with markdown formatting',
    },
    {
      value: 'pdf',
      label: 'PDF',
      description: 'Formatted document for printing and sharing',
    },
    {
      value: 'docx',
      label: 'Plain Text',
      description: 'Text file format (.txt) with metadata',
    },
  ];

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
    >
      <div
        className="workspace-card rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-ink-800">Export Draft</h3>
          <button 
            onClick={onClose} 
            className="text-ink-500 hover:text-ink-700 transition-colors"
            disabled={isLoading}
          >
            ✕
          </button>
        </div>

        {/* Draft Info */}
        <div className="bg-ink-50 rounded-lg p-3">
          <h4 className="font-medium text-ink-800 truncate">
            {draft.title || 'Untitled Draft'}
          </h4>
          <div className="flex items-center gap-2 text-xs text-ink-500 mt-1">
            {(draft.grade || draft.strand) && (
              <>
                {draft.grade && <span>{draft.grade}</span>}
                {draft.grade && draft.strand && <span>•</span>}
                {draft.strand && <span>{draft.strand}</span>}
              </>
            )}
            <span>•</span>
            <span>Created {formatDate(draft.createdAt)}</span>
          </div>
        </div>

        {/* Format Selection */}
        <div className="space-y-3">
          <label className="block text-sm font-medium text-ink-700">
            Export Format
          </label>
          <div className="space-y-2">
            {formatOptions.map((option) => (
              <label
                key={option.value}
                className="flex items-start gap-3 p-3 border border-ink-200 rounded-lg cursor-pointer hover:bg-parchment-50 transition-colors"
              >
                <input
                  type="radio"
                  name="format"
                  value={option.value}
                  checked={selectedFormat === option.value}
                  onChange={(e) => setSelectedFormat(e.target.value as ExportFormat)}
                  className="mt-1 text-ink-600 focus:ring-ink-500"
                  disabled={isLoading}
                />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-ink-800">{option.label}</div>
                  <div className="text-sm text-ink-600">{option.description}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-ink-200">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-parchment-200 text-ink-700 rounded-md hover:bg-parchment-300 transition-colors"
            disabled={isLoading}
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={isLoading}
            className="px-4 py-2 bg-ink-600 text-white rounded-md hover:bg-ink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isLoading && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            )}
            {isLoading ? 'Exporting...' : `Export as ${formatOptions.find(f => f.value === selectedFormat)?.label}`}
          </button>
        </div>
      </div>
    </div>
  );
}