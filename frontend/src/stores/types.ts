/**
 * Shared interfaces for Zustand stores to ensure consistency
 */

export interface BaseStoreState {
  // Timestamp tracking
  lastFetched: number | null;
  
  // Error state
  error: string | null;
}

export interface LoadingState {
  isLoading: boolean;
}

export interface AsyncStoreState extends BaseStoreState, LoadingState {
  // Reset actions
  resetErrors: () => void;
  updateLastFetched: () => void;
}

export interface AsyncStoreActions {
  setError: (error: string | null) => void;
  setIsLoading: (loading: boolean) => void;
  resetErrors: () => void;
  updateLastFetched: () => void;
}

export interface SelectableState<T> {
  selected: T | null;
  setSelected: (item: T | null) => void;
}

export interface FilterableState<T> {
  filters: T;
  setFilters: (filters: T) => void;
  updateFilters: (updates: Partial<T>) => void;
}

export interface PaginatedState {
  page: number;
  pageSize: number;
  total: number;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  setTotal: (total: number) => void;
}

// Helper function to create base store actions
export const createBaseStoreActions = <T extends BaseStoreState>(
  set: (updater: (state: T) => T) => void,
  get: () => T
) => ({
  setError: (error: string | null) => set((state) => ({ ...state, error })),
  resetErrors: () => set((state) => ({ ...state, error: null })),
  updateLastFetched: () => set((state) => ({ ...state, lastFetched: Date.now() })),
});

// Helper function to create loading actions
export const createLoadingActions = <T extends LoadingState>(
  set: (updater: (state: T) => T) => void
) => ({
  setIsLoading: (isLoading: boolean) => set((state) => ({ ...state, isLoading })),
});

// Helper function to create selectable actions
export const createSelectableActions = <T, S extends SelectableState<T>>(
  set: (updater: (state: S) => S) => void
) => ({
  setSelected: (selected: T | null) => set((state) => ({ ...state, selected })),
});

// Helper function to create filterable actions
export const createFilterableActions = <T, S extends FilterableState<T>>(
  set: (updater: (state: S) => S) => void
) => ({
  setFilters: (filters: T) => set((state) => ({ ...state, filters })),
  updateFilters: (updates: Partial<T>) =>
    set((state) => ({ ...state, filters: { ...state.filters, ...updates } })),
});

// Helper function to create paginated actions
export const createPaginatedActions = <T extends PaginatedState>(
  set: (updater: (state: T) => T) => void
) => ({
  setPage: (page: number) => set((state) => ({ ...state, page })),
  setPageSize: (pageSize: number) => set((state) => ({ ...state, pageSize })),
  setTotal: (total: number) => set((state) => ({ ...state, total })),
});