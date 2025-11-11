import { useState, useCallback, useRef, useEffect } from 'react';
import api from '../lib/api';

interface ImageData {
  id: string;
  filename: string;
  uploaded_at: string;
  ocr_text: string | null;
  vision_analysis: string | null;
  file_size: number;
  mime_type: string;
}

interface StorageInfo {
  total_images: number;
  total_size_bytes: number;
  total_size_mb: number;
  quota_mb: number;
  used_percentage: number;
}

interface ImagesResponse {
  images: ImageData[];
}

interface StorageInfoResponse {
  image_count: number;
  usage_mb: number;
  limit_mb: number;
  percentage: number;
}

interface UploadResponse {
  results: Array<{
    success: boolean;
    filename?: string;
    error?: string;
  }>;
}

export default function ImagesPage() {
  const [images, setImages] = useState<ImageData[]>([]);
  const [storageInfo, setStorageInfo] = useState<StorageInfo | null>(null);
  const [selectedImage, setSelectedImage] = useState<ImageData | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadImages = useCallback(async () => {
    try {
      const result = await api.getImages();
      if (result.ok) {
        const data = result.data as ImagesResponse;
        setImages(data.images);
      } else {
        setError(result.message || 'Failed to load images');
      }
    } catch (err) {
      console.error('Failed to load images:', err);
      setError('Failed to load images');
    }
  }, []);

  const loadStorageInfo = useCallback(async () => {
    try {
      const result = await api.getImageStorageInfo();
      if (result.ok) {
        const data = result.data as StorageInfoResponse;
        setStorageInfo({
          total_images: data.image_count,
          total_size_bytes: data.usage_mb * 1024 * 1024,
          total_size_mb: data.usage_mb,
          quota_mb: data.limit_mb,
          used_percentage: data.percentage,
        });
      }
    } catch (err) {
      console.error('Failed to load storage info:', err);
    }
  }, []);

  useEffect(() => {
    loadImages();
    loadStorageInfo();
  }, [loadImages, loadStorageInfo]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files).filter(file =>
      file.type.startsWith('image/')
    );

    if (files.length > 0) {
      await uploadFiles(files);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      uploadFiles(Array.from(files));
    }
  }, []);

  const uploadFiles = async (files: File[]) => {
    setIsUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });
      formData.append('processing_mode', 'cloud');

      const result = await api.uploadImages(formData, (progress) => {
        setUploadProgress(progress);
      });

      if (result.ok) {
        const data = result.data as UploadResponse;
        const successCount = data.results?.filter((r) => r.success).length || 0;
        if (successCount > 0) {
          await loadImages();
          await loadStorageInfo();
        }

        const failedCount = data.results?.filter((r) => !r.success).length || 0;
        if (failedCount > 0) {
          setError(`${failedCount} file(s) failed to upload`);
        }
      } else {
        setError(result.message || 'Failed to upload images');
      }
    } catch (err: any) {
      console.error('Upload failed:', err);
      setError(err.message || 'Failed to upload images');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDelete = async (imageId: string) => {
    if (!confirm('Are you sure you want to delete this image?')) {
      return;
    }

    try {
      const result = await api.deleteImage(imageId);
      if (result.ok) {
        await loadImages();
        await loadStorageInfo();
        if (selectedImage?.id === imageId) {
          setSelectedImage(null);
        }
      } else {
        setError(result.message || 'Failed to delete image');
      }
    } catch (err: any) {
      console.error('Delete failed:', err);
      setError(err.message || 'Failed to delete image');
    }
  };

  const filteredImages = searchQuery
    ? images.filter(img =>
        img.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
        img.ocr_text?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        img.vision_analysis?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : images;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Image Processing</h1>
        <p className="mt-2 text-gray-600">
          Upload sheet music, diagrams, and other images for OCR and AI analysis
        </p>
      </div>

      {/* Storage Info */}
      {storageInfo && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Storage Usage</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Images:</span>
              <span className="font-medium">{storageInfo.total_images}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Storage:</span>
              <span className="font-medium">
                {storageInfo.total_size_mb.toFixed(2)} MB / {storageInfo.quota_mb} MB
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className={`h-2.5 rounded-full ${
                  storageInfo.used_percentage > 90
                    ? 'bg-red-600'
                    : storageInfo.used_percentage > 70
                    ? 'bg-yellow-600'
                    : 'bg-blue-600'
                }`}
                style={{ width: `${Math.min(storageInfo.used_percentage, 100)}%` }}
              ></div>
            </div>
          </div>
        </div>
      )}

      {/* Upload Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
        />

        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>

        <p className="mt-4 text-lg text-gray-600">
          Drag and drop images here, or{' '}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            browse files
          </button>
        </p>
        <p className="mt-2 text-sm text-gray-500">
          Supports PNG, JPEG, GIF, WebP (max 10MB per file)
        </p>

        {isUploading && (
          <div className="mt-6 max-w-md mx-auto">
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            <p className="mt-2 text-sm text-gray-600">Uploading... {uploadProgress}%</p>
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      {/* Search */}
      {images.length > 0 && (
        <div>
          <input
            type="text"
            placeholder="Search images by filename or content..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      {/* Image Gallery */}
      {filteredImages.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredImages.map((image) => (
            <div
              key={image.id}
              className="bg-white shadow rounded-lg overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setSelectedImage(image)}
            >
              <div className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-gray-900 truncate">{image.filename}</h3>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(image.id);
                    }}
                    className="text-red-600 hover:text-red-700"
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>

                <div className="text-sm text-gray-600 mb-2">
                  {new Date(image.uploaded_at).toLocaleDateString()}
                </div>

                {image.ocr_text && (
                  <div className="mt-2">
                    <p className="text-xs text-gray-500 font-medium">OCR Text:</p>
                    <p className="text-sm text-gray-700 line-clamp-3">{image.ocr_text}</p>
                  </div>
                )}

                {image.vision_analysis && (
                  <div className="mt-2">
                    <p className="text-xs text-gray-500 font-medium">AI Analysis:</p>
                    <p className="text-sm text-gray-700 line-clamp-3">{image.vision_analysis}</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : images.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">No images uploaded yet</p>
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-500">No images match your search</p>
        </div>
      )}

      {/* Image Detail Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedImage(null)}
        >
          <div
            className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-2xl font-bold text-gray-900">{selectedImage.filename}</h2>
                <button
                  onClick={() => setSelectedImage(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-500">Uploaded: {new Date(selectedImage.uploaded_at).toLocaleString()}</p>
                  <p className="text-sm text-gray-500">Size: {(selectedImage.file_size / 1024).toFixed(2)} KB</p>
                  <p className="text-sm text-gray-500">Type: {selectedImage.mime_type}</p>
                </div>

                {selectedImage.ocr_text && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">OCR Extracted Text</h3>
                    <div className="bg-gray-50 rounded p-4">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{selectedImage.ocr_text}</p>
                    </div>
                  </div>
                )}

                {selectedImage.vision_analysis && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">AI Vision Analysis</h3>
                    <div className="bg-blue-50 rounded p-4">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{selectedImage.vision_analysis}</p>
                    </div>
                  </div>
                )}

                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => handleDelete(selectedImage.id)}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                  >
                    Delete
                  </button>
                  <button
                    onClick={() => setSelectedImage(null)}
                    className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
