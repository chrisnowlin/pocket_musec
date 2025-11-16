import { create } from 'zustand';
import type { SessionResponsePayload } from '../lib/types';
import type { ChatMessage, ChatState, LessonSettings } from '../types/unified';
import { backendToFrontendGrade, backendToFrontendStrand } from '../lib/gradeUtils';

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

export interface ConversationStoreState {
  session: SessionResponsePayload | null;
  lessonSettings: LessonSettings;
  chatState: ChatState;
  messages: ChatMessage[];
  isTyping: boolean;
  chatError: string | null;
  isLoadingConversation: boolean;

  setSession: (session: SessionResponsePayload | null) => void;
  syncLessonSettingsFromSession: (session: SessionResponsePayload | null) => void;
  updateLessonSettings: (updates: Partial<LessonSettings>) => void;
  replaceLessonSettings: (settings: LessonSettings) => void;

  setChatInput: (value: string) => void;
  resetChatInput: () => void;

  setMessages: (messages: ChatMessage[]) => void;
  appendMessage: (message: ChatMessage) => void;
  resetMessages: () => void;

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

  setSession: (session) => {
    set({ session });
    get().syncLessonSettingsFromSession(session);
  },

  syncLessonSettingsFromSession: (session) => {
    if (!session) return;

    const updates: Partial<LessonSettings> = {};

    if (session.grade_level) {
      updates.selectedGrade = backendToFrontendGrade(session.grade_level);
    }

    if (session.strand_code) {
      updates.selectedStrand = backendToFrontendStrand(session.strand_code);
    }

    if (session.selected_standards) {
      updates.selectedStandards = session.selected_standards;
    }

    if (session.selected_objectives) {
      updates.selectedObjectives = session.selected_objectives;
    }

    if (session.additional_context !== undefined && session.additional_context !== null) {
      updates.lessonContext = session.additional_context;
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

  setMessages: (messages) => set({ messages }),

  appendMessage: (message) => {
    set((state) => ({ messages: [...state.messages, message] }));
  },

  resetMessages: () => {
    set({ messages: [buildWelcomeMessage()] });
  },

  setIsTyping: (value) => set({ isTyping: value }),
  setChatError: (value) => set({ chatError: value }),
  setIsLoadingConversation: (value) => set({ isLoadingConversation: value }),
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
