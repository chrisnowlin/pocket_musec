import { create } from 'zustand';
import type { ViewMode } from '../types/unified';

interface ConversationEditorState {
  open: boolean;
  content: string;
  sessionId: string | null;
  isSaving: boolean;
}

interface DeleteConfirmState {
  open: boolean;
  sessionId: string | null;
}

interface UIStoreState {
  mode: ViewMode;
  imageModalOpen: boolean;
  draftsModalOpen: boolean;
  conversationEditor: ConversationEditorState;
  deleteConfirm: DeleteConfirmState;
  clearAllHistoryConfirmOpen: boolean;

  setMode: (mode: ViewMode) => void;
  setImageModalOpen: (open: boolean) => void;
  setDraftsModalOpen: (open: boolean) => void;

  openConversationEditor: (sessionId: string, content: string) => void;
  closeConversationEditor: () => void;
  setConversationEditorSaving: (saving: boolean) => void;
  seedConversationEditor: (sessionId: string | null, content: string) => void;

  openDeleteConfirm: (sessionId: string) => void;
  closeDeleteConfirm: () => void;

  setClearAllHistoryConfirmOpen: (open: boolean) => void;
}

export const useUIStore = create<UIStoreState>((set) => ({
  mode: 'chat',
  imageModalOpen: false,
  draftsModalOpen: false,
  conversationEditor: {
    open: false,
    content: '',
    sessionId: null,
    isSaving: false,
  },
  deleteConfirm: {
    open: false,
    sessionId: null,
  },
  clearAllHistoryConfirmOpen: false,

  setMode: (mode) => set({ mode }),
  setImageModalOpen: (open) => set({ imageModalOpen: open }),
  setDraftsModalOpen: (open) => set({ draftsModalOpen: open }),

  openConversationEditor: (sessionId, content) =>
    set({
      conversationEditor: {
        open: true,
        content,
        sessionId,
        isSaving: false,
      },
    }),
  closeConversationEditor: () =>
    set({
      conversationEditor: {
        open: false,
        content: '',
        sessionId: null,
        isSaving: false,
      },
    }),
  setConversationEditorSaving: (isSaving) =>
    set((state) => ({
      conversationEditor: {
        ...state.conversationEditor,
        isSaving,
      },
    })),
  seedConversationEditor: (sessionId, content) =>
    set((state) => ({
      conversationEditor: {
        ...state.conversationEditor,
        sessionId,
        content,
      },
    })),

  openDeleteConfirm: (sessionId) =>
    set({
      deleteConfirm: {
        open: true,
        sessionId,
      },
    }),
  closeDeleteConfirm: () =>
    set({
      deleteConfirm: {
        open: false,
        sessionId: null,
      },
    }),

  setClearAllHistoryConfirmOpen: (open) => set({ clearAllHistoryConfirmOpen: open }),
}));

export const uiSelectors = {
  mode: (state: UIStoreState) => state.mode,
  imageModalOpen: (state: UIStoreState) => state.imageModalOpen,
  draftsModalOpen: (state: UIStoreState) => state.draftsModalOpen,
  conversationEditor: (state: UIStoreState) => state.conversationEditor,
  deleteConfirm: (state: UIStoreState) => state.deleteConfirm,
  clearAllHistoryConfirmOpen: (state: UIStoreState) => state.clearAllHistoryConfirmOpen,
};
