import { useState, useRef, useEffect } from 'react';

interface ConversationMenuProps {
  sessionId: string;
  onDelete: (sessionId: string) => void;
  onOpenEditor: (sessionId: string) => void;
}

export default function ConversationMenu({
  sessionId,
  onDelete,
  onOpenEditor,
}: ConversationMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        menuRef.current &&
        buttonRef.current &&
        !menuRef.current.contains(event.target as Node) &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOpen]);

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering the conversation button click
    setIsOpen(!isOpen);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(false);
    onDelete(sessionId);
  };

  const handleOpenEditor = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(false);
    onOpenEditor(sessionId);
  };

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        onClick={handleToggle}
        className="p-1 rounded hover:bg-ink-700 text-parchment-400 hover:text-parchment-100 transition-colors"
        aria-label="Conversation options"
        type="button"
      >
        <svg
          className="w-4 h-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
        >
          <circle cx="12" cy="5" r="1" />
          <circle cx="12" cy="12" r="1" />
          <circle cx="12" cy="19" r="1" />
        </svg>
      </button>

      {isOpen && (
        <div
          ref={menuRef}
          className="absolute right-0 top-full mt-1 bg-ink-700 border border-ink-600 rounded-lg shadow-lg z-50 min-w-[160px]"
        >
          <div className="py-1">
            <button
              onClick={handleOpenEditor}
              className="w-full text-left px-3 py-2 text-sm text-parchment-200 hover:bg-ink-600 hover:text-parchment-100 transition-colors flex items-center gap-2"
            >
              <svg
                className="w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
              Open Editor
            </button>
            <button
              onClick={handleDelete}
              className="w-full text-left px-3 py-2 text-sm text-parchment-200 hover:bg-ink-600 hover:text-red-300 transition-colors flex items-center gap-2"
            >
              <svg
                className="w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              Delete Conversation
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

