import React, { useState, useEffect } from 'react';
import { exportProgressService, ExportFormatProgress, ExportProgressUpdate } from '../../services/exportProgressService';

interface ExportProgressIndicatorProps {
  exportId: string;
  className?: string;
  showSteps?: boolean;
  onExportComplete?: (progress: ExportFormatProgress) => void;
  onExportError?: (error: Error) => void;
  onDownloadReady?: (exportId: string) => void;
}

export const ExportProgressIndicator: React.FC<ExportProgressIndicatorProps> = ({
  exportId,
  className = '',
  showSteps = false,
  onExportComplete,
  onExportError,
  onDownloadReady,
}) => {
  const [progress, setProgress] = useState<ExportFormatProgress | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Subscribe to progress updates
    const subscription = {
      exportId,
      onProgress: (update: ExportProgressUpdate) => {
        if (update.format_progress) {
          setProgress(update.format_progress);
          setError(null);

          if (update.format_progress.status === 'completed') {
            onExportComplete?.(update.format_progress);
            onDownloadReady?.(exportId);
          }
        }
      },
      onError: (err: Error) => {
        setError(err.message);
        onExportError?.(err);
      },
      onConnectionChange: (connected: boolean) => {
        setIsConnected(connected);
      },
    };

    exportProgressService.subscribeToExportProgress(subscription)
      .catch((err) => {
        console.error('Failed to subscribe to export progress:', err);
        setError(err.message);
      });

    return () => {
      exportProgressService.unsubscribeFromProgress(exportId);
    };
  }, [exportId, onExportComplete, onExportError, onDownloadReady]);

  if (!progress) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
          <span className="text-sm text-gray-600">Initializing export...</span>
        </div>
      </div>
    );
  }

  const progressColor = exportProgressService.getStatusColor(progress.status);
  const formatIcon = exportProgressService.getExportFormatIcon(progress.format);
  const isCompleted = progress.status === 'completed';
  const isFailed = progress.status === 'failed';
  const isRunning = progress.status === 'running';

  return (
    <div className={`bg-white border border-gray-200 rounded-lg overflow-hidden ${className}`}>
      {/* Header */}
      <div className={`px-4 py-3 flex items-center justify-between ${progressColor} bg-opacity-10`}>
        <div className="flex items-center space-x-3">
          <span className="text-lg">{formatIcon}</span>
          <div>
            <h3 className="font-semibold text-gray-900">
              {progress.format.toUpperCase()} Export
            </h3>
            <p className="text-sm text-gray-600">
              {progress.status === 'completed' ? 'Ready to download' :
               progress.status === 'failed' ? 'Export failed' :
               progress.status === 'running' ? 'Processing...' :
               'Preparing...'}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {isConnected ? (
            <div className="flex items-center space-x-1 text-green-600">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs">Live</span>
            </div>
          ) : (
            <div className="flex items-center space-x-1 text-gray-500">
              <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
              <span className="text-xs">Polling</span>
            </div>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">
            Overall Progress
          </span>
          <span className="text-sm text-gray-500">
            {progress.overall_progress.toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              progress.status === 'failed' ? 'bg-red-500' :
              progress.status === 'completed' ? 'bg-green-500' :
              progressColor
            }`}
            style={{ width: `${progress.overall_progress}%` }}
          />
        </div>

        {/* Time and Size Info */}
        <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
          <div className="flex items-center space-x-4">
            {progress.estimated_time_remaining && isRunning && (
              <span>⏱️ {exportProgressService.formatTimeRemaining(progress.estimated_time_remaining)}</span>
            )}
            {progress.file_size_bytes && (
              <span>📁 {exportProgressService.formatFileSize(progress.file_size_bytes)}</span>
            )}
          </div>
          {progress.retry_count > 0 && (
            <span className="text-yellow-600">
              Retry {progress.retry_count}/{progress.max_retries}
            </span>
          )}
        </div>
      </div>

      {/* Current Step Info */}
      {progress.current_step && showSteps && (
        <div className="px-4 py-3 border-t border-gray-100">
          <div className="flex items-start space-x-3">
            <span className="mt-0.5">
              {exportProgressService.getStepIcon(progress.current_step.step)}
            </span>
            <div className="flex-1">
              <h4 className="font-medium text-gray-900">{progress.current_step.name}</h4>
              <p className="text-sm text-gray-600">{progress.current_step.description}</p>
              {progress.current_step.message && (
                <p className="text-xs text-blue-600 mt-1">{progress.current_step.message}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Steps List (Optional) */}
      {showSteps && progress.steps.length > 0 && (
        <div className="px-4 py-3 border-t border-gray-100">
          <h4 className="font-medium text-gray-900 mb-3">Export Steps</h4>
          <div className="space-y-2">
            {progress.steps.slice(0, 5).map((step, index) => {
              const isStepActive = progress.current_step?.step === step.step;
              const isStepCompleted = step.status === 'completed' || step.status === 'skipped';
              const isStepFailed = step.status === 'failed';

              return (
                <div key={step.step} className="flex items-center space-x-3 py-2">
                  <span className="text-sm">
                    {isStepFailed ? '❌' :
                     isStepCompleted ? '✅' :
                     isStepActive ? '⏳' : '⏸️'}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className={`text-sm truncate ${
                        isStepActive ? 'font-medium' : 'text-gray-600'
                      }`}>
                        {step.name}
                      </span>
                      {isStepActive && (
                        <span className="text-xs text-blue-600">
                          {step.progress.toFixed(0)}%
                        </span>
                      )}
                    </div>
                    {isStepActive && (
                      <div className="w-full bg-gray-200 rounded-full h-1 mt-1">
                        <div
                          className="h-full bg-blue-500 rounded-full transition-all duration-300"
                          style={{ width: `${step.progress}%` }}
                        />
                      </div>
                    )}
                    {step.error_message && isStepFailed && (
                      <p className="text-xs text-red-600 mt-1">{step.error_message}</p>
                    )}
                  </div>
                </div>
              );
            })}
            {progress.steps.length > 5 && (
              <div className="text-xs text-gray-500 pt-2">
                +{progress.steps.length - 5} more steps
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error Section */}
      {error && (
        <div className="px-4 py-3 bg-red-50 border-t border-red-100">
          <div className="flex items-start space-x-3">
            <span>⚠️</span>
            <div className="flex-1">
              <h4 className="font-medium text-red-900">Export Error</h4>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
        <div className="text-xs text-gray-500">
          Created: {new Date(progress.created_at).toLocaleString()}
        </div>
        <div className="flex items-center space-x-2">
          {isRunning && (
            <button
              onClick={() => exportProgressService.cancelExport(exportId)}
              className="px-3 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
            >
              Cancel Export
            </button>
          )}
          {isFailed && progress.retry_count < progress.max_retries && (
            <button
              onClick={() => exportProgressService.retryExport(exportId)}
              className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
            >
              Retry Export
            </button>
          )}
          {isCompleted && (
            <button
              onClick={() => exportProgressService.downloadExportedFile(exportId)}
              className="px-3 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors flex items-center space-x-1"
            >
              <span>📥</span>
              <span>Download</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExportProgressIndicator;