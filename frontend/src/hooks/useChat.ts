import { useState, useCallback, useEffect } from 'react';
import api from '../lib/api';
import type { ChatMessage, ChatSender } from '../types/unified';
import type { SessionResponsePayload, ChatResponsePayload } from '../lib/types';

interface UseChatProps {
  session: SessionResponsePayload | null;
  lessonDuration: string;
  classSize: string;
}

export function useChat({ session, lessonDuration, classSize }: UseChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'ai',
      text: "👋 Welcome! I'm your PocketMusec AI assistant. I'll help you craft engaging, standards-aligned music lessons.",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [isLoadingConversation, setIsLoadingConversation] = useState(false);

  const appendMessage = useCallback((sender: ChatSender, text: string, id?: string) => {
    const messageId = id ?? `${sender}-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: messageId,
        sender,
        text,
        timestamp: new Date().toISOString(),
      },
    ]);
    return messageId;
  }, []);

  const updateMessageText = useCallback((id: string, updater: (current: string) => string) => {
    setMessages((prev) =>
      prev.map((message) =>
        message.id === id ? { ...message, text: updater(message.text) } : message
      )
    );
  }, []);

  const processChatMessage = useCallback(
    async (messageText: string, onComplete?: (session: SessionResponsePayload) => void) => {
      const activeSessionId = session?.id;
      if (!activeSessionId) {
        setChatError('Start a session before chatting with the AI.');
        return;
      }

      setIsTyping(true);
      setChatError(null);

      const aiMessageId = appendMessage('ai', '');

      try {
        const response = await api.streamChatMessage(activeSessionId, {
          message: messageText,
          lesson_duration: lessonDuration,
          class_size: classSize,
        });

        if (!response.ok || !response.body) {
          throw new Error('Streaming is unavailable.');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          let boundary = buffer.indexOf('\n\n');
          while (boundary !== -1) {
            const chunk = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);
            if (chunk.startsWith('data:')) {
              const payload = chunk.replace(/^data:\s*/, '');
              if (payload && payload !== '[DONE]') {
                try {
                  const event = JSON.parse(payload);
                  if (event.type === 'delta' && event.text) {
                    updateMessageText(aiMessageId, (current) => `${current} ${event.text}`.trim());
                  } else if (event.type === 'status' && event.message) {
                    updateMessageText(aiMessageId, () => event.message);
                  } else if (event.type === 'complete') {
                    const payloadData = event.payload as ChatResponsePayload;
                    updateMessageText(aiMessageId, () => payloadData.response);
                    if (onComplete) {
                      onComplete(payloadData.session);
                    }
                  }
                } catch (err) {
                  console.error('Failed to parse stream event', err);
                }
              }
            }
            boundary = buffer.indexOf('\n\n');
          }
        }
      } catch (err: any) {
        console.error('Chat message failed:', err);
        setChatError(err.message || 'Failed to send your message');
        updateMessageText(aiMessageId, () => 'Sorry, I could not generate a response.');
      } finally {
        setIsTyping(false);
      }
    },
    [session?.id, lessonDuration, classSize, appendMessage, updateMessageText]
  );

  const resetMessages = useCallback(() => {
    setMessages([
      {
        id: 'welcome',
        sender: 'ai',
        text: "👋 Welcome! I'm your PocketMusec AI assistant. I'll help you craft engaging, standards-aligned music lessons.",
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);

  const loadConversationMessages = useCallback(async (sessionData: SessionResponsePayload) => {
    if (!sessionData.conversation_history) {
      resetMessages();
      return;
    }

    setIsLoadingConversation(true);
    try {
      const conversationHistory = JSON.parse(sessionData.conversation_history);
      const restoredMessages: ChatMessage[] = [
        {
          id: 'welcome',
          sender: 'ai',
          text: "👋 Welcome! I'm your PocketMusec AI assistant. I'll help you craft engaging, standards-aligned music lessons.",
          timestamp: new Date().toISOString(),
        },
      ];

      conversationHistory.forEach((message: any, index: number) => {
        if (message.role === 'user') {
          restoredMessages.push({
            id: `user-${index}-${Date.now()}`,
            sender: 'user',
            text: message.content,
            timestamp: new Date().toISOString(),
          });
        } else if (message.role === 'assistant') {
          restoredMessages.push({
            id: `ai-${index}-${Date.now()}`,
            sender: 'ai',
            text: message.content,
            timestamp: new Date().toISOString(),
          });
        }
      });

      setMessages(restoredMessages);
    } catch (error) {
      console.error('Failed to load conversation history:', error);
      resetMessages();
    } finally {
      setIsLoadingConversation(false);
    }
  }, [resetMessages]);

  // Load conversation messages when session changes
  useEffect(() => {
    if (session) {
      loadConversationMessages(session);
    }
  }, [session, loadConversationMessages]);

  return {
    messages,
    isTyping,
    chatError,
    appendMessage,
    processChatMessage,
    resetMessages,
    setChatError,
    isLoadingConversation,
    loadConversationMessages,
  };
}
