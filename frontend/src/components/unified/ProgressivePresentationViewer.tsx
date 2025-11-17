import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { performanceService, usePerformanceOptimizations } from '../../services/performanceService';
import { progressService, DetailedProgress, ProgressUpdate } from '../../services/progressService';
import { ErrorRecoveryStates } from './ErrorRecoveryStates';
import { DetailedProgressIndicator } from './DetailedProgressIndicator';
import { LoadingOverlay } from './SkeletonLoader';
import type { PresentationDetail, SourceSection } from '../../types/presentations';
import { PresentationError, PresentationErrorCode } from '../../errors/presentationErrors';

interface ProgressivePresentationViewerProps {
  presentationId: string;
  initialJobId?: string; // Optional job ID if presentation is being generated
  isOpen: boolean;
  onClose: () => void;
  onExport?: (format: 'json' | 'markdown' | 'pptx' | 'pdf') => void;
  onError?: (error: PresentationError) => void;
  enableProgressiveLoading?: boolean;
  performanceMonitoring?: boolean;
}

interface ViewerState {
  phase: 'generating' | 'loading' | 'viewing' | 'error';
  presentation: PresentationDetail | null;
  currentSlideIndex: number;
  loadedSlides: number;
  totalSlides: number;
  loadingProgress: number;
  error: PresentationError | null;
  showTeacherScript: boolean;
  isExporting: boolean;
  exportProgress: string | null;
  progressData: DetailedProgress | null;
}

