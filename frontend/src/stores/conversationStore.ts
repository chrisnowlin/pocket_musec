import { create } from 'zustand';
import type { SessionResponsePayload } from '../lib/types';
import type { ChatMessage, ChatState, LessonSettings } from '../types/unified';
import { backendToFrontendGrade, backendToFrontendStrand } from '../lib/gradeUtils';
import type { BaseStoreState, LoadingState } from './types';

const WELCOME_MESSAGE_TEXT = "👋 Welcome! I'm your PocketMusec AI assistant. I'll help you craft engaging, standards-aligned music lessons.";

export const buildWelcomeMessage = (): ChatMessage => ({
  id: 'welcome',
  sender: 'ai',
  text: WELCOME_MESSAGE_TEXT,
  timestamp: new Date().toISOString(),
});

const defaultLessonSettings: LessonSettings = {
  selectedStandards: [],
  selectedGrade: 'All Grades',
  selectedStrand: 'All Strands',
  selectedObjectives: [],
  lessonContext: 'Class has recorders and a 30-minute block with mixed instruments.',
  lessonDuration: '30 minutes',
  classSize: '25',
};

const defaultChatState: ChatState = {
  input: '',
};

export interface ConversationStoreState extends BaseStoreState {
  session: SessionResponsePayload | null;
  lessonSettings: LessonSettings;
  chatState: ChatState;
  messages: ChatMessage[];
  isTyping: boolean;
  chatError: string | null;
  isLoadingConversation: boolean;
  lastFetched: number | null;

  setSession: (session: SessionResponsePayload | null) => void;
  syncLessonSettingsFromSession: (session: SessionResponsePayload | null) => void;
  updateLessonSettings: (updates: Partial<LessonSettings>) => void;
  replaceLessonSettings: (settings: LessonSettings) => void;

  setChatInput: (value: string) => void;
  resetChatInput: () => void;

  setMessages: (messages: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void;
  appendMessage: (message: ChatMessage) => void;
  resetMessages: () => void;
  updateMessageText: (id: string, updater: (current: string) => string) => void;
  updateMessageWithMetadata: (id: string, newText: string) => void;

  setIsTyping: (value: boolean) => void;
  setChatError: (value: string | null) => void;
  setIsLoadingConversation: (value: boolean) => void;
}

export const useConversationStore = create<ConversationStoreState>((set, get) => ({
  session: null,
  lessonSettings: defaultLessonSettings,
  chatState: defaultChatState,
  messages: [buildWelcomeMessage()],
  isTyping: false,
  chatError: null,
  isLoadingConversation: false,
  lastFetched: null,
  error: null,

  setSession: (session) => {
    set({ session });
    get().syncLessonSettingsFromSession(session);
  },

  syncLessonSettingsFromSession: (session) => {
    if (!session) return;

    const updates: Partial<LessonSettings> = {};

    if (session.gradeLevel) {
      updates.selectedGrade = backendToFrontendGrade(session.gradeLevel);
    }

    if (session.strandCode) {
      updates.selectedStrand = backendToFrontendStrand(session.strandCode);
    }

    if (session.selectedStandards) {
      updates.selectedStandards = session.selectedStandards;
    }

    if (session.selectedObjectives) {
      updates.selectedObjectives = session.selectedObjectives;
    }

    if (session.additionalContext !== undefined && session.additionalContext !== null) {
      updates.lessonContext = session.additionalContext;
    }

    set((state) => ({
      lessonSettings: {
        ...state.lessonSettings,
        ...updates,
      },
    }));
  },

  updateLessonSettings: (updates) => {
    set((state) => ({
      lessonSettings: {
        ...state.lessonSettings,
        ...updates,
      },
    }));
  },

  replaceLessonSettings: (settings) => {
    set({ lessonSettings: settings });
  },

  setChatInput: (value) => {
    set((state) => ({ chatState: { ...state.chatState, input: value } }));
  },

  resetChatInput: () => {
    set({ chatState: defaultChatState });
  },

  setMessages: (messages) => {
    set((state) => ({
      messages: typeof messages === 'function' ? messages(state.messages) : messages
    }));
  },

  appendMessage: (message) => {
    set((state) => ({ messages: [...state.messages, message] }));
  },

  resetMessages: () => {
    set({ messages: [buildWelcomeMessage()] });
  },

  updateMessageText: (id, updater) => {
    set((state) => ({
      messages: state.messages.map((message) =>
        message.id === id ? { ...message, text: updater(message.text) } : message
      )
    }));
  },

  updateMessageWithMetadata: (id, newText) => {
    set((state) => ({
      messages: state.messages.map((message) => {
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
    }));
  },

  setIsTyping: (value) => set({ isTyping: value }),
  setChatError: (value) => set({ chatError: value }),
  setIsLoadingConversation: (value) => set({ isLoadingConversation: value }),
  
  // Base store actions
  setError: (error: string | null) => set({ error }),
  resetErrors: () => set({ error: null, chatError: null }),
  updateLastFetched: () => set({ lastFetched: Date.now() }),
}));

export const conversationSelectors = {
  session: (state: ConversationStoreState) => state.session,
  lessonSettings: (state: ConversationStoreState) => state.lessonSettings,
  chatState: (state: ConversationStoreState) => state.chatState,
  messages: (state: ConversationStoreState) => state.messages,
  isTyping: (state: ConversationStoreState) => state.isTyping,
  chatError: (state: ConversationStoreState) => state.chatError,
  isLoadingConversation: (state: ConversationStoreState) => state.isLoadingConversation,
};

export const conversationActions = {
  setSession: (session: SessionResponsePayload | null) => useConversationStore.getState().setSession(session),
  updateLessonSettings: (updates: Partial<LessonSettings>) =>
    useConversationStore.getState().updateLessonSettings(updates),
};
