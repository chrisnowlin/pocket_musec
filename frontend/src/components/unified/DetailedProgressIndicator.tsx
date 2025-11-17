import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { progressService, DetailedProgress, ProgressUpdate, ProgressSubscription } from '../../services/progressService';

interface DetailedProgressIndicatorProps {
  jobId: string;
  isVisible?: boolean;
  onClose?: () => void;
  onPause?: () => void;
  onResume?: () => void;
  onCancel?: () => void;
  showDetailedSteps?: boolean;
  compact?: boolean;
  className?: string;
}

export function DetailedProgressIndicator({
  jobId,
  isVisible = true,
  onClose,
  onPause,
  onResume,
  onCancel,
  showDetailedSteps = true,
  compact = false,
  className = ''
}: DetailedProgressIndicatorProps) {
  const [progress, setProgress] = useState<DetailedProgress | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isExpanded, setIsExpanded] = useState(!compact);
  const [showTimeDetails, setShowTimeDetails] = useState(false);

  // Subscribe to progress updates
  useEffect(() => {
    if (!isVisible || !jobId) return;

    const subscription: ProgressSubscription = {
      jobId,
      onProgress: (update: ProgressUpdate) => {
        setHasError(false);
        setErrorMessage('');

        if (update.progress) {
          setProgress(update.progress);
        }

        // Handle completion
        if (update.update_type === 'job_complete' && update.result) {
          console.log('Job completed:', update.result);
          // Auto-close after completion if desired
          setTimeout(() => {
            if (onClose) onClose();
          }, 3000);
        }

        // Handle errors
        if (update.update_type === 'job_error' && update.error) {
          setHasError(true);
          setErrorMessage(update.error.message || 'An error occurred');
        }
      },
      onError: (error: Error) => {
        console.error('Progress tracking error:', error);
        setHasError(true);
        setErrorMessage(error.message);
      },
      onConnectionChange: (connected: boolean) => {
        setIsConnected(connected);
      }
    };

    progressService.subscribe(subscription);

    return () => {
      progressService.unsubscribe(jobId);
    };
  }, [jobId, isVisible, onClose]);

  // Format time for display
  const formatTimeDisplay = useCallback((isoString?: string) => {
    if (!isoString) return '';
    return new Date(isoString).toLocaleTimeString();
  }, []);

  // Calculate progress status
  const progressStatus = useMemo(() => {
    if (!progress) return null;
    return progressService.getStepProgressStatus(progress.overall_progress);
  }, [progress]);

  // Get step status color
  const getStepStatusColor = useCallback((status: string, isActive: boolean) => {
    if (status === 'completed' || status === 'skipped') return 'text-green-600 bg-green-50';
    if (status === 'failed') return 'text-red-600 bg-red-50';
    if (status === 'running') return 'text-blue-600 bg-blue-50 animate-pulse';
    if (isActive) return 'text-purple-600 bg-purple-50';
    return 'text-gray-500 bg-gray-50';
  }, []);

  if (!isVisible) return null;

  if (compact && progress) {
    // Compact mode - just show progress bar and basic info
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-3 ${className}`}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="text-sm font-medium">{progressStatus?.text}</div>
            <div className="text-xs text-gray-500">
              {Math.round(progress.overall_progress)}%
            </div>
          </div>
          <div className="text-xs text-gray-400">
            {progressService.formatTimeRemaining(progress.estimated_time_remaining_seconds)}
          </div>
        </div>

        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${progressService.getProgressColor(progress.overall_progress)}`}
            style={{ width: `${progress.overall_progress}%` }}
          />
        </div>

        {hasError && (
          <div className="mt-2 text-xs text-red-600">
            {errorMessage}
          </div>
        )}
      </div>
    );
  }

  // Full detailed mode
  return (
    <div className={`bg-white rounded-lg shadow-lg border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`text-lg ${progressStatus?.color || 'text-gray-600'}`}>
              {progressStatus?.icon || '⏳'}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">
                Generating Presentation
              </h3>
              {progress && (
                <p className="text-sm text-gray-600">
                  {progress.current_message || 'Processing...'}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Connection indicator */}
            <div className={`flex items-center gap-1 text-xs ${
              isConnected ? 'text-green-600' : 'text-yellow-600'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-600' : 'bg-yellow-600 animate-pulse'
              }`} />
              {isConnected ? 'Live' : 'Connecting...'}
            </div>

            {/* Action buttons */}
            {onCancel && (
              <button
                onClick={onCancel}
                className="px-3 py-1 text-sm bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
              >
                Cancel
              </button>
            )}
            {onClose && (
              <button
                onClick={onClose}
                className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Progress Bar Section */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">
            Overall Progress
          </span>
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-gray-900">
              {Math.round(progress?.overall_progress || 0)}%
            </span>
            {progress?.estimated_time_remaining_seconds && (
              <span className="text-sm text-gray-500">
                ~{progressService.formatTimeRemaining(progress.estimated_time_remaining_seconds)}
              </span>
            )}
          </div>
        </div>

        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${progressService.getProgressColor(progress?.overall_progress || 0)}`}
            style={{ width: `${progress?.overall_progress || 0}%` }}
          />
        </div>

        {/* Time estimation details */}
        {progress && (
          <div className="mt-3 flex items-center justify-between">
            <div className="text-xs text-gray-500">
              Started: {formatTimeDisplay(progress.last_updated)}
            </div>
            <button
              onClick={() => setShowTimeDetails(!showTimeDetails)}
              className="text-xs text-blue-600 hover:text-blue-700"
            >
              {showTimeDetails ? 'Hide' : 'Show'} Details
            </button>
          </div>
        )}

        {showTimeDetails && progress && (
          <div className="mt-2 p-2 bg-gray-50 rounded text-xs text-gray-600 space-y-1">
            {progress.estimated_completion_time && (
              <div>Est. completion: {formatTimeDisplay(progress.estimated_completion_time)}</div>
            )}
            <div>Last updated: {formatTimeDisplay(progress.last_updated)}</div>
            {progress.current_step && (
              <div>Current step: {progress.current_step_info?.name}</div>
            )}
          </div>
        )}
      </div>

      {/* Error Display */}
      {hasError && (
        <div className="p-4 bg-red-50 border-b border-gray-200">
          <div className="flex items-start gap-3">
            <div className="text-red-600 mt-0.5">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="flex-1">
              <h4 className="font-medium text-red-800">Generation Error</h4>
              <p className="text-sm text-red-700 mt-1">{errorMessage}</p>
            </div>
          </div>
        </div>
      )}

      {/* Detailed Steps */}
      {showDetailedSteps && progress && (
        <div className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900">Generation Steps</h4>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              {isExpanded ? 'Collapse' : 'Expand'}
            </button>
          </div>

          {isExpanded && (
            <div className="space-y-3">
              {progress.steps.map((step, index) => {
                const isActive = progressService.isStepActive(progress.current_step || '', step.step);
                const isCompleted = progressService.isStepCompleted(step.status);
                const isFailed = progressService.isStepFailed(step.status);

                return (
                  <div
                    key={step.step}
                    className={`flex items-center gap-3 p-3 rounded-lg border ${
                      isActive ? 'border-purple-200 bg-purple-50' : 'border-gray-200'
                    }`}
                  >
                    {/* Step icon and status */}
                    <div className="flex items-center gap-2">
                      <div className="text-lg">
                        {progressService.getStepIcon(step.step)}
                      </div>
                      <div className="text-sm">
                        {progressService.getStepStatusIcon(step.status)}
                      </div>
                    </div>

                    {/* Step details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <div className={`font-medium text-sm ${
                          getStepStatusColor(step.status, isActive).split(' ')[0]
                        }`}>
                          {step.name}
                        </div>
                        {step.status === 'running' && (
                          <div className="text-xs text-blue-600">
                            {Math.round(step.progress)}%
                          </div>
                        )}
                      </div>

                      <div className={`text-xs ${
                        getStepStatusColor(step.status, isActive).split(' ')[0]
                      }`}>
                        {step.description}
                      </div>

                      {step.details.current_message && (
                        <div className="text-xs text-gray-600 mt-1">
                          {step.details.current_message}
                        </div>
                      )}

                      {step.error_message && (
                        <div className="text-xs text-red-600 mt-1">
                          Error: {step.error_message}
                        </div>
                      )}

                      {/* Step progress bar */}
                      {step.status === 'running' && (
                        <div className="mt-2 w-full bg-gray-200 rounded-full h-1">
                          <div
                            className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                            style={{ width: `${step.progress}%` }}
                          />
                        </div>
                      )}
                    </div>

                    {/* Step timing */}
                    {isCompleted && step.actual_duration && (
                      <div className="text-xs text-gray-500 whitespace-nowrap">
                        {Math.round(step.actual_duration)}s
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default DetailedProgressIndicator;