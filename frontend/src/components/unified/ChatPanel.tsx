import { useRef, useEffect, MouseEvent as ReactMouseEvent, RefObject } from 'react';
import type { ChatMessage as ChatMessageType } from '../../types/unified';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';

interface ChatPanelProps {
  messages: ChatMessageType[];
  isTyping: boolean;
  chatInput: string;
  setChatInput: (value: string) => void;
  onSendMessage: () => void;
  sessionError: string | null;
  chatError: string | null;
  messageContainerHeight: number | null;
  onResizerMouseDown: (
    event: ReactMouseEvent<HTMLDivElement>,
    ref: RefObject<HTMLDivElement>
  ) => void;
  resizing: boolean;
  isLoadingConversation?: boolean;
  onUpdateMessage?: (id: string, newText: string) => void;
}

export default function ChatPanel({
  messages,
  isTyping,
  chatInput,
  setChatInput,
  onSendMessage,
  sessionError,
  chatError,
  messageContainerHeight,
  onResizerMouseDown,
  resizing,
  isLoadingConversation = false,
  onUpdateMessage,
}: ChatPanelProps) {
  const messageContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messageContainerRef.current) {
      messageContainerRef.current.scrollTop = messageContainerRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  return (
    <div className="h-full flex flex-col">
      <div className="flex flex-col flex-1 min-h-0">
        <div
          className={`resizer-horizontal ${resizing ? 'resizing' : ''}`}
          onMouseDown={(event) => onResizerMouseDown(event, messageContainerRef)}
        />
        <div
          ref={messageContainerRef}
          id="chatMessagesContainer"
          className="flex-1 scrollable px-6 py-4 space-y-4 workspace-card"
          style={messageContainerHeight ? { height: `${messageContainerHeight}px`, flexShrink: 0 } : {}}
        >
          <div className="border-b border-ink-300 pb-4 mb-4">
            <h2 className="text-lg font-semibold text-ink-800">Lesson Planning Chat</h2>
            <p className="text-sm text-ink-600">Conversational AI guidance</p>
          </div>
          
          {isLoadingConversation ? (
            <div className="flex items-center justify-center py-8">
              <div className="flex items-center gap-2">
                <div className="typing-indicator flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-full bg-ink-500" />
                  <span className="w-2.5 h-2.5 rounded-full bg-ink-500" />
                  <span className="w-2.5 h-2.5 rounded-full bg-ink-500" />
                </div>
                <span className="text-xs text-ink-600">Loading conversation...</span>
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onUpdateMessage={onUpdateMessage}
                  citations={message.citations}
                  lessonId={message.lessonId}
                />
              ))}

              {isTyping && (
                <div className="flex items-center gap-2">
                  <div className="typing-indicator flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-ink-500" />
                    <span className="w-2.5 h-2.5 rounded-full bg-ink-500" />
                    <span className="w-2.5 h-2.5 rounded-full bg-ink-500" />
                  </div>
                  <span className="text-xs text-ink-600">PocketMusec is typing...</span>
                </div>
              )}
            </>
          )}

          <ChatInput
            value={chatInput}
            onChange={setChatInput}
            onSend={onSendMessage}
            disabled={isTyping || isLoadingConversation}
            sessionError={sessionError}
            chatError={chatError}
          />
        </div>
      </div>
    </div>
  );
}
