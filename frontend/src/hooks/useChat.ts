import { useCallback, useEffect, useRef } from 'react';
import api from '../lib/api';
import type { ChatMessage, ChatSender } from '../types/unified';
import type { SessionResponsePayload, ChatResponsePayload } from '../lib/types';
import { useConversationStore, buildWelcomeMessage } from '../stores/conversationStore';

interface UseChatProps {
  session: SessionResponsePayload | null;
  lessonDuration: string;
  classSize: string;
}

export function useChat({ session, lessonDuration, classSize }: UseChatProps) {
  const messages = useConversationStore((state) => state.messages);
  const setMessages = useConversationStore((state) => state.setMessages);
  const appendStoreMessage = useConversationStore((state) => state.appendMessage);
  const resetStoreMessages = useConversationStore((state) => state.resetMessages);
  const isTyping = useConversationStore((state) => state.isTyping);
  const setIsTyping = useConversationStore((state) => state.setIsTyping);
  const chatError = useConversationStore((state) => state.chatError);
  const setChatError = useConversationStore((state) => state.setChatError);
  const isLoadingConversation = useConversationStore((state) => state.isLoadingConversation);
  const setIsLoadingConversation = useConversationStore((state) => state.setIsLoadingConversation);
  const lastLoadedSessionRef = useRef<string | null>(null);

  // Generate stable message IDs based on content and timestamp
  const generateMessageId = useCallback((sender: ChatSender, text: string, index?: number): string => {
    if (index !== undefined) {
      // For loaded messages, use a stable format
      const hash = simpleHash(text);
      return `${sender}-loaded-${index}-${hash}`;
    } else {
      // For new messages, use timestamp
      return `${sender}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }
  }, []);

  const simpleHash = (str: string): string => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36);
  };

  const appendMessage = useCallback((sender: ChatSender, text: string, id?: string) => {
    const messageId = id ?? generateMessageId(sender, text);
    appendStoreMessage({
      id: messageId,
      sender,
      text,
      timestamp: new Date().toISOString(),
    });
    return messageId;
  }, [appendStoreMessage, generateMessageId]);

  const updateMessageText = useCallback((id: string, updater: (current: string) => string) => {
    setMessages((prev) =>
      prev.map((message) =>
        message.id === id ? { ...message, text: updater(message.text) } : message
      )
    );
  }, []);

  const updateMessageWithMetadata = useCallback((id: string, newText: string) => {
    setMessages((prev) =>
      prev.map((message) => {
        if (message.id === id) {
          // If this is the first modification, store the original text
          if (!message.isModified && !message.originalText) {
            return {
              ...message,
              text: newText,
              originalText: message.text,
              isModified: true
            };
          }
          // If already modified, just update the text
          return {
            ...message,
            text: newText,
            isModified: true
          };
        }
        return message;
      })
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

      // Add user message and track its status
      const userMessageId = appendMessage('user', messageText);
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
        let isPersisted = false;

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
                  if (event.type === 'persisted') {
                    // Backend confirmed conversation was saved
                    isPersisted = event.session_updated;
                    if (!isPersisted) {
                      console.warn('Conversation save had issues:', event.message);
                    }
                  } else if (event.type === 'delta' && event.text) {
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

        // If we never got a persisted confirmation, mark as error
        if (!isPersisted) {
          console.warn('No persistence confirmation received for messages');
        }

      } catch (err: any) {
        console.error('Chat message failed:', err);
        setChatError(err.message || 'Failed to send your message');
        updateMessageText(aiMessageId, () => 'Sorry, I could not generate a response.');
      } finally {
        setIsTyping(false);
      }
    },
    [session?.id, lessonDuration, classSize, appendMessage, updateMessageText, updateMessageStatus]
  );

  const resetMessages = useCallback(() => {
    resetStoreMessages();
  }, [resetStoreMessages]);

  const loadDraftContent = useCallback((draftTitle: string, draftContent: string) => {
    const introText = draftTitle
      ? `📄 Loaded draft "${draftTitle}". Continue refining it here or ask for updates.`
      : '📄 Loaded draft content. Continue refining it here or ask for updates.';

    const introId = generateMessageId('ai', introText);
    const draftMessageId = generateMessageId('ai', draftContent);
    const now = new Date().toISOString();

    const draftMessages: ChatMessage[] = [
      buildWelcomeMessage(),
      {
        id: introId,
        sender: 'ai',
        text: introText,
        timestamp: now,
      },
      {
        id: draftMessageId,
        sender: 'ai',
        text: draftContent,
        timestamp: now,
      },
    ];

    setMessages(draftMessages);
    setChatError(null);
    lastLoadedSessionRef.current = null;
  }, [generateMessageId]);

  const loadConversationMessages = useCallback(async (sessionData: SessionResponsePayload) => {
    // Skip if same session was already loaded
    if (lastLoadedSessionRef.current === sessionData.id && messages.length > 1) {
      return;
    }

    if (!sessionData.conversation_history) {
      resetMessages();
      lastLoadedSessionRef.current = sessionData.id;
      return;
    }

    setIsLoadingConversation(true);
    try {
      const conversationHistory = JSON.parse(sessionData.conversation_history);
      
      // Start with welcome message
      const restoredMessages: ChatMessage[] = [buildWelcomeMessage()];

      conversationHistory.forEach((message: any, index: number) => {
        if (message.role === 'user') {
          const messageId = generateMessageId('user', message.content, index);
          restoredMessages.push({
            id: messageId,
            sender: 'user',
            text: message.content,
            timestamp: new Date().toISOString(),
          });
        } else if (message.role === 'assistant') {
          const messageId = generateMessageId('ai', message.content, index);
          restoredMessages.push({
            id: messageId,
            sender: 'ai',
            text: message.content,
            timestamp: new Date().toISOString(),
          });
        }
      });

      // Use incremental update instead of complete replacement
      setMessages(prev => {
        // If this is a new session or we have no messages, replace completely
        if (lastLoadedSessionRef.current !== sessionData.id || prev.length <= 1) {
          return restoredMessages;
        }
        
        // Otherwise, merge with existing messages while preserving streaming state
        const existingIds = new Set(prev.map(m => m.id));
        const newMessages = restoredMessages.filter(m => !existingIds.has(m.id));
        return [...prev, ...newMessages];
      });

      lastLoadedSessionRef.current = sessionData.id;
    } catch (error) {
      console.error('Failed to load conversation history:', error);
      resetMessages();
      lastLoadedSessionRef.current = null;
    } finally {
      setIsLoadingConversation(false);
    }
  }, [resetMessages, generateMessageId, messages.length]);

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
    updateMessageText,
    updateMessageWithMetadata,
    generateMessageId,
    loadDraftContent,
  };
}
