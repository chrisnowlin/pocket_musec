import { create } from 'zustand';

export type ErrorSeverity = 'error' | 'warning' | 'info';

export interface ErrorMetadata {
  source?: string; // Which component/hook threw the error
  action?: string; // What action was being performed
  timestamp: number;
  data?: any; // Additional context
}

export interface AppError {
  id: string;
  message: string;
  severity: ErrorSeverity;
  metadata: ErrorMetadata;
  dismissed: boolean;
}

interface ErrorStoreState {
  errors: AppError[];
  
  // Actions
  addError: (message: string, severity?: ErrorSeverity, metadata?: Partial<ErrorMetadata>) => string;
  dismissError: (id: string) => void;
  clearErrors: () => void;
  clearErrorsBySource: (source: string) => void;
  
  // Getters
  getActiveErrors: () => AppError[];
  getErrorsBySource: (source: string) => AppError[];
  hasActiveErrors: () => boolean;
}

const generateErrorId = () => `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

export const useErrorStore = create<ErrorStoreState>((set, get) => ({
  errors: [],

  addError: (message, severity = 'error', metadata = {}) => {
    const id = generateErrorId();
    const error: AppError = {
      id,
      message,
      severity,
      metadata: {
        timestamp: Date.now(),
        ...metadata,
      },
      dismissed: false,
    };
    
    set((state) => ({
      errors: [...state.errors, error],
    }));
    
    return id;
  },

  dismissError: (id) => {
    set((state) => ({
      errors: state.errors.map((error) =>
        error.id === id ? { ...error, dismissed: true } : error
      ),
    }));
  },

  clearErrors: () => {
    set({ errors: [] });
  },

  clearErrorsBySource: (source) => {
    set((state) => ({
      errors: state.errors.filter((error) => error.metadata.source !== source),
    }));
  },

  getActiveErrors: () => {
    return get().errors.filter((error) => !error.dismissed);
  },

  getErrorsBySource: (source) => {
    return get().errors.filter((error) => error.metadata.source === source);
  },

  hasActiveErrors: () => {
    return get().errors.some((error) => !error.dismissed);
  },
}));

// Selectors
export const errorSelectors = {
  errors: (state: ErrorStoreState) => state.errors,
  activeErrors: (state: ErrorStoreState) => state.errors.filter((e) => !e.dismissed),
  errorCount: (state: ErrorStoreState) => state.errors.filter((e) => !e.dismissed).length,
  hasErrors: (state: ErrorStoreState) => state.errors.some((e) => !e.dismissed),
  
  // By severity
  criticalErrors: (state: ErrorStoreState) => 
    state.errors.filter((e) => !e.dismissed && e.severity === 'error'),
  warnings: (state: ErrorStoreState) => 
    state.errors.filter((e) => !e.dismissed && e.severity === 'warning'),
  infos: (state: ErrorStoreState) => 
    state.errors.filter((e) => !e.dismissed && e.severity === 'info'),
};

// Actions for external usage
export const errorActions = {
  addError: (message: string, severity?: ErrorSeverity, metadata?: Partial<ErrorMetadata>) =>
    useErrorStore.getState().addError(message, severity, metadata),
  dismissError: (id: string) => useErrorStore.getState().dismissError(id),
  clearErrors: () => useErrorStore.getState().clearErrors(),
  clearErrorsBySource: (source: string) => useErrorStore.getState().clearErrorsBySource(source),
};