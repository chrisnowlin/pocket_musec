import type { ChatMessage as ChatMessageType } from '../../types/unified';
import MarkdownRenderer from '../MarkdownRenderer';

interface ChatMessageProps {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  return (
    <div
      className={`flex gap-3 items-start ${
        message.sender === 'user' ? 'justify-end' : ''
      }`}
    >
      {message.sender === 'ai' && (
        <div className="w-8 h-8 bg-ink-600 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
          <svg
            className="w-5 h-5 text-parchment-100"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
            />
          </svg>
        </div>
      )}
      <div className={message.sender === 'user' ? 'flex justify-end w-full' : 'flex-1 max-w-3xl'}>
        <div
          className={
            message.sender === 'user' ? 'flex flex-col items-end max-w-[80%]' : 'w-full'
          }
        >
          <div
            className={`flex items-center gap-2 mb-2 ${
              message.sender === 'user' ? 'justify-end' : ''
            }`}
          >
            <span className="text-xs font-semibold text-ink-700">
              {message.sender === 'ai' ? 'PocketMusec AI' : 'You'}
            </span>
            <span className="text-xs text-ink-400">•</span>
            <span className="text-xs text-ink-600">Just now</span>
          </div>
          <div
            className={`rounded-lg shadow-sm border px-4 py-3 ${
              message.sender === 'ai'
                ? 'bg-parchment-50 border-ink-300 text-ink-800'
                : 'bg-ink-700 text-parchment-100'
            } ${message.sender === 'user' ? 'w-fit max-w-full' : ''}`}
          >
            {message.sender === 'ai' ? (
              <MarkdownRenderer content={message.text} className="text-sm leading-relaxed" />
            ) : (
              <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                {message.text}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
