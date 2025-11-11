import { useState, useCallback, useEffect, ChangeEvent, DragEvent } from 'react';
import api from '../lib/api';
import type { ImageData, StorageInfo } from '../types/unified';

export function useImages() {
  const [images, setImages] = useState<ImageData[]>([]);
  const [storageInfo, setStorageInfo] = useState<StorageInfo | null>(null);
  const [selectedImage, setSelectedImage] = useState<ImageData | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [imageDragActive, setImageDragActive] = useState(false);

  const loadImages = useCallback(async () => {
    try {
      const result = await api.getImages();
      if (result.ok) {
        setImages(result.data as ImageData[]);
      } else {
        setUploadError(result.message || 'Unable to load images');
      }
    } catch (err: any) {
      console.error('Failed to load images', err);
      setUploadError(err.message || 'Unable to load images');
    }
  }, []);

  const loadStorageInfo = useCallback(async () => {
    try {
      const result = await api.getImageStorageInfo();
      if (result.ok) {
        const data = result.data as StorageInfo;
        setStorageInfo(data);
      }
    } catch (err) {
      console.error('Failed to load storage info', err);
    }
  }, []);

  const uploadFiles = useCallback(
    async (files: File[]) => {
      if (!files.length) return;
      setIsUploading(true);
      setUploadError(null);
      setUploadProgress(0);

      const formData = new FormData();
      files.forEach((file) => {
        formData.append('files', file);
      });
      formData.append('analyze_vision', 'true');

      try {
        const result = await api.uploadImages(formData, (progress) => {
          setUploadProgress(progress);
        });

        if (result.ok) {
          await loadImages();
          await loadStorageInfo();
        } else {
          setUploadError(result.message || 'Upload failed');
        }
      } catch (err: any) {
        console.error('Upload failed', err);
        setUploadError(err.message || 'Upload failed');
      } finally {
        setIsUploading(false);
        setUploadProgress(0);
      }
    },
    [loadImages, loadStorageInfo]
  );

  const handleFileSelect = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const files = event.target.files;
      if (files && files.length) {
        uploadFiles(Array.from(files));
      }
    },
    [uploadFiles]
  );

  const handleDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setImageDragActive(false);
      const files = Array.from(event.dataTransfer.files).filter((file) =>
        file.type.startsWith('image/')
      );
      if (files.length) {
        uploadFiles(files);
      }
    },
    [uploadFiles]
  );

  const handleDeleteImage = useCallback(
    async (imageId: string) => {
      try {
        const result = await api.deleteImage(imageId);
        if (result.ok) {
          await loadImages();
          await loadStorageInfo();
          if (selectedImage?.id === imageId) {
            setSelectedImage(null);
          }
        } else {
          setUploadError(result.message || 'Failed to delete image');
        }
      } catch (err: any) {
        console.error('Failed to delete image', err);
        setUploadError(err.message || 'Failed to delete image');
      }
    },
    [loadImages, loadStorageInfo, selectedImage?.id]
  );

  useEffect(() => {
    loadImages();
    loadStorageInfo();
  }, [loadImages, loadStorageInfo]);

  return {
    images,
    storageInfo,
    selectedImage,
    isUploading,
    uploadProgress,
    uploadError,
    imageDragActive,
    setSelectedImage,
    setImageDragActive,
    handleFileSelect,
    handleDrop,
    handleDeleteImage,
    loadImages,
    loadStorageInfo,
  };
}
