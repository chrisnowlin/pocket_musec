import React, { useState, useEffect, useRef } from 'react';
import { EnhancedPresentationViewer } from './EnhancedPresentationViewer';
import { ProgressivePresentationViewer } from './ProgressivePresentationViewer';
import { DetailedProgressIndicator } from './DetailedProgressIndicator';
import { ErrorRecoveryStates } from './ErrorRecoveryStates';
import { PresentationGenerationSkeleton } from './SkeletonLoader';
import { progressService } from '../../services/progressService';
import { performanceService } from '../../services/performanceService';
import apiClient from '../../services/presentationApiClient';
import { PresentationError, PresentationErrorCode } from '../../errors/presentationErrors';

interface ProgressSystemIntegrationProps {
  mode: 'generate' | 'view' | 'error';
  jobId?: string | null;
  presentationId?: string | null;
  onPresentationCreated?: (jobId: string) => void;
  onPresentationComplete?: (presentationId: string) => void;
  onBackToGenerate?: () => void;
}

export function ProgressSystemIntegration({
  mode,
  jobId: propJobId,
  presentationId: propPresentationId,
  onPresentationCreated,
  onPresentationComplete,
  onBackToGenerate
}: ProgressSystemIntegrationProps) {
  const [jobId, setJobId] = useState<string | null>(propJobId || null);
  const [presentationId, setPresentationId] = useState<string | null>(propPresentationId || null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showProgress, setShowProgress] = useState(false);
  const [error, setError] = useState<any>(null);
  const [presentationData, setPresentationData] = useState<any>(null);

  // Generate presentation function
  const generatePresentation = async (options = {}) => {
    if (isGenerating) return;

    try {
      setIsGenerating(true);
      setError(null);

      // Start performance monitoring
      performanceService.startTiming('demo_generation');

      // Generate the presentation
      const response = await apiClient.generatePresentation('demo-lesson-123', {
        style: 'default',
        useLlmPolish: true,
        timeoutSeconds: 30,
        ...options
      });

      const newJobId = response.jobId;
      setJobId(newJobId);
      setShowProgress(true);

      // Subscribe to progress updates
      progressService.subscribe({
        jobId: newJobId,
        onProgress: (update) => {
          console.log('Progress update:', update);

          if (update.update_type === 'job_complete' && update.result) {
            // Presentation generation complete
            setPresentationId(update.result.presentationId);
            setIsGenerating(false);
            onPresentationCreated?.(newJobId);
            onPresentationComplete?.(update.result.presentationId);
          }

          if (update.update_type === 'job_error' && update.error) {
            // Handle generation error
            setError(update.error);
            setIsGenerating(false);
          }
        },
        onError: (error) => {
          console.error('Progress tracking error:', error);
          setError(error);
          setIsGenerating(false);
        }
      });

    } catch (error) {
      console.error('Failed to start generation:', error);
      setError(error);
      setIsGenerating(false);
    }
  };

  // Simulate presentation load for view mode
  const loadDemoPresentation = async () => {
    if (!presentationId) return;

    try {
      performanceService.startTiming('demo_load');

      // Simulate API call
      const presentation = await apiClient.getPresentation(presentationId);
      setPresentationData(presentation);

      const metrics = performanceService.endTiming('demo_load');
      console.log('Demo load metrics:', metrics);

    } catch (error) {
      console.error('Failed to load presentation:', error);
      setError(error);
    }
  };

  // Handle retry
  const handleRetry = () => {
    setError(null);
    generatePresentation();
  };

  // Handle error recovery
  const handleErrorRecovery = (action: string) => {
    console.log('Error recovery action:', action);

    switch (action) {
      case 'retry':
        handleRetry();
        break;
      case 'skip_ai':
        generatePresentation({ use_llm_polish: false });
        break;
      case 'contact_support':
        window.open('mailto:support@pocketmusec.com', '_blank');
        break;
      default:
        console.log('Unknown recovery action:', action);
    }
  };

  // Load demo data when entering view mode
  useEffect(() => {
    if (mode === 'view' && presentationId && !presentationData) {
      loadDemoPresentation();
    }
  }, [mode, presentationId, presentationData]);

  // Render based on mode
  switch (mode) {
    case 'generate':
      return (
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Interactive Presentation Generation Demo
            </h2>
            <p className="text-gray-600 mb-6">
              Start generating a presentation to see the comprehensive progress tracking system in action.
            </p>
          </div>

          {/* Controls */}
          <div className="flex flex-col items-center gap-4">
            <div className="flex gap-4">
              <button
                onClick={() => generatePresentation()}
                disabled={isGenerating}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-md transition-colors font-medium"
              >
                {isGenerating ? 'Generation in Progress...' : 'Start Generation'}
              </button>

              {isGenerating && (
                <button
                  onClick={() => {
                    progressService.unsubscribe(jobId!);
                    setIsGenerating(false);
                    setShowProgress(false);
                  }}
                  className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors font-medium"
                >
                  Cancel
                </button>
              )}
            </div>

            <div className="text-sm text-gray-500">
              Try different generation options:
              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => generatePresentation({ use_llm_polish: true })}
                  disabled={isGenerating}
                  className="px-3 py-1 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 text-gray-700 rounded text-sm"
                >
                  With AI Polish
                </button>
                <button
                  onClick={() => generatePresentation({ use_llm_polish: false })}
                  disabled={isGenerating}
                  className="px-3 py-1 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 text-gray-700 rounded text-sm"
                >
                  Without AI Polish
                </button>
                <button
                  onClick={() => generatePresentation({ timeout_seconds: 10 })}
                  disabled={isGenerating}
                  className="px-3 py-1 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 text-gray-700 rounded text-sm"
                >
                  Fast Mode (10s)
                </button>
              </div>
            </div>
          </div>

          {/* Progress Display */}
          {isGenerating && jobId && (
            <div className="max-w-2xl mx-auto">
              <DetailedProgressIndicator
                jobId={jobId}
                isVisible={true}
                onClose={() => {
                  setIsGenerating(false);
                  setShowProgress(false);
                }}
                className="mb-4"
                showDetailedSteps={true}
                compact={false}
              />
            </div>
          )}

          {/* Skeleton Loader Demo */}
          {isGenerating && !jobId && (
            <div className="max-w-2xl mx-auto">
              <PresentationGenerationSkeleton />
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="max-w-2xl mx-auto">
              <ErrorRecoveryStates
                error={error}
                onRetry={handleRetry}
                onContactSupport={() => handleErrorRecovery('contact_support')}
                className="mb-4"
              />
            </div>
          )}

          {/* Success Message */}
          {!isGenerating && presentationId && (
            <div className="max-w-2xl mx-auto">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                <h3 className="text-lg font-medium text-green-800 mb-2">
                  🎉 Presentation Generated Successfully!
                </h3>
                <p className="text-sm text-green-700 mb-4">
                  Job ID: {jobId} | Presentation ID: {presentationId}
                </p>
                <div className="flex gap-2 justify-center">
                  <button
                    onClick={() => {
                      mode = 'view'; // This would be handled by parent
                    }}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
                  >
                    View Presentation
                  </button>
                  <button
                    onClick={onBackToGenerate}
                    className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
                  >
                    Generate Another
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      );

    case 'view':
      return (
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Enhanced Presentation Viewer Demo
            </h2>
            <p className="text-gray-600 mb-6">
              Experience the progressive loading and interactive features of the presentation viewer.
            </p>
          </div>

          {presentationId && (
            <div className="flex justify-center">
              <button
                onClick={() => {
                  // Open the enhanced viewer
                  const viewer: any = document.createElement('div');
                  // This would typically open the actual viewer component
                  console.log('Opening enhanced viewer for presentation:', presentationId);
                }}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors font-medium"
              >
                Open Enhanced Viewer
              </button>
            </div>
          )}

          {!presentationId && (
            <div className="text-center">
              <p className="text-gray-500 mb-4">
                No presentation available. Please generate a presentation first.
              </p>
              <button
                onClick={onBackToGenerate}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
              >
                Back to Generation
              </button>
            </div>
          )}
        </div>
      );

    case 'error':
      // Create demo error object
      const demoError: PresentationError = {
        error: {
          code: PresentationErrorCode.SERVICE_UNAVAILABLE,
          user_message: 'Demo: AI service is temporarily unavailable',
          technical_message: 'This is a simulated error to demonstrate error recovery',
          retry_recommended: true,
          retry_after_seconds: 30,
          escalation_required: false
        },
        timestamp: new Date().toISOString(),
        recovery: {
          retry_recommended: true,
          retry_after_seconds: 30,
          actions: ['retry', 'skip_ai', 'contact_support']
        }
      };

      return (
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Error Recovery System Demo
            </h2>
            <p className="text-gray-600 mb-6">
              Experience comprehensive error handling and recovery options.
            </p>
          </div>

          <div className="max-w-2xl mx-auto">
            <ErrorRecoveryStates
              error={demoError}
              onRetry={handleRetry}
              onContactSupport={() => handleErrorRecovery('contact_support')}
              onAlternativeAction={() => handleErrorRecovery('skip_ai')}
              showDetails={true}
              className="mb-4"
            />

            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-2">Error Recovery Features Demonstrated:</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Contextual error messages with clear user guidance</li>
                <li>• Recommended recovery actions based on error type</li>
                <li>• Automatic retry with exponential backoff</li>
                <li>• Fallback options (skip AI, alternative formats, etc.)</li>
                <li>• Support contact integration</li>
                <li>• Technical details for debugging</li>
              </ul>
            </div>
          </div>
        </div>
      );

    default:
      return (
        <div className="text-center">
          <p className="text-gray-500">Invalid demo mode</p>
        </div>
      );
  }
}

export default ProgressSystemIntegration;
