import MarkdownRenderer from '../MarkdownRenderer';
import type { DraftItem } from '../../types/unified';

interface DraftPreviewProps {
  draft: DraftItem | null;
  isLoading?: boolean;
}

export default function DraftPreview({ draft, isLoading = false }: DraftPreviewProps) {
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

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-parchment-50 rounded-lg border border-ink-200">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ink-600"></div>
          <span className="text-sm text-ink-600">Loading preview...</span>
        </div>
      </div>
    );
  }

  if (!draft) {
    return (
      <div className="h-full flex items-center justify-center bg-parchment-50 rounded-lg border border-ink-200">
        <div className="text-center">
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
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
            />
          </svg>
          <p className="mt-4 text-lg text-ink-600">No draft selected</p>
          <p className="mt-2 text-sm text-ink-500">
            Select a draft from the list to preview its content
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-parchment-50 rounded-lg border border-ink-200">
      {/* Header */}
      <div className="p-4 border-b border-ink-200 bg-white">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-ink-800 truncate">
              {draft.title || 'Untitled Draft'}
            </h3>
            <div className="flex items-center gap-2 text-xs text-ink-500 mt-1">
              {(draft.grade || draft.strand) && (
                <>
                  {draft.grade && <span>{draft.grade}</span>}
                  {draft.grade && draft.strand && <span>•</span>}
                  {draft.strand && <span>{draft.strand}</span>}
                  <span>•</span>
                </>
              )}
              <span>Created {formatDate(draft.createdAt)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 bg-white">
          {draft.content ? (
            <MarkdownRenderer 
              content={draft.content} 
              className="prose prose-sm max-w-none"
            />
          ) : (
            <div className="text-center py-8">
              <svg
                className="mx-auto h-8 w-8 text-ink-400"
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
              <p className="mt-2 text-sm text-ink-500">No content available</p>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-ink-200 bg-ink-50">
        <div className="flex items-center justify-between text-xs text-ink-500">
          <div>
            Last updated {formatDate(draft.updatedAt)}
          </div>
          <div>
            {draft.content.length} characters
          </div>
        </div>
      </div>
    </div>
  );
}