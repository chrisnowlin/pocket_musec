import React, { useMemo, useState, useCallback, useEffect } from 'react';
import type { PresentationDetail, SourceSection } from '../../types/presentations';
import { PresentationStatusIndicator } from './PresentationStatusIndicator';
import { DetailedProgressIndicator } from './DetailedProgressIndicator';
import { LoadingOverlay, PresentationGenerationSkeleton } from './SkeletonLoader';
import { usePresentationErrorHandler, PresentationError } from '../../errors/presentationErrors';
import apiClient from '../../services/presentationApiClient';
import { progressService } from '../../services/progressService';

interface EnhancedPresentationViewerProps {
  presentation: PresentationDetail;
  isOpen: boolean;
  onClose: () => void;
  onExport?: (format: 'json' | 'markdown' | 'pptx' | 'pdf') => void;
  isExporting?: boolean;
  onError?: (error: PresentationError) => void;
  jobId?: string; // Job ID for progress tracking
  showProgress?: boolean; // Whether to show progress overlay
}

export function EnhancedPresentationViewer({
  presentation,
  isOpen,
  onClose,
  onExport,
  isExporting = false,
  onError,
  jobId,
  showProgress = false
}: EnhancedPresentationViewerProps) {
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [showTeacherScript, setShowTeacherScript] = useState(true);
  const [exportError, setExportError] = useState<PresentationError | null>(null);
  const [exportProgress, setExportProgress] = useState<string | null>(null);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [regenerationJobId, setRegenerationJobId] = useState<string | null>(null);
  const [currentJobStatus, setCurrentJobStatus] = useState<any>(null);

  const { handleError, getRecoveryActions } = usePresentationErrorHandler();

  // Handle current job status updates
  useEffect(() => {
    if (!jobId || !showProgress) return;

    const subscription = {
      jobId,
      onProgress: (update: any) => {
        if (update.job_status) {
          setCurrentJobStatus(update.job_status);
        }
      },
      onError: (error: Error) => {
        console.error('Job progress error:', error);
      }
    };

    progressService.subscribe(subscription);

    return () => {
      progressService.unsubscribe(jobId);
    };
  }, [jobId, showProgress]);

  if (!isOpen) return null;

  const currentSlide = presentation.slides[currentSlideIndex];
  const totalSlides = presentation.slides.length;

  const isPresentationReady = presentation.status === 'complete';
  const isPresentationGenerating = showProgress && jobId;
  const isPresentationError = presentation.status === 'error';

  const goToSlide = (index: number) => {
    if (index >= 0 && index < totalSlides) {
      setCurrentSlideIndex(index);
    }
  };

  const nextSlide = () => goToSlide(currentSlideIndex + 1);
  const prevSlide = () => goToSlide(currentSlideIndex - 1);

  const handleExport = useCallback(async (format: 'json' | 'markdown' | 'pptx' | 'pdf') => {
    try {
      setExportError(null);
      setExportProgress(`Preparing ${format.toUpperCase()} export...`);

      // Call the provided onExport handler if it exists
      if (onExport) {
        onExport(format);
        return;
      }

      // Use the API client for direct export
      const blob = await apiClient.exportPresentation(presentation.id, format, {
        onProgress: (formatting, progress) => {
          setExportProgress(`Exporting ${format.toUpperCase()}: ${progress}%`);
        }
      });

      // Download the file
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `presentation_${presentation.id}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setExportProgress(`${format.toUpperCase()} export completed successfully`);

      // Clear progress after 3 seconds
      setTimeout(() => setExportProgress(null), 3000);

    } catch (error: any) {
      console.error('Export failed:', error);

      const structuredError = error.structuredError || handleError(error);
      setExportError(structuredError);

      // Call error handler if provided
      if (onError) {
        onError(structuredError);
      }
    } finally {
      setExportProgress(null);
    }
  }, [presentation.id, onExport, onError, handleError]);

  const handleRegenerate = useCallback(async () => {
    try {
      setIsRegenerating(true);
      setRegenerationJobId(null);

      // Start regeneration
      const response = await fetch(`/api/presentations/${presentation.id}/regenerate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          style: presentation.style,
          use_llm_polish: true,
          timeout_seconds: 30
        })
      });

      if (!response.ok) {
        throw new Error('Failed to start regeneration');
      }

      const result = await response.json();
      setRegenerationJobId(result.job_id);

    } catch (error) {
      console.error('Regeneration failed:', error);
      setIsRegenerating(false);
    }
  }, [presentation.id, presentation.style]);

  const handleRegenerationComplete = useCallback(() => {
    setIsRegenerating(false);
    setRegenerationJobId(null);
    // Refresh the presentation
    window.location.reload();
  }, []);

  const clearExportError = () => {
    setExportError(null);
  };

  const slideTitle = useMemo(() => {
    return (
      presentation.title ||
      presentation.slides[0]?.title ||
      'Lesson Presentation'
    );
  }, [presentation.title, presentation.slides]);

  const getExportErrorMessage = () => {
    if (!exportError) return null;

    const recoveryActions = getRecoveryActions(exportError);
    const primaryActions = recoveryActions.filter(action => action.type === 'primary');
    const secondaryActions = recoveryActions.filter(action => action.type === 'secondary');

    return (
      <div className="space-y-4">
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex items-start">
            <svg className="h-5 w-5 text-yellow-400 mt-0.5 mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <h4 className="text-sm font-medium text-yellow-800">Export Error</h4>
              <p className="mt-1 text-sm text-yellow-700">{exportError.error.user_message}</p>
            </div>
            <button
              onClick={clearExportError}
              className="ml-3 text-yellow-600 hover:text-yellow-800"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {primaryActions.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {primaryActions.map((action, index) => (
              <button
                key={index}
                onClick={action.action}
                className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
              >
                {action.label}
              </button>
            ))}
          </div>
        )}

        {secondaryActions.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {secondaryActions.map((action, index) => (
              <button
                key={index}
                onClick={action.action}
                className="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 text-gray-900 rounded-md transition-colors"
              >
                {action.label}
              </button>
            ))}
          </div>
        )}

        {import.meta.env.DEV && (
          <details className="mt-2">
            <summary className="text-xs text-gray-500 cursor-pointer">Technical Details</summary>
            <div className="mt-1 p-2 bg-gray-100 rounded text-xs text-gray-700 font-mono">
              <div><strong>Code:</strong> {exportError.error.code}</div>
              <div><strong>Technical:</strong> {exportError.error.technical_message}</div>
            </div>
          </details>
        )}
      </div>
    );
  };

  const getSectionStyle = (section?: SourceSection): string => {
    switch (section) {
      case 'overview':
        return 'bg-purple-100 text-purple-800';
      case 'objectives':
        return 'bg-blue-100 text-blue-800';
      case 'materials':
        return 'bg-amber-100 text-amber-800';
      case 'warmup':
        return 'bg-green-100 text-green-800';
      case 'activity':
        return 'bg-emerald-100 text-emerald-800';
      case 'assessment':
        return 'bg-orange-100 text-orange-800';
      case 'differentiation':
        return 'bg-pink-100 text-pink-800';
      case 'closure':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSectionLabel = (section?: SourceSection): string => {
    switch (section) {
      case 'overview':
        return 'Overview';
      case 'objectives':
        return 'Objectives';
      case 'materials':
        return 'Materials';
      case 'warmup':
        return 'Warmup';
      case 'activity':
        return 'Activity';
      case 'assessment':
        return 'Assessment';
      case 'differentiation':
        return 'Differentiation';
      case 'closure':
        return 'Closure';
      default:
        return 'Section';
    }
  };

  // Show loading skeleton while presentation is being generated
  if (!isPresentationReady && isPresentationGenerating) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[90]">
        <div className="w-full max-w-2xl mx-4">
          <DetailedProgressIndicator
            jobId={jobId!}
            isVisible={true}
            onClose={onClose}
            compact={false}
            showDetailedSteps={true}
          />
        </div>
      </div>
    );
  }

  // Show generation skeleton as fallback
  if (!isPresentationReady && showProgress) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[90]">
        <div className="w-full max-w-2xl mx-4">
          <PresentationGenerationSkeleton />
          <div className="mt-4 text-center">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Show error state if generation failed
  if (isPresentationError) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[90]">
        <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-red-100 rounded-full mb-4">
              <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Generation Failed</h3>
            <p className="text-sm text-gray-500 mb-4">
              {presentation.errorMessage || 'An error occurred during presentation generation.'}
            </p>
            <div className="flex flex-col gap-2">
              <button
                onClick={handleRegenerate}
                disabled={isRegenerating}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-md transition-colors"
              >
                {isRegenerating ? 'Starting regeneration...' : 'Try Again'}
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>

        {isRegenerating && regenerationJobId && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-[100]">
            <div className="w-full max-w-2xl mx-4">
              <DetailedProgressIndicator
                jobId={regenerationJobId}
                isVisible={true}
                compact={false}
                showDetailedSteps={true}
              />
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[90]">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 p-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{slideTitle}</h2>
              <p className="text-sm text-gray-500">Lesson #{presentation.lessonId}</p>
            </div>
            <PresentationStatusIndicator status={presentation.status} />
            {currentJobStatus && (
              <div className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                Job #{currentJobStatus.job_id} - {currentJobStatus.progress}%
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {exportProgress && (
              <div className="flex-1 bg-blue-50 border border-blue-200 rounded-md px-3 py-2">
                <div className="flex items-center text-sm text-blue-700">
                  <svg className="animate-spin h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {exportProgress}
                </div>
              </div>
            )}

            {(onExport || apiClient) && isPresentationReady && (
              <>
                <button
                  onClick={() => handleExport('json')}
                  disabled={isExporting || !!exportProgress}
                  className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-md transition-colors"
                >
                  {exportProgress ? 'Processing...' : 'Export JSON'}
                </button>
                <button
                  onClick={() => handleExport('markdown')}
                  disabled={isExporting || !!exportProgress}
                  className="px-3 py-1 text-sm bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white rounded-md transition-colors"
                >
                  {exportProgress ? 'Processing...' : 'Export Markdown'}
                </button>
                <button
                  onClick={() => handleExport('pptx')}
                  disabled={isExporting || !!exportProgress}
                  className="px-3 py-1 text-sm bg-orange-600 hover:bg-orange-700 disabled:bg-orange-300 text-white rounded-md transition-colors"
                >
                  {exportProgress ? 'Processing...' : 'Export PPTX'}
                </button>
                <button
                  onClick={() => handleExport('pdf')}
                  disabled={isExporting || !!exportProgress}
                  className="px-3 py-1 text-sm bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white rounded-md transition-colors"
                >
                  {exportProgress ? 'Processing...' : 'Export PDF'}
                </button>
              </>
            )}
            <button
              onClick={onClose}
              className="px-3 py-1 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
            >
              Close
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex">
          {/* Slide Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {currentSlide && (
              <div className="space-y-4">
                {/* Slide Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-500">
                      Slide {currentSlideIndex + 1} of {totalSlides}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSectionStyle(currentSlide.sourceSection)}`}>
                      {getSectionLabel(currentSlide.sourceSection)}
                    </span>
                    <span className="text-sm text-gray-500">
                      {currentSlide.durationMinutes ? `${currentSlide.durationMinutes} min` : 'Flexible'}
                    </span>
                  </div>
                </div>

                {/* Slide Title */}
                <h3 className="text-2xl font-bold text-gray-900">{currentSlide.title}</h3>

                {/* Slide Content */}
                {currentSlide.subtitle && (
                  <p className="text-lg text-gray-600">{currentSlide.subtitle}</p>
                )}

                <div className="space-y-3">
                  {((currentSlide.keyPoints && currentSlide.keyPoints.length > 0) ||
                    currentSlide.content) && (
                    <ul className="list-disc list-inside text-gray-800 space-y-1">
                      {(currentSlide.keyPoints && currentSlide.keyPoints.length > 0
                        ? currentSlide.keyPoints
                        : currentSlide.content
                        ? [currentSlide.content]
                        : []
                      ).map((point: string, idx: number) => (
                        <li key={idx}>{point}</li>
                      ))}
                    </ul>
                  )}
                  {currentSlide.standardCodes &&
                    currentSlide.standardCodes.length > 0 && (
                      <div className="text-sm text-gray-500">
                        Standards: {currentSlide.standardCodes.join(', ')}
                      </div>
                    )}
                </div>
              </div>
            )}
          </div>

          {/* Teacher Script Sidebar */}
          <div className="w-96 border-l border-gray-200 flex flex-col">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="font-medium text-gray-900">Teacher Script</h3>
              <button
                onClick={() => setShowTeacherScript(!showTeacherScript)}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                {showTeacherScript ? 'Hide' : 'Show'}
              </button>
            </div>
            {showTeacherScript && currentSlide && (
              <div className="flex-1 p-4 overflow-y-auto">
                <div className="bg-yellow-50 rounded-lg p-4">
                  <div className="whitespace-pre-wrap text-sm text-gray-700">
                    {currentSlide.teacherScript || 'No teacher script provided.'}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Error Display */}
        {exportError && (
          <div className="border-b border-gray-200 p-4">
            {getExportErrorMessage()}
          </div>
        )}

        {/* Navigation */}
        <div className="border-t border-gray-200 p-4 flex items-center justify-between">
          <button
            onClick={prevSlide}
            disabled={currentSlideIndex === 0}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-300 text-white rounded-md transition-colors"
          >
            Previous
          </button>

          {/* Slide Navigation Dots */}
          <div className="flex items-center gap-2">
            {presentation.slides.map((_, index) => (
              <button
                key={index}
                onClick={() => goToSlide(index)}
                className={`w-2 h-2 rounded-full transition-colors ${
                  index === currentSlideIndex
                    ? 'bg-blue-600'
                    : 'bg-gray-300 hover:bg-gray-400'
                }`}
              />
            ))}
          </div>

          <button
            onClick={nextSlide}
            disabled={currentSlideIndex === totalSlides - 1}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-300 text-white rounded-md transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

export default EnhancedPresentationViewer;