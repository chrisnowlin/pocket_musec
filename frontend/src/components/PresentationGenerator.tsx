import React, { useState, useCallback } from 'react';
import PresentationErrorBoundary from './PresentationErrorBoundary';
import { usePresentationErrorHandler, PresentationError } from '../errors/presentationErrors';
import apiClient from '../services/presentationApiClient';
import type { PresentationPreview } from '../types/unified';

interface Lesson {
  id: string;
  title: string;
  content: string;
}

interface PresentationGeneratorProps {
  lesson: Lesson;
  onPresentationGenerated?: (presentationId: string) => void;
}

const PresentationGenerator: React.FC<PresentationGeneratorProps> = ({
  lesson,
  onPresentationGenerated
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState<string>('');
  const [generatedPresentation, setGeneratedPresentation] = useState<any>(null);
  const [previewData, setPreviewData] = useState<PresentationPreview | null>(null);
  const [error, setError] = useState<PresentationError | null>(null);

  const { handleError, getRecoveryActions, scheduleRetry } = usePresentationErrorHandler();

  const handleGeneratePresentation = useCallback(async (options: {
    style?: string;
    useLlmPolish?: boolean;
    timeoutSeconds?: number;
  } = {}) => {
    try {
      setIsGenerating(true);
      setError(null);
      setGenerationProgress('Starting presentation generation...');

      // Step 1: Start generation job
      setGenerationProgress('Creating generation job...');
      const generationResult = await apiClient.generatePresentation(lesson.id, options);

      setGenerationProgress(`Job started: ${generationResult.message}`);

      if (generationResult.accepted) {
        // Step 2: Poll job status
        const pollResult = await apiClient.pollJobStatus(generationResult.jobId, {
          onProgress: (status, attempt) => {
            const statusMessages: Record<string, string> = {
              'pending': 'Waiting to start...',
              'running': `Generating presentation (attempt ${attempt})...`,
              'completed': 'Finalizing presentation...',
            };

            setGenerationProgress(statusMessages[status.status] || `Processing... (attempt ${attempt})`);
          }
        });

        if (pollResult.success) {
          setGenerationProgress('Presentation generated successfully!');
          setGeneratedPresentation(pollResult.status.presentationId);

          if (onPresentationGenerated) {
            onPresentationGenerated(pollResult.status.presentationId);
          }

          // Clear progress after 3 seconds
          setTimeout(() => setGenerationProgress(''), 3000);
        }
      }

    } catch (error: any) {
      console.error('Presentation generation failed:', error);

      const structuredError = error.structuredError || handleError(error, {
        lessonId: lesson.id,
        operation: 'generate_presentation'
      });

      setError(structuredError);
      setGenerationProgress('');

    } finally {
      setIsGenerating(false);
    }
  }, [lesson.id, onPresentationGenerated, handleError]);

  const handleRetryWithFallback = useCallback(async () => {
    if (!error) return;

    // Try regenerating without AI polishing if it was an LLM error
    if (error.error.code.includes('llm_')) {
      setGenerationProgress('Retrying without AI polishing...');
      await handleGeneratePresentation({
        useLlmPolish: false,
        style: 'default',
        timeoutSeconds: 15 // Shorter timeout for scaffold-only
      });
    } else {
      // General retry
      setGenerationProgress('Retrying generation...');
      await handleGeneratePresentation();
    }
  }, [error, handleGeneratePresentation]);

  const clearError = useCallback(() => {
    setError(null);
    setGenerationProgress('');
  }, []);

  const recoveryActions = error ? getRecoveryActions(error) : [];

  if (generatedPresentation) {
    return (
      <div className="p-6 bg-green-50 border border-green-200 rounded-lg">
        <div className="flex items-center">
          <svg className="h-5 w-5 text-green-500 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <div>
            <h3 className="text-green-800 font-medium">Presentation Generated Successfully!</h3>
            <p className="text-green-600 text-sm mt-1">
              Your presentation for "{lesson.title}" is ready to view.
            </p>
          </div>
        </div>

        <div className="mt-4 flex gap-2">
          <button
            onClick={() => window.location.href = `/presentations/${generatedPresentation}`}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm font-medium"
          >
            View Presentation
          </button>
          <button
            onClick={() => {
              setGeneratedPresentation(null);
              clearError();
            }}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-900 rounded-md text-sm font-medium"
          >
            Generate Another
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white border border-gray-200 rounded-lg">
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Generate Presentation
          </h3>
          <p className="text-sm text-gray-600">
            Create an engaging presentation from "{lesson.title}"
          </p>
        </div>

        {/* Generation Options */}
        <div className="space-y-3">
          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                defaultChecked={true}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                disabled={isGenerating}
              />
              <span className="ml-2 text-sm text-gray-700">
                Use AI polishing
              </span>
            </label>
          </div>

          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <span className="text-sm text-gray-700 mr-2">Timeout:</span>
              <select
                className="rounded border-gray-300 text-sm focus:ring-blue-500 focus:border-blue-500"
                disabled={isGenerating}
                defaultValue="30"
              >
                <option value="15">15 seconds</option>
                <option value="30">30 seconds</option>
                <option value="60">60 seconds</option>
              </select>
            </label>
          </div>
        </div>

        {/* Progress Display */}
        {generationProgress && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <div className="flex items-center">
              <svg className="animate-spin h-4 w-4 text-blue-600 mr-2" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="text-sm text-blue-700">{generationProgress}</span>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex items-start">
              <svg className="h-5 w-5 text-red-400 mt-0.5 mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex-1">
                <h4 className="text-sm font-medium text-red-800">Generation Error</h4>
                <p className="mt-1 text-sm text-red-700">{error.error.user_message}</p>

                {recoveryActions.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {recoveryActions.map((action, index) => (
                      <button
                        key={index}
                        onClick={action.action}
                        className={`px-3 py-1 text-sm rounded-md transition-colors ${
                          action.type === 'primary'
                            ? 'bg-blue-600 hover:bg-blue-700 text-white'
                            : action.type === 'danger'
                            ? 'bg-red-600 hover:bg-red-700 text-white'
                            : 'bg-gray-200 hover:bg-gray-300 text-gray-900'
                        }`}
                      >
                        {action.label}
                      </button>
                    ))}
                  </div>
                )}

                <button
                  onClick={clearError}
                  className="mt-3 text-sm text-red-600 hover:text-red-800"
                >
                  Dismiss error
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={() => handleGeneratePresentation()}
            disabled={isGenerating || !!generationProgress}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-md text-sm font-medium transition-colors"
          >
            {isGenerating ? 'Generating...' : 'Generate Presentation'}
          </button>

          {error?.error.code.includes('llm_') && (
            <button
              onClick={handleRetryWithFallback}
              disabled={isGenerating || !!generationProgress}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-300 text-white rounded-md text-sm font-medium transition-colors"
            >
              Try Without AI
            </button>
          )}
        </div>

        {/* Development Details */}
        {import.meta.env.DEV && error && (
          <details className="mt-4">
            <summary className="text-xs text-gray-500 cursor-pointer">Debug Details</summary>
            <div className="mt-2 p-2 bg-gray-100 rounded text-xs text-gray-700 font-mono">
              <div><strong>Error Code:</strong> {error.error.code}</div>
              <div><strong>Technical:</strong> {error.error.technical_message}</div>
              <div><strong>Timestamp:</strong> {error.timestamp}</div>
              <div><strong>Retry Recommended:</strong> {error.error.retry_recommended ? 'Yes' : 'No'}</div>
              {error.error.retry_after_seconds && (
                <div><strong>Retry After:</strong> {error.error.retry_after_seconds}s</div>
              )}
            </div>
          </details>
        )}
      </div>
    </div>
  );
};

/**
 * Wrapped component with error boundary
 */
const PresentationGeneratorWithErrorBoundary: React.FC<PresentationGeneratorProps> = (props) => {
  const handleError = (error: PresentationError) => {
    console.error('Presentation generator encountered an error:', error);
    // Could send to monitoring service here
  };

  return (
    <PresentationErrorBoundary
      onError={handleError}
      fallback={(error, resetError) => (
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
          <div className="text-center">
            <svg className="mx-auto h-12 w-12 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-red-800">
              Presentation Generator Failed
            </h3>
            <p className="mt-2 text-sm text-red-600">
              {error.error.user_message}
            </p>

            <div className="mt-4">
              <button
                onClick={resetError}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md text-sm font-medium"
              >
                Try Again
              </button>
            </div>

            {import.meta.env.DEV && (
              <details className="mt-4 text-left">
                <summary className="text-xs text-red-500 cursor-pointer">Technical Details</summary>
                <div className="mt-2 p-2 bg-red-100 rounded text-xs text-red-700 font-mono">
                  <div><strong>Code:</strong> {error.error.code}</div>
                  <div><strong>Technical:</strong> {error.error.technical_message}</div>
                  <div><strong>Timestamp:</strong> {error.timestamp}</div>
                </div>
              </details>
            )}
          </div>
        </div>
      )}
    >
      <PresentationGenerator {...props} />
    </PresentationErrorBoundary>
  );
};

export default PresentationGeneratorWithErrorBoundary;
