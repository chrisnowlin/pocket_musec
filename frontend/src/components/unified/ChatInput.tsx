import { useRef, FormEvent } from 'react';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
  sessionError?: string | null;
  chatError?: string | null;
}

export default function ChatInput({
  value,
  onChange,
  onSend,
  disabled,
  sessionError,
  chatError,
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleTextareaInput = (event: FormEvent<HTMLTextAreaElement>) => {
    const target = event.currentTarget;
    target.style.height = 'auto';
    target.style.height = `${Math.min(target.scrollHeight, 180)}px`;
  };

  const handleSend = () => {
    if (!value.trim() || disabled) return;
    onSend();
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  return (
    <div className="border-t border-ink-300 pt-4 mt-4">
      <div className="flex gap-3 items-end">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onInput={handleTextareaInput}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                handleSend();
              }
            }}
            className="w-full border border-ink-300 rounded-xl px-4 py-3 pr-12 resize-none focus:outline-none focus:ring-2 focus:ring-ink-500 focus:border-transparent text-sm bg-parchment-50 text-ink-800"
            rows={1}
            placeholder="Type a message or use the buttons above..."
            disabled={disabled}
          />
          <button className="absolute right-3 bottom-3 text-ink-500 hover:text-ink-700 transition-colors">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
              />
            </svg>
          </button>
        </div>
        <button
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          className="bg-ink-700 hover:bg-ink-800 text-parchment-100 rounded-xl px-6 py-3 font-medium transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </div>
      {sessionError && (
        <div className="mt-2 rounded-md bg-parchment-300 px-3 py-2 text-xs text-ink-800 border border-ink-400">
          {sessionError}
        </div>
      )}
      {chatError && (
        <div className="mt-2 rounded-md bg-parchment-300 px-3 py-2 text-xs text-ink-800 border border-ink-500">
          {chatError}
        </div>
      )}
    </div>
  );
}
