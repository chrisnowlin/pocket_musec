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
        <button
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          className="absolute right-3 bottom-3 text-ink-500 hover:text-ink-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
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
