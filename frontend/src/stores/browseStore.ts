import { create } from 'zustand';
import type { BrowseState, SettingsState } from '../types/unified';

export interface BrowseStoreState {
  // Browse state
  browseState: BrowseState;
  settingsState: SettingsState;
  
  // Actions
  setBrowseState: (state: BrowseState) => void;
  updateBrowseState: (updates: Partial<BrowseState>) => void;
  setSettingsState: (state: SettingsState) => void;
  updateSettingsState: (updates: Partial<SettingsState>) => void;
  
  // Specific actions
  setBrowseQuery: (query: string) => void;
  setProcessingMode: (mode: string) => void;
  
  // Reset actions
  resetBrowseState: () => void;
  resetSettingsState: () => void;
  resetAll: () => void;
}

const defaultBrowseState: BrowseState = {
  query: '',
};

const defaultSettingsState: SettingsState = {
  processingMode: 'cloud',
};

export const useBrowseStore = create<BrowseStoreState>((set) => ({
  browseState: defaultBrowseState,
  settingsState: defaultSettingsState,

  setBrowseState: (browseState) => set({ browseState }),
  updateBrowseState: (updates) =>
    set((state) => ({ browseState: { ...state.browseState, ...updates } })),
  setSettingsState: (settingsState) => set({ settingsState }),
  updateSettingsState: (updates) =>
    set((state) => ({ settingsState: { ...state.settingsState, ...updates } })),

  setBrowseQuery: (query) =>
    set((state) => ({ browseState: { ...state.browseState, query } })),
  setProcessingMode: (processingMode) =>
    set((state) => ({ settingsState: { ...state.settingsState, processingMode } })),

  resetBrowseState: () => set({ browseState: defaultBrowseState }),
  resetSettingsState: () => set({ settingsState: defaultSettingsState }),
  resetAll: () => set({ 
    browseState: defaultBrowseState, 
    settingsState: defaultSettingsState 
  }),
}));

// Selectors for optimized subscriptions
export const browseSelectors = {
  browseState: (state: BrowseStoreState) => state.browseState,
  settingsState: (state: BrowseStoreState) => state.settingsState,
  browseQuery: (state: BrowseStoreState) => state.browseState.query,
  processingMode: (state: BrowseStoreState) => state.settingsState.processingMode,
  
  // Computed selectors
  hasBrowseQuery: (state: BrowseStoreState) => state.browseState.query.trim().length > 0,
  isCloudProcessing: (state: BrowseStoreState) => state.settingsState.processingMode === 'cloud',
  isLocalProcessing: (state: BrowseStoreState) => state.settingsState.processingMode === 'local',
};

// Actions for external usage
export const browseActions = {
  resetBrowseState: () => useBrowseStore.getState().resetBrowseState(),
  resetSettingsState: () => useBrowseStore.getState().resetSettingsState(),
  resetAll: () => useBrowseStore.getState().resetAll(),
  setBrowseQuery: (query: string) => useBrowseStore.getState().setBrowseQuery(query),
  setProcessingMode: (mode: string) => useBrowseStore.getState().setProcessingMode(mode),
  updateBrowseState: (updates: Partial<BrowseState>) => 
    useBrowseStore.getState().updateBrowseState(updates),
  updateSettingsState: (updates: Partial<SettingsState>) => 
    useBrowseStore.getState().updateSettingsState(updates),
};