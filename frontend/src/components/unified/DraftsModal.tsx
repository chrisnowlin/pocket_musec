import type { DraftsModalProps } from '../../types/unified';

export default function DraftsModal({
  isOpen,
  onClose,
  drafts,
  isLoading,
  onOpenDraft,
  onDeleteDraft,
}: DraftsModalProps) {
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
          <h3 className="text-lg font-semibold text-ink-800">Saved Drafts</h3>
          <button onClick={onClose} className="text-ink-500 hover:text-ink-700">
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ink-600"></div>
              <span className="ml-3 text-ink-600">Loading drafts...</span>
            </div>
          ) : drafts.length === 0 ? (
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
              <p className="mt-4 text-lg text-ink-600">No saved drafts</p>
              <p className="mt-2 text-sm text-ink-500">
                Start creating a lesson and save it as a draft to see it here.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {drafts.map((draft) => (
                <div
                  key={draft.id}
                  className="border border-ink-200 rounded-lg p-4 hover:bg-parchment-50 transition-colors"
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
                        onClick={() => onOpenDraft(draft.id)}
                        className="px-3 py-1.5 text-sm bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700 transition-colors"
                        title="Continue editing this draft"
                      >
                        Open
                      </button>
                      <button
                        onClick={() => onDeleteDraft(draft.id)}
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