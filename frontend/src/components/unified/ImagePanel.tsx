import { RefObject, ChangeEvent, DragEvent, useMemo } from 'react';
import type { ImageData, StorageInfo } from '../../types/unified';
import FileDropzone from './FileDropzone';
import PanelLayout from './PanelLayout';
import PanelHeader from './PanelHeader';
import ClassificationBadge from './ClassificationBadge';

interface ImagePanelProps {
  images: ImageData[];
  storageInfo: StorageInfo | null;
  selectedImage: ImageData | null;
  isUploading: boolean;
  uploadProgress: number;
  uploadError: string | null;
  imageDragActive: boolean;
  filters: {
    category?: string;
    education_level?: string;
    difficulty_level?: string;
  };
  onImageSelect: (image: ImageData) => void;
  onFileSelect: (event: ChangeEvent<HTMLInputElement>) => void;
  onDrop: (event: DragEvent<HTMLDivElement>) => void;
  onDeleteImage: (id: string) => void;
  onDragOver: (active: boolean) => void;
  onFiltersChange: (filters: {
    category?: string;
    education_level?: string;
    difficulty_level?: string;
  }) => void;
  fileInputRef: RefObject<HTMLInputElement>;
}

export default function ImagePanel({
  images,
  storageInfo,
  selectedImage,
  isUploading,
  uploadProgress,
  uploadError,
  imageDragActive,
  filters,
  onImageSelect,
  onFileSelect,
  onDrop,
  onDeleteImage,
  onDragOver,
  onFiltersChange,
  fileInputRef,
}: ImagePanelProps) {
  // Get unique values for filter options
  const categories = useMemo(() => {
    const cats = [...new Set(images
      .map(img => img.classification?.category)
      .filter(Boolean)
    )];
    return cats.sort();
  }, [images]);

  const educationLevels = useMemo(() => {
    const levels = [...new Set(images
      .map(img => img.classification?.education_level)
      .filter(Boolean)
    )];
    return levels.sort();
  }, [images]);

  const difficultyLevels = useMemo(() => {
    const levels = [...new Set(images
      .map(img => img.classification?.difficulty_level)
      .filter(Boolean)
    )];
    return levels.sort();
  }, [images]);

  const recentImages = useMemo(() => images.slice(0, 3), [images]);

  const handleFilterChange = (filterType: 'category' | 'education_level' | 'difficulty_level', value: string) => {
    const newFilters = { ...filters };
    
    if (value === 'all') {
      delete newFilters[filterType];
    } else {
      newFilters[filterType] = value;
    }
    
    onFiltersChange(newFilters);
  };

  return (
    <div className="h-full overflow-y-auto px-6 py-4">
      <div className="max-w-4xl mx-auto">
        <PanelHeader
          title="Image Processing"
          subtitle="Upload sheet music, diagrams, and other images for OCR and AI analysis"
          className="mb-4"
        />

        {/* Classification Filters */}
        {images.length > 0 && (
          <PanelLayout className="p-4 mb-6">
            <h3 className="text-sm font-semibold text-ink-800 mb-3">Filters</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-ink-700 mb-1">Category</label>
                <select
                  value={filters.category || 'all'}
                  onChange={(e) => handleFilterChange('category', e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-ink-300 rounded-md bg-parchment-50 text-ink-800"
                >
                  <option value="all">All Categories</option>
                  {categories.map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-700 mb-1">Education Level</label>
                <select
                  value={filters.education_level || 'all'}
                  onChange={(e) => handleFilterChange('education_level', e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-ink-300 rounded-md bg-parchment-50 text-ink-800"
                >
                  <option value="all">All Levels</option>
                  {educationLevels.map(level => (
                    <option key={level} value={level}>{level}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-700 mb-1">Difficulty Level</label>
                <select
                  value={filters.difficulty_level || 'all'}
                  onChange={(e) => handleFilterChange('difficulty_level', e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-ink-300 rounded-md bg-parchment-50 text-ink-800"
                >
                  <option value="all">All Difficulties</option>
                  {difficultyLevels.map(level => (
                    <option key={level} value={level}>{level}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="mt-2 text-xs text-ink-600">
              Showing {images.length} images
            </div>
          </PanelLayout>
        )}

        {/* Storage Info */}
        {storageInfo && (
          <PanelLayout className="p-6 mb-6">
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
          </PanelLayout>
        )}

        {/* Upload Area */}
        <FileDropzone
          isActive={imageDragActive}
          onDragActiveChange={onDragOver}
          onDrop={onDrop}
          fileInputRef={fileInputRef}
          onFileSelect={onFileSelect}
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors mb-6 ${
            imageDragActive
              ? 'border-ink-500 bg-parchment-200'
              : 'border-ink-300 hover:border-ink-400 bg-parchment-50'
          }`}
        >
          {(openFileDialog) => (
            <>
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
                  onClick={openFileDialog}
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
            </>
          )}
        </FileDropzone>

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
                <PanelLayout
                  key={image.id}
                  className="p-4 hover:shadow-lg transition-shadow cursor-pointer"
                >
                  <div onClick={() => onImageSelect(image)}>
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
                    {image.classification && (
                      <div className="mt-3">
                        <ClassificationBadge classification={image.classification} />
                      </div>
                    )}
                  </div>
                </PanelLayout>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
