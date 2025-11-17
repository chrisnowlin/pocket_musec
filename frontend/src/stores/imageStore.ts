import { create } from 'zustand';
import { shallow } from 'zustand/shallow';
import type { ImageData, StorageInfo } from '../types/unified';

export interface ImageStoreState {
  // Data
  images: ImageData[];
  storageInfo: StorageInfo | null;
  selectedImage: ImageData | null;
  
  // Loading states
  isLoading: boolean;
  isUploading: boolean;
  uploadProgress: number;
  lastFetched: number | null;
  
  // Error states
  error: string | null;
  uploadError: string | null;
  
  // UI states
  imageDragActive: boolean;
  filters: {
    category?: string;
    educationLevel?: string;
    difficultyLevel?: string;
  };
  
  // Actions
  setImages: (images: ImageData[]) => void;
  setStorageInfo: (info: StorageInfo | null) => void;
  setSelectedImage: (image: ImageData | null) => void;
  setIsLoading: (loading: boolean) => void;
  setIsUploading: (uploading: boolean) => void;
  setUploadProgress: (progress: number) => void;
  setError: (error: string | null) => void;
  setUploadError: (error: string | null) => void;
  setImageDragActive: (active: boolean) => void;
  setFilters: (filters: ImageStoreState['filters']) => void;
  updateFilters: (updates: Partial<ImageStoreState['filters']>) => void;
  updateLastFetched: () => void;
  
  // Reset actions
  resetImageState: () => void;
  resetErrors: () => void;
}

const initialState = {
  images: [],
  storageInfo: null,
  selectedImage: null,
  isLoading: false,
  isUploading: false,
  uploadProgress: 0,
  lastFetched: null,
  error: null,
  uploadError: null,
  imageDragActive: false,
  filters: {
    category: undefined,
    educationLevel: undefined,
    difficultyLevel: undefined,
  },
};

export const useImageStore = create<ImageStoreState>((set, get) => ({
  ...initialState,

  setImages: (images) => set({ images }),
  setStorageInfo: (storageInfo) => set({ storageInfo }),
  setSelectedImage: (selectedImage) => set({ selectedImage }),
  setIsLoading: (isLoading) => set({ isLoading }),
  setIsUploading: (isUploading) => set({ isUploading }),
  setUploadProgress: (uploadProgress) => set({ uploadProgress }),
  setError: (error) => set({ error }),
  setUploadError: (uploadError) => set({ uploadError }),
  setImageDragActive: (imageDragActive) => set({ imageDragActive }),
  setFilters: (filters) => set({ filters }),
  updateFilters: (updates) => set((state) => ({ 
    filters: { ...state.filters, ...updates } 
  })),
  
  updateLastFetched: () => set({ lastFetched: Date.now() }),
  
  resetImageState: () => set(initialState),
  resetErrors: () => set({ error: null, uploadError: null }),
}));

// Selectors for optimized subscriptions
export const imageSelectors = {
  images: (state: ImageStoreState) => state.images,
  storageInfo: (state: ImageStoreState) => state.storageInfo,
  selectedImage: (state: ImageStoreState) => state.selectedImage,
  isLoading: (state: ImageStoreState) => state.isLoading,
  isUploading: (state: ImageStoreState) => state.isUploading,
  uploadProgress: (state: ImageStoreState) => state.uploadProgress,
  error: (state: ImageStoreState) => state.error,
  uploadError: (state: ImageStoreState) => state.uploadError,
  imageDragActive: (state: ImageStoreState) => state.imageDragActive,
  lastFetched: (state: ImageStoreState) => state.lastFetched,
  
  // Computed selectors
  hasImages: (state: ImageStoreState) => state.images.length > 0,
  isStorageInfoLoaded: (state: ImageStoreState) => state.storageInfo !== null,
  hasSelectedImage: (state: ImageStoreState) => state.selectedImage !== null,
  isAnyLoading: (state: ImageStoreState) => state.isLoading || state.isUploading,
  hasAnyError: (state: ImageStoreState) => state.error !== null || state.uploadError !== null,
  
  // Memoized selectors for expensive operations
  getImagesByCategory: (state: ImageStoreState, category?: string) => 
    category ? state.images.filter(img => img.classification?.category === category) : state.images,
  getImagesByEducationLevel: (state: ImageStoreState, educationLevel?: string) => 
    educationLevel ? state.images.filter(img => img.classification?.educationLevel === educationLevel) : state.images,
  getImagesByDifficultyLevel: (state: ImageStoreState, difficultyLevel?: string) => 
    difficultyLevel ? state.images.filter(img => img.classification?.difficultyLevel === difficultyLevel) : state.images,
  getFilteredImages: (state: ImageStoreState) => {
    const { images, filters } = state;
    return images.filter(img => {
      if (filters.category && img.classification?.category !== filters.category) return false;
      if (filters.educationLevel && img.classification?.educationLevel !== filters.educationLevel) return false;
      if (filters.difficultyLevel && img.classification?.difficultyLevel !== filters.difficultyLevel) return false;
      return true;
    });
  },
};

// Actions for external usage
export const imageActions = {
  resetImageState: () => useImageStore.getState().resetImageState(),
  resetErrors: () => useImageStore.getState().resetErrors(),
  updateLastFetched: () => useImageStore.getState().updateLastFetched(),
};