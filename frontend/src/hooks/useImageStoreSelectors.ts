import { useMemo } from 'react';
import { shallow } from 'zustand/shallow';
import { useImageStore, imageSelectors } from '../stores/imageStore';

// Memoized selectors for performance optimization
export const useImageStoreData = () => {
  return useImageStore(
    (state) => ({
      images: state.images,
      storageInfo: state.storageInfo,
      selectedImage: state.selectedImage,
      isLoading: state.isLoading,
      isUploading: state.isUploading,
      uploadProgress: state.uploadProgress,
      error: state.error,
      uploadError: state.uploadError,
      imageDragActive: state.imageDragActive,
      filters: state.filters,
    }),
    shallow
  );
};

export const useImageStoreComputed = () => {
  const { images, filters } = useImageStoreData();
  
  return useMemo(() => ({
    hasImages: images.length > 0,
    isStorageInfoLoaded: false, // Will be derived from storageInfo
    hasSelectedImage: false, // Will be derived from selectedImage
    isAnyLoading: false, // Will be derived from loading states
    hasAnyError: false, // Will be derived from error states
    
    // Expensive computed values
    filteredImages: images.filter(img => {
      if (filters.category && img.classification?.category !== filters.category) return false;
      if (filters.educationLevel && img.classification?.educationLevel !== filters.educationLevel) return false;
      if (filters.difficultyLevel && img.classification?.difficultyLevel !== filters.difficultyLevel) return false;
      return true;
    }),
    
    imagesByCategory: images.reduce((acc, img) => {
      const category = img.classification?.category || 'uncategorized';
      acc[category] = (acc[category] || []).concat(img);
      return acc;
    }, {} as Record<string, typeof images>),
    
    imagesByEducationLevel: images.reduce((acc, img) => {
      const level = img.classification?.educationLevel || 'unknown';
      acc[level] = (acc[level] || []).concat(img);
      return acc;
    }, {} as Record<string, typeof images>),
    
    imagesByDifficultyLevel: images.reduce((acc, img) => {
      const level = img.classification?.difficultyLevel || 'unknown';
      acc[level] = (acc[level] || []).concat(img);
      return acc;
    }, {} as Record<string, typeof images>),
  }), [images, filters]);
};

export const useImageStoreActions = () => {
  return useImageStore(
    (state) => ({
      setImages: state.setImages,
      setStorageInfo: state.setStorageInfo,
      setSelectedImage: state.setSelectedImage,
      setIsLoading: state.setIsLoading,
      setIsUploading: state.setIsUploading,
      setUploadProgress: state.setUploadProgress,
      setError: state.setError,
      setUploadError: state.setUploadError,
      setImageDragActive: state.setImageDragActive,
      setFilters: state.setFilters,
      updateFilters: state.updateFilters,
      resetErrors: state.resetErrors,
      resetImageState: state.resetImageState,
    }),
    shallow
  );
};