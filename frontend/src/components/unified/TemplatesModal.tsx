import type { TemplatesModalProps } from '../../types/unified';

export default function TemplatesModal({
  isOpen,
  onClose,
  templates,
  isLoading,
  onSelectTemplate,
  onDeleteTemplate,
}: TemplatesModalProps) {
  if (!isOpen) return null;

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

  const truncateContent = (content: string, maxLength: number = 100) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength).trim() + '...';
  };

  const truncateDescription = (description: string, maxLength: number = 150) => {
    if (description.length <= maxLength) return description;
    return description.substring(0, maxLength).trim() + '...';
  };

  return (
    <div
      className="fixed inset-0 z-[70] flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
    >
      <div
        className="workspace-card rounded-2xl max-w-4xl w-full max-h-[80vh] p-6 shadow-xl space-y-4 flex flex-col"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-ink-800">Lesson Templates</h3>
          <button onClick={onClose} className="text-ink-500 hover:text-ink-700">
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ink-600"></div>
              <span className="ml-3 text-ink-600">Loading templates...</span>
            </div>
          ) : templates.length === 0 ? (
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
              <p className="mt-4 text-lg text-ink-600">No saved templates</p>
              <p className="mt-2 text-sm text-ink-500">
                Create a lesson and save it as a template to see it here.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {templates.map((template) => (
                <div
                  key={template.id}
                  className="border border-ink-200 rounded-lg p-4 hover:bg-parchment-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-medium text-ink-800 truncate">
                          {template.name}
                        </h4>
                        <div className="flex items-center gap-1 text-xs text-ink-500">
                          <span>{template.grade}</span>
                          <span>•</span>
                          <span>{template.strand}</span>
                        </div>
                      </div>
                      
                      {template.description && (
                        <p className="text-sm text-ink-600 mb-2">
                          {truncateDescription(template.description)}
                        </p>
                      )}
                      
                      <p className="text-sm text-ink-600 mb-2">
                        {truncateContent(template.content)}
                      </p>
                      
                      <div className="flex items-center gap-4 text-xs text-ink-500">
                        {template.standardCode && (
                          <span>Standard: {template.standardCode}</span>
                        )}
                        {template.lessonDuration && (
                          <span>Duration: {template.lessonDuration}</span>
                        )}
                        {template.classSize && (
                          <span>Class Size: {template.classSize}</span>
                        )}
                      </div>
                      
                      <p className="text-xs text-ink-500 mt-2">
                        Last updated {formatDate(template.updatedAt)}
                      </p>
                    </div>
                    
                    <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                      <button
                        onClick={() => onSelectTemplate(template.id)}
                        className="px-3 py-1.5 text-sm bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700 transition-colors"
                        title="Use this template"
                      >
                        Use Template
                      </button>
                      <button
                        onClick={() => onDeleteTemplate(template.id)}
                        className="px-3 py-1.5 text-sm bg-parchment-200 text-ink-700 rounded-md hover:bg-parchment-300 transition-colors"
                        title="Delete this template"
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
  );
}