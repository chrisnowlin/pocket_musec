import { RefObject, ChangeEvent, DragEvent } from 'react';

interface ImageUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  isUploading: boolean;
  uploadProgress: number;
  uploadError: string | null;
  imageDragActive: boolean;
  onDrop: (event: DragEvent<HTMLDivElement>) => void;
  onDragOver: (active: boolean) => void;
  onFileSelect: (event: ChangeEvent<HTMLInputElement>) => void;
  fileInputRef: RefObject<HTMLInputElement>;
}

export default function ImageUploadModal({
  isOpen,
  onClose,
  isUploading,
  uploadProgress,
  uploadError,
  imageDragActive,
  onDrop,
  onDragOver,
  onFileSelect,
  fileInputRef,
}: ImageUploadModalProps) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
    >
      <div
        className="workspace-card rounded-2xl max-w-3xl w-full p-6 shadow-xl space-y-4"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-ink-800">Upload Images</h3>
          <button onClick={onClose} className="text-ink-500 hover:text-ink-700">
            ✕
          </button>
        </div>
        <div
          className={`border-2 rounded-2xl p-8 text-center transition-colors ${
            imageDragActive
              ? 'border-ink-500 bg-parchment-200'
              : 'border-dashed border-ink-300 bg-parchment-50'
          }`}
          onDragOver={(event) => {
            event.preventDefault();
            onDragOver(true);
          }}
          onDragLeave={(event) => {
            event.preventDefault();
            onDragOver(false);
          }}
          onDrop={onDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            onChange={onFileSelect}
          />
          <svg
            className="mx-auto h-12 w-12 text-ink-500"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <p className="mt-4 text-lg text-ink-700">
            Drag and drop images or{' '}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="text-ink-600 hover:text-ink-700 font-medium"
            >
              browse files
            </button>
          </p>
          <p className="mt-2 text-xs text-ink-600">PNG, JPEG, TIFF, WebP (max 10MB per file)</p>
          {isUploading && (
            <div className="mt-6">
              <div className="w-full bg-parchment-200 rounded-full h-2.5">
                <div
                  className="h-2.5 rounded-full bg-ink-600 transition-all"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-xs text-ink-600 mt-2">
                Uploading — {uploadProgress}% complete
              </p>
            </div>
          )}
        </div>
        {uploadError && (
          <p className="text-sm text-ink-800 bg-parchment-300 px-3 py-2 rounded-md border border-ink-500">
            {uploadError}
          </p>
        )}
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-parchment-200 text-ink-700 rounded-md hover:bg-parchment-300"
          >
            Cancel
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2 bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700"
          >
            Browse Files
          </button>
        </div>
      </div>
    </div>
  );
}
