import { create } from 'zustand';
import type { 
  PresentationDocument, 
  PresentationSummary, 
  PresentationStatus 
} from '../types/presentations';

export interface PresentationStoreState {
  // Data
  presentations: PresentationSummary[];
  currentPresentation: PresentationDocument | null;
  
  // Loading states
  isLoading: boolean;
  isGenerating: boolean;
  isExporting: boolean;
  lastFetched: number | null;
  
  // Error states
  error: string | null;
  
  // Actions
  setPresentations: (presentations: PresentationSummary[]) => void;
  setCurrentPresentation: (presentation: PresentationDocument | null) => void;
  setIsLoading: (loading: boolean) => void;
  setIsGenerating: (generating: boolean) => void;
  setIsExporting: (exporting: boolean) => void;
  setError: (error: string | null) => void;
  updateLastFetched: () => void;
  
  // Update actions
  addPresentation: (presentation: PresentationSummary) => void;
  removePresentation: (presentationId: string) => void;
  updatePresentation: (presentationId: string, updates: Partial<PresentationSummary>) => void;
  
  // Reset actions
  resetPresentationState: () => void;
  resetErrors: () => void;
}

const initialState = {
  presentations: [],
  currentPresentation: null,
  isLoading: false,
  isGenerating: false,
  isExporting: false,
  lastFetched: null,
  error: null,
};

export const usePresentationStore = create<PresentationStoreState>((set, get) => ({
  ...initialState,

  setPresentations: (presentations) => set({ presentations }),
  setCurrentPresentation: (currentPresentation) => set({ currentPresentation }),
  setIsLoading: (isLoading) => set({ isLoading }),
  setIsGenerating: (isGenerating) => set({ isGenerating }),
  setIsExporting: (isExporting) => set({ isExporting }),
  setError: (error) => set({ error }),
  
  updateLastFetched: () => set({ lastFetched: Date.now() }),
  
  addPresentation: (presentation) => 
    set((state) => ({ presentations: [...state.presentations, presentation] })),
    
  removePresentation: (presentationId) =>
    set((state) => ({
      presentations: state.presentations.filter(p => p.id !== presentationId),
      currentPresentation: state.currentPresentation?.id === presentationId ? null : state.currentPresentation
    })),
    
  updatePresentation: (presentationId, updates) =>
    set((state) => ({
      presentations: state.presentations.map(p => 
        p.id === presentationId ? { ...p, ...updates } : p
      ),
      currentPresentation: state.currentPresentation?.id === presentationId 
        ? { ...state.currentPresentation, ...updates } as PresentationDocument
        : state.currentPresentation
    })),
  
  resetPresentationState: () => set(initialState),
  resetErrors: () => set({ error: null }),
}));

// Selectors for optimized subscriptions
export const presentationSelectors = {
  presentations: (state: PresentationStoreState) => state.presentations,
  currentPresentation: (state: PresentationStoreState) => state.currentPresentation,
  isLoading: (state: PresentationStoreState) => state.isLoading,
  isGenerating: (state: PresentationStoreState) => state.isGenerating,
  isExporting: (state: PresentationStoreState) => state.isExporting,
  error: (state: PresentationStoreState) => state.error,
  lastFetched: (state: PresentationStoreState) => state.lastFetched,
  
  // Computed selectors
  hasPresentations: (state: PresentationStoreState) => state.presentations.length > 0,
  hasCurrentPresentation: (state: PresentationStoreState) => state.currentPresentation !== null,
  isAnyLoading: (state: PresentationStoreState) => state.isLoading || state.isGenerating || state.isExporting,
  hasError: (state: PresentationStoreState) => state.error !== null,
  
  // Helper selectors
  getPresentationById: (state: PresentationStoreState, id: string) => 
    state.presentations.find(p => p.id === id),
  getPresentationsByLessonId: (state: PresentationStoreState, lessonId: string) =>
    state.presentations.filter(p => p.lesson_id === lessonId),
  getCompletedPresentations: (state: PresentationStoreState) =>
    state.presentations.filter(p => p.status === 'complete'),
  getPendingPresentations: (state: PresentationStoreState) =>
    state.presentations.filter(p => p.status === 'pending'),
};

// Actions for external usage
export const presentationActions = {
  resetPresentationState: () => usePresentationStore.getState().resetPresentationState(),
  resetErrors: () => usePresentationStore.getState().resetErrors(),
  updateLastFetched: () => usePresentationStore.getState().updateLastFetched(),
  addPresentation: (presentation: PresentationSummary) => usePresentationStore.getState().addPresentation(presentation),
  removePresentation: (presentationId: string) => usePresentationStore.getState().removePresentation(presentationId),
  updatePresentation: (presentationId: string, updates: Partial<PresentationSummary>) => 
    usePresentationStore.getState().updatePresentation(presentationId, updates),
};