export function ProgressivePresentationViewer({
  presentationId,
  initialJobId,
  isOpen,
  onClose,
  onExport,
  onError,
  enableProgressiveLoading = true,
  performanceMonitoring = import.meta.env.DEV
}: ProgressivePresentationViewerProps) {
  const { performanceService, debounce, throttle, loadPresentationProgressively } = usePerformanceOptimizations();
  const viewerRef = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<ViewerState>({
    phase: initialJobId ? 'generating' : 'loading',
    presentation: null,
    currentSlideIndex: 0,
    loadedSlides: 0,
    totalSlides: 0,
    loadingProgress: 0,
    error: null,
    showTeacherScript: true,
    isExporting: false,
    exportProgress: null,
    progressData: null
  });

  // Load presentation data
  const loadPresentation = useCallback(async () => {
    if (!presentationId) return;

    setState(prev => ({ ...prev, phase: 'loading', error: null }));

    try {
      if (performanceMonitoring) {
        performanceService.startTiming('presentation_load');
      }

      const presentation = enableProgressiveLoading
        ? await loadPresentationProgressively(
            presentationId,
            (progress, loaded, total) => {
              setState(prev => ({
                ...prev,
                loadingProgress: progress,
                loadedSlides: loaded,
                totalSlides: total
              }));
            }
          )
        : await performanceService.fetchWithRetry(`/api/presentations/${presentationId}`);

      if (performanceMonitoring) {
        const metrics = performanceService.endTiming('presentation_load');
        console.log('Presentation loading metrics:', metrics);
      }

      setState(prev => ({
        ...prev,
        phase: 'viewing',
        presentation,
        totalSlides: presentation.slides.length,
        loadedSlides: presentation.slides.length,
        loadingProgress: 100
      }));

    } catch (error) {
      console.error('Failed to load presentation:', error);
      const presentationError: PresentationError = {
        error: {
          code: PresentationErrorCode.INTERNAL_ERROR,
          user_message: 'Failed to load presentation',
          technical_message: (error as Error).message || 'Unknown error',
          retry_recommended: true,
          escalation_required: false
        },
        timestamp: new Date().toISOString(),
        recovery: {
          retry_recommended: true,
          actions: ['Retry loading presentation']
        }
      };

      setState(prev => ({
        ...prev,
        phase: 'error',
        error: presentationError
      }));

      onError?.(presentationError);
    }
  }, [presentationId, enableProgressiveLoading, performanceMonitoring, performanceService, loadPresentationProgressively, onError]);

  // Handle job progress updates
  const handleJobProgress = useCallback((update: ProgressUpdate) => {
    if (update.progress) {
      setState(prev => ({
        ...prev,
        progressData: update.progress || null
      }));
    }

    // Handle completion
    if (update.update_type === 'job_complete') {
      // Start loading the presentation
      loadPresentation();
    }

    // Handle errors
    if (update.update_type === 'job_error' && update.error) {
      const presentationError: PresentationError = {
        error: update.error,
        timestamp: new Date().toISOString(),
        recovery: {
          retry_recommended: update.error.retry_recommended,
          actions: ['Retry operation']
        }
      };

      setState(prev => ({
        ...prev,
        phase: 'error',
        error: presentationError
      }));
    }
  }, [loadPresentation]);

  // Subscribe to job progress if jobId provided
  useEffect(() => {
    if (!initialJobId || !isOpen) return;

    const subscription = {
      jobId: initialJobId,
      onProgress: handleJobProgress,
      onError: (error: Error) => {
        console.error('Job progress error:', error);
        const presentationError: PresentationError = {
          error: {
            code: PresentationErrorCode.JOB_NOT_FOUND,
            user_message: 'Error tracking generation progress',
            technical_message: (error as Error).message || 'Unknown error',
            retry_recommended: true,
            escalation_required: false
          },
          timestamp: new Date().toISOString(),
          recovery: {
            retry_recommended: true,
            actions: ['Retry generation']
          }
        };

        setState(prev => ({
          ...prev,
          phase: 'error',
          error: presentationError
        }));
      }
    };

    progressService.subscribe(subscription);

    return () => {
      progressService.unsubscribe(initialJobId);
    };
  }, [initialJobId, isOpen, handleJobProgress]);

  // Load presentation when opening viewer
  useEffect(() => {
    if (isOpen && !initialJobId && state.phase !== 'loading' && state.phase !== 'viewing') {
      loadPresentation();
    }
  }, [isOpen, initialJobId, state.phase, loadPresentation]);

  // Clean up performance monitoring on close
  useEffect(() => {
    return () => {
      if (performanceMonitoring) {
        performanceService.cleanup();
      }
    };
  }, [performanceMonitoring, performanceService]);

  // Navigation handlers
  const goToSlide = useCallback((index: number) => {
    if (!state.presentation) return;
    const maxIndex = state.presentation.slides.length - 1;
    const clampedIndex = Math.max(0, Math.min(index, maxIndex));
    setState(prev => ({ ...prev, currentSlideIndex: clampedIndex }));
  }, [state.presentation]);

  const nextSlide = useCallback(() => {
    goToSlide(state.currentSlideIndex + 1);
  }, [state.currentSlideIndex, goToSlide]);

  const prevSlide = useCallback(() => {
    goToSlide(state.currentSlideIndex - 1);
  }, [state.currentSlideIndex, goToSlide]);

  // Export handler with progress tracking
  const handleExport = useCallback(async (format: 'json' | 'markdown' | 'pptx' | 'pdf') => {
    if (!state.presentation) return;

    try {
      setState(prev => ({ ...prev, isExporting: true, exportProgress: `Preparing ${format.toUpperCase()} export...` }));

      if (performanceMonitoring) {
        performanceService.startTiming(`export_${format}`);
      }

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setState(prev => {
          if (prev.exportProgress && prev.exportProgress.includes(':')) {
            const currentProgress = parseInt(prev.exportProgress.split(': ')[1]);
            const newProgress = Math.min(100, currentProgress + 10);
            return {
              ...prev,
              exportProgress: `Exporting ${format.toUpperCase()}: ${newProgress}%`
            };
          }
          return prev;
        });
      }, 500);

      // Call the provided export handler
      if (onExport) {
        onExport(format);
      } else {
        // Default export implementation would go here
        console.log(`Exporting ${format}`);
      }

      clearInterval(progressInterval);

      if (performanceMonitoring) {
        const metrics = performanceService.endTiming(`export_${format}`);
        console.log(`${format} export metrics:`, metrics);
      }

      setState(prev => ({
        ...prev,
        exportProgress: `${format.toUpperCase()} export completed successfully`,
        isExporting: false
      }));

      // Clear progress message after 3 seconds
      setTimeout(() => {
        setState(prev => ({ ...prev, exportProgress: null }));
      }, 3000);

    } catch (error) {
      console.error('Export failed:', error);
      setState(prev => ({
        ...prev,
        isExporting: false,
        exportProgress: null
      }));

      const presentationError: PresentationError = {
        error: {
          code: PresentationErrorCode.EXPORT_PDF_FAILED,
          user_message: 'Export failed',
          technical_message: (error as Error).message || 'Unknown error',
          retry_recommended: true,
          escalation_required: false
        },
        timestamp: new Date().toISOString(),
        recovery: {
          retry_recommended: true,
          actions: ['Retry export']
        }
      };

      onError?.(presentationError);
    }
  }, [state.presentation, onExport, onError, performanceMonitoring, performanceService]);

  // Memoized current slide
  const currentSlide = useMemo(() => {
    if (!state.presentation || state.presentation.slides.length === 0) return null;
    return state.presentation.slides[state.currentSlideIndex];
  }, [state.presentation, state.currentSlideIndex]);

  // Render based on phase
  if (!isOpen) return null;

  // Generating phase with progress
  if (state.phase === 'generating') {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[90]">
        <div className="w-full max-w-2xl mx-4">
          {state.progressData ? (
            <DetailedProgressIndicator
              jobId={initialJobId!}
              isVisible={true}
              onClose={onClose}
              compact={false}
              showDetailedSteps={true}
            />
          ) : (
            <LoadingOverlay
              isVisible={true}
              message="Starting presentation generation..."
            />
          )}
        </div>
      </div>
    );
  }

  // Loading phase with progress
  if (state.phase === 'loading') {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[90]">
        <LoadingOverlay
          isVisible={true}
          message={`Loading presentation... ${Math.round(state.loadingProgress)}%`}
          showProgress={true}
          progress={state.loadingProgress}
        />
      </div>
    );
  }

  // Error phase
  if (state.phase === 'error' && state.error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[90]">
        <div className="w-full max-w-2xl mx-4">
          <ErrorRecoveryStates
            error={state.error}
            onRetry={loadPresentation}
            onContactSupport={() => window.open('mailto:support@pocketmusec.com', '_blank')}
          />
        </div>
      </div>
    );
  }

  // Viewing phase
  if (state.phase === 'viewing' && state.presentation && currentSlide) {
    const totalSlides = state.presentation.slides.length;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[90]" ref={viewerRef}>
        <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="border-b border-gray-200 p-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {state.presentation.title || 'Lesson Presentation'}
                </h2>
                <p className="text-sm text-gray-500">Lesson #{state.presentation.lessonId}</p>
              </div>
              {state.progressData && (
                <div className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                  {state.progressData.current_message}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              {state.exportProgress && (
                <div className="flex-1 bg-blue-50 border border-blue-200 rounded-md px-3 py-2">
                  <div className="flex items-center text-sm text-blue-700">
                    <svg className="animate-spin h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    {state.exportProgress}
                  </div>
                </div>
              )}

              <div className="flex gap-2">
                {onExport && (
                  <>
                    <button
                      onClick={() => handleExport('json')}
                      disabled={state.isExporting}
                      className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-md transition-colors"
                    >
                      Export JSON
                    </button>
                    <button
                      onClick={() => handleExport('markdown')}
                      disabled={state.isExporting}
                      className="px-3 py-1 text-sm bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white rounded-md transition-colors"
                    >
                      Export Markdown
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
          </div>

          {/* Main Content */}
          <div className="flex-1 flex">
            {/* Slide Content */}
            <div className="flex-1 p-6 overflow-y-auto">
              <div className="space-y-4">
                {/* Slide Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-500">
                      Slide {state.currentSlideIndex + 1} of {totalSlides}
                    </span>
                    {currentSlide.sourceSection && (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSectionStyle(currentSlide.sourceSection)}`}>
                        {getSectionLabel(currentSlide.sourceSection)}
                      </span>
                    )}
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
                      ).map((point, idx) => (
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
            </div>

            {/* Teacher Script Sidebar */}
            <div className="w-96 border-l border-gray-200 flex flex-col">
              <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="font-medium text-gray-900">Teacher Script</h3>
                <button
                  onClick={() => setState(prev => ({ ...prev, showTeacherScript: !prev.showTeacherScript }))}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  {state.showTeacherScript ? 'Hide' : 'Show'}
                </button>
              </div>
              {state.showTeacherScript && (
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

          {/* Navigation */}
          <div className="border-t border-gray-200 p-4 flex items-center justify-between">
            <button
              onClick={prevSlide}
              disabled={state.currentSlideIndex === 0}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-300 text-white rounded-md transition-colors"
            >
              Previous
            </button>

            {/* Slide Navigation Dots */}
            <div className="flex items-center gap-2">
              {state.presentation.slides.map((_, index) => (
                <button
                  key={index}
                  onClick={() => goToSlide(index)}
                  className={`w-2 h-2 rounded-full transition-colors ${
                    index === state.currentSlideIndex
                      ? 'bg-blue-600'
                      : 'bg-gray-300 hover:bg-gray-400'
                  }`}
                />
              ))}
            </div>

            <button
              onClick={nextSlide}
              disabled={state.currentSlideIndex === totalSlides - 1}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-300 text-white rounded-md transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

// Utility functions
function getSectionStyle(section?: SourceSection): string {
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
}

function getSectionLabel(section?: SourceSection): string {
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
}

export default ProgressivePresentationViewer;