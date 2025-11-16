import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

interface Slide {
  id: string;
  title: string;
  subtitle?: string;
  key_points?: string[];
  teacher_script?: string;
  duration_minutes?: number;
  standard_codes?: string[];
  media_url?: string;
  slide_number: number;
}

interface ExportAsset {
  format: string;
  url_or_path: string;
  generated_at: string;
  file_size_bytes: number;
}

interface PresentationDetail {
  id: string;
  presentation_id: string;
  lesson_id: string;
  lesson_revision: number;
  version: string;
  status: string;
  style: string;
  slide_count: number;
  created_at: string;
  updated_at: string;
  has_exports: boolean;
  error_code?: string;
  error_message?: string;
  title?: string;
  description?: string;
  total_slides?: number;
  total_duration_minutes?: number;
  is_stale?: boolean;
  slides: Slide[];
  export_assets: ExportAsset[];
}

const PresentationViewer: React.FC = () => {
  const { presentationId } = useParams<{ presentationId: string }>();
  const navigate = useNavigate();

  const [presentation, setPresentation] = useState<PresentationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [viewMode, setViewMode] = useState<'slides' | 'export'>('slides');
  const [exporting, setExporting] = useState<string | null>(null);

  useEffect(() => {
    if (presentationId) {
      loadPresentation(presentationId);
    }
  }, [presentationId]);

  const loadPresentation = async (id: string) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/presentations/${id}`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setPresentation(data);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to load presentation');
      }
    } catch (err: any) {
      console.error('Failed to load presentation:', err);
      setError(err.message || 'Failed to load presentation');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: string) => {
    if (!presentationId) return;

    try {
      setExporting(format);
      const response = await fetch(`/api/presentations/${presentationId}/export?format=${format}`, {
        credentials: 'include'
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `presentation_${presentationId}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to export presentation');
      }
    } catch (err: any) {
      console.error('Export failed:', err);
      setError(err.message || 'Failed to export presentation');
    } finally {
      setExporting(null);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'running': 'bg-blue-100 text-blue-800',
      'completed': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800',
      'cancelled': 'bg-gray-100 text-gray-800'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-800'}`}>
        {status}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const nextSlide = () => {
    if (presentation && currentSlide < presentation.slides.length - 1) {
      setCurrentSlide(currentSlide + 1);
    }
  };

  const prevSlide = () => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ink-600"></div>
      </div>
    );
  }

  if (error || !presentation) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex items-start">
            <svg className="h-5 w-5 text-red-400 mt-0.5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
              <div className="mt-4">
                <button
                  onClick={() => navigate('/presentations')}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  ← Back to Presentations
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-parchment-100">
      {/* Header */}
      <div className="bg-parchment-50 shadow-sm border-b border-ink-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/presentations')}
                className="text-ink-400 hover:text-ink-600"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div>
                <h1 className="text-xl font-semibold text-ink-900">
                  {presentation.title || `Presentation ${presentation.presentation_id}`}
                </h1>
                <p className="text-sm text-ink-600">
                  Lesson ID: {presentation.lesson_id} • {presentation.slides.length} slides
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {getStatusBadge(presentation.status)}
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setViewMode('slides')}
                  className={`px-3 py-1 rounded-md text-sm font-medium ${
                    viewMode === 'slides'
                      ? 'bg-parchment-200 text-ink-700'
                      : 'text-ink-500 hover:text-ink-700'
                  }`}
                >
                  Slides
                </button>
                <button
                  onClick={() => setViewMode('export')}
                  className={`px-3 py-1 rounded-md text-sm font-medium ${
                    viewMode === 'export'
                      ? 'bg-parchment-200 text-ink-700'
                      : 'text-ink-500 hover:text-ink-700'
                  }`}
                >
                  Export
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {viewMode === 'slides' ? (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Slide Navigation */}
            <div className="lg:col-span-1">
              <div className="bg-parchment-50 rounded-lg shadow p-4">
                <h3 className="text-sm font-medium text-ink-900 mb-3">Slides</h3>
                <div className="space-y-1 max-h-96 overflow-y-auto">
                  {presentation.slides.map((slide, index) => (
                    <button
                      key={slide.id}
                      onClick={() => setCurrentSlide(index)}
                      className={`w-full text-left p-3 rounded-md text-sm transition-colors ${
                        currentSlide === index
                          ? 'bg-parchment-200 text-ink-700 border-ink-300 border'
                          : 'hover:bg-parchment-100 text-ink-700'
                      }`}
                    >
                      <div className="font-medium">Slide {index + 1}</div>
                      <div className="text-ink-500 truncate">{slide.title}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Presentation Info */}
              <div className="bg-parchment-50 rounded-lg shadow p-4 mt-4">
                <h3 className="text-sm font-medium text-ink-900 mb-3">Details</h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-ink-500">Created:</span>
                    <span className="ml-2 text-ink-900">{formatDate(presentation.created_at)}</span>
                  </div>
                  <div>
                    <span className="text-ink-500">Style:</span>
                    <span className="ml-2 text-ink-900">{presentation.style}</span>
                  </div>
                  <div>
                    <span className="text-ink-500">Version:</span>
                    <span className="ml-2 text-ink-900">{presentation.version}</span>
                  </div>
                  {presentation.total_duration_minutes && (
                    <div>
                      <span className="text-ink-500">Duration:</span>
                      <span className="ml-2 text-ink-900">{presentation.total_duration_minutes} min</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Slide Content */}
            <div className="lg:col-span-3">
              <div className="bg-parchment-50 rounded-lg shadow">
                {/* Slide Header */}
                <div className="border-b border-ink-200 px-6 py-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-medium text-ink-900">
                      Slide {currentSlide + 1} of {presentation.slides.length}
                    </h2>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={prevSlide}
                        disabled={currentSlide === 0}
                        className="p-2 text-ink-400 hover:text-ink-600 disabled:opacity-50"
                      >
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                      </button>
                      <button
                        onClick={nextSlide}
                        disabled={currentSlide === presentation.slides.length - 1}
                        className="p-2 text-ink-400 hover:text-ink-600 disabled:opacity-50"
                      >
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Slide Body */}
                <div className="p-6">
                  {presentation.slides[currentSlide] && (
                    <div className="space-y-4">
                      <h3 className="text-2xl font-bold text-ink-900">
                        {presentation.slides[currentSlide].title}
                      </h3>

                      {presentation.slides[currentSlide].subtitle && (
                        <h4 className="text-xl text-ink-700">
                          {presentation.slides[currentSlide].subtitle}
                        </h4>
                      )}

                      {presentation.slides[currentSlide].media_url && (
                        <div className="my-6">
                          <img
                            src={presentation.slides[currentSlide].media_url}
                            alt={presentation.slides[currentSlide].title}
                            className="w-full max-w-2xl mx-auto rounded-lg shadow-md"
                          />
                        </div>
                      )}

                      {presentation.slides[currentSlide].key_points && (
                        <div>
                          <h5 className="text-lg font-semibold text-ink-900 mb-3">Key Points</h5>
                          <ul className="list-disc list-inside space-y-2 text-ink-700">
                            {presentation.slides[currentSlide].key_points?.map((point, index) => (
                              <li key={index}>{point}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {presentation.slides[currentSlide].teacher_script && (
                        <div>
                          <h5 className="text-lg font-semibold text-ink-900 mb-3">Teacher Script</h5>
                          <div className="bg-parchment-100 border border-parchment-300 rounded-md p-4">
                            <p className="text-ink-700 whitespace-pre-wrap">
                              {presentation.slides[currentSlide].teacher_script}
                            </p>
                          </div>
                        </div>
                      )}

                      {presentation.slides[currentSlide].standard_codes && (
                        <div>
                          <h5 className="text-lg font-semibold text-ink-900 mb-3">Standards</h5>
                          <div className="flex flex-wrap gap-2">
                            {presentation.slides[currentSlide].standard_codes?.map((code, index) => (
                              <span
                                key={index}
                                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
                              >
                                {code}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {presentation.slides[currentSlide].duration_minutes && (
                        <div className="text-sm text-ink-600">
                          <svg className="inline h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Duration: {presentation.slides[currentSlide].duration_minutes} minutes
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto">
            <div className="bg-parchment-50 rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-ink-900 mb-6">Export Options</h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Export Formats */}
                <div>
                  <h3 className="text-lg font-medium text-ink-900 mb-4">Available Formats</h3>
                  <div className="space-y-3">
                    <div className="border border-ink-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-ink-900">PowerPoint (PPTX)</h4>
                          <p className="text-sm text-ink-600">Microsoft PowerPoint format</p>
                        </div>
                        <button
                          onClick={() => handleExport('pptx')}
                          disabled={exporting === 'pptx'}
                          className="px-4 py-2 bg-ink-600 text-white rounded-md hover:bg-ink-700 disabled:opacity-50"
                        >
                          {exporting === 'pptx' ? 'Exporting...' : 'Export'}
                        </button>
                      </div>
                    </div>

                    <div className="border border-ink-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-ink-900">PDF</h4>
                          <p className="text-sm text-ink-600">Portable Document Format</p>
                        </div>
                        <button
                          onClick={() => handleExport('pdf')}
                          disabled={exporting === 'pdf'}
                          className="px-4 py-2 bg-ink-600 text-white rounded-md hover:bg-ink-700 disabled:opacity-50"
                        >
                          {exporting === 'pdf' ? 'Exporting...' : 'Export'}
                        </button>
                      </div>
                    </div>

                    <div className="border border-ink-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-ink-900">JSON</h4>
                          <p className="text-sm text-ink-600">Raw data format</p>
                        </div>
                        <button
                          onClick={() => handleExport('json')}
                          disabled={exporting === 'json'}
                          className="px-4 py-2 bg-ink-600 text-white rounded-md hover:bg-ink-700 disabled:opacity-50"
                        >
                          {exporting === 'json' ? 'Exporting...' : 'Export'}
                        </button>
                      </div>
                    </div>

                    <div className="border border-ink-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-ink-900">Markdown</h4>
                          <p className="text-sm text-ink-600">Text format with formatting</p>
                        </div>
                        <button
                          onClick={() => handleExport('markdown')}
                          disabled={exporting === 'markdown'}
                          className="px-4 py-2 bg-ink-600 text-white rounded-md hover:bg-ink-700 disabled:opacity-50"
                        >
                          {exporting === 'markdown' ? 'Exporting...' : 'Export'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Existing Exports */}
                {presentation.export_assets.length > 0 && (
                  <div>
                    <h3 className="text-lg font-medium text-ink-900 mb-4">Existing Exports</h3>
                    <div className="space-y-3">
                      {presentation.export_assets.map((asset, index) => (
                        <div key={index} className="border border-ink-200 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <h4 className="font-medium text-ink-900 uppercase">{asset.format}</h4>
                              <p className="text-sm text-ink-600">
                                Created: {formatDate(asset.generated_at)} •
                                Size: {formatFileSize(asset.file_size_bytes)}
                              </p>
                            </div>
                            <button
                              onClick={() => {
                                const a = document.createElement('a');
                                a.href = asset.url_or_path;
                                a.download = `presentation_${presentation.presentationId}.${asset.format}`;
                                document.body.appendChild(a);
                                a.click();
                                document.body.removeChild(a);
                              }}
                              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                            >
                              Download
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PresentationViewer;