import { RefObject, ChangeEvent, DragEvent, useMemo } from 'react';
import type { ImageData, StorageInfo } from '../../types/unified';

interface ImagePanelProps {
  images: ImageData[];
  storageInfo: StorageInfo | null;
  selectedImage: ImageData | null;
  isUploading: boolean;
  uploadProgress: number;
  uploadError: string | null;
  imageDragActive: boolean;
  onImageSelect: (image: ImageData) => void;
  onFileSelect: (event: ChangeEvent<HTMLInputElement>) => void;
  onDrop: (event: DragEvent<HTMLDivElement>) => void;
  onDeleteImage: (id: string) => void;
  onDragOver: (active: boolean) => void;
  fileInputRef: RefObject<HTMLInputElement>;
}

export default function ImagePanel({
  images,
  storageInfo,
  isUploading,
  uploadProgress,
  uploadError,
  imageDragActive,
  onImageSelect,
  onFileSelect,
  onDrop,
  onDeleteImage,
  onDragOver,
  fileInputRef,
}: ImagePanelProps) {
  const recentImages = useMemo(() => images.slice(0, 3), [images]);

  return (
    <div className="h-full overflow-y-auto px-6 py-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-ink-800">Image Processing</h2>
          <p className="text-ink-600 mt-2">
            Upload sheet music, diagrams, and other images for OCR and AI analysis
          </p>
        </div>

        {/* Storage Info */}
        {storageInfo && (
          <div className="workspace-card p-6 mb-6">
            <h3 className="text-lg font-semibold text-ink-800 mb-4">Storage Usage</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-ink-600">Images:</span>
                <span className="font-medium text-ink-800">{storageInfo.image_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-ink-600">Storage:</span>
                <span className="font-medium text-ink-800">
                  {storageInfo.usage_mb.toFixed(2)} MB / {storageInfo.limit_mb} MB
                </span>
              </div>
              <div className="w-full bg-parchment-200 rounded-full h-2.5">
                <div
                  className={`h-2.5 rounded-full ${
                    storageInfo.percentage > 90
                      ? 'bg-ink-700'
                      : storageInfo.percentage > 70
                      ? 'bg-ink-600'
                      : 'bg-ink-500'
                  }`}
                  style={{ width: `${Math.min(storageInfo.percentage, 100)}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Upload Area */}
        <div
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors mb-6 ${
            imageDragActive
              ? 'border-ink-500 bg-parchment-200'
              : 'border-ink-300 hover:border-ink-400 bg-parchment-50'
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            onDragOver(true);
          }}
          onDragLeave={(e) => {
            e.preventDefault();
            onDragOver(false);
          }}
          onDrop={onDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*"
            onChange={onFileSelect}
            className="hidden"
          />

          <svg
            className="mx-auto h-12 w-12 text-ink-500"
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

          <p className="mt-4 text-lg text-ink-700">
            Drag and drop images here, or{' '}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="text-ink-600 hover:text-ink-700 font-medium"
            >
              browse files
            </button>
          </p>
          <p className="mt-2 text-sm text-ink-600">
            Supports PNG, JPEG, GIF, WebP (max 10MB per file)
          </p>

          {isUploading && (
            <div className="mt-6 max-w-md mx-auto">
              <div className="w-full bg-parchment-200 rounded-full h-2.5">
                <div
                  className="bg-ink-600 h-2.5 rounded-full transition-all"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="mt-2 text-sm text-ink-600">Uploading... {uploadProgress}%</p>
            </div>
          )}
        </div>

        {uploadError && (
          <div className="rounded-md bg-parchment-300 p-4 mb-6 border border-ink-400">
            <div className="text-sm text-ink-800">{uploadError}</div>
          </div>
        )}

        {/* Recent Images */}
        {recentImages.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-ink-800 mb-4">Recent Images</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {recentImages.map((image) => (
                <div
                  key={image.id}
                  className="workspace-card p-4 hover:shadow-lg transition-shadow cursor-pointer"
                  onClick={() => onImageSelect(image)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-ink-800 truncate">{image.filename}</h4>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteImage(image.id);
                      }}
                      className="text-ink-700 hover:text-ink-800"
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
                  <p className="text-sm text-ink-600">
                    {new Date(image.uploaded_at).toLocaleDateString()}
                  </p>
                  {image.ocr_text && (
                    <p className="text-sm text-ink-700 mt-2 line-clamp-2">{image.ocr_text}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
