import React, { useState, useEffect } from 'react';
import { exportProgressService, BulkExportProgress, ExportProgressUpdate } from '../../services/exportProgressService';

interface BulkExportProgressIndicatorProps {
  bulkExportId: string;
  className?: string;
  showFormatDetails?: boolean;
  onBulkExportComplete?: (progress: BulkExportProgress) => void;
  onBulkExportError?: (error: Error) => void;
  onDownloadReady?: (bulkExportId: string) => void;
}

export const BulkExportProgressIndicator: React.FC<BulkExportProgressIndicatorProps> = ({
  bulkExportId,
  className = '',
  showFormatDetails = true,
  onBulkExportComplete,
  onBulkExportError,
  onDownloadReady,
}) => {
  const [progress, setProgress] = useState<BulkExportProgress | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Subscribe to bulk progress updates
    const subscription = {
      bulkExportId,
      onProgress: (update: ExportProgressUpdate) => {
        if (update.bulk_progress) {
          setProgress(update.bulk_progress);
          setError(null);

          if (update.bulk_progress.status === 'completed') {
            onBulkExportComplete?.(update.bulk_progress);
            onDownloadReady?.(bulkExportId);
          }
        }
      },
      onError: (err: Error) => {
        setError(err.message);
        onBulkExportError?.(err);
      },
      onConnectionChange: (connected: boolean) => {
        setIsConnected(connected);
      },
    };

    exportProgressService.subscribeToExportProgress(subscription)
      .catch((err) => {
        console.error('Failed to subscribe to bulk export progress:', err);
        setError(err.message);
      });

    return () => {
      exportProgressService.unsubscribeFromProgress(undefined, bulkExportId);
    };
  }, [bulkExportId, onBulkExportComplete, onBulkExportError, onDownloadReady]);

  if (!progress) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
          <span className="text-sm text-gray-600">Initializing bulk export...</span>
        </div>
      </div>
    );
  }

  const progressColor = exportProgressService.getStatusColor(progress.status);
  const isCompleted = progress.status === 'completed';
  const isFailed = progress.status === 'failed';
  const isRunning = progress.status === 'running';

  const formatSummary = {
    total: progress.formats.length,
    successful: progress.successful_exports.length,
    failed: progress.failed_exports.length,
    cancelled: progress.cancelled_exports.length,
    running: Object.values(progress.export_progress).filter(
      f => f.status === 'running'
    ).length,
    pending: Object.values(progress.export_progress).filter(
      f => f.status === 'pending'
    ).length,
  };

  return (
    <div className={`bg-white border border-gray-200 rounded-lg overflow-hidden ${className}`}>
      {/* Header */}
      <div className={`px-4 py-3 flex items-center justify-between ${progressColor} bg-opacity-10`}>
        <div className="flex items-center space-x-3">
          <span className="text-lg">📦</span>
          <div>
            <h3 className="font-semibold text-gray-900">
              Bulk Export ({progress.formats.length} formats)
            </h3>
            <p className="text-sm text-gray-600">
              {isCompleted ? 'All exports completed' :
               isFailed ? 'Some exports failed' :
               isRunning ? 'Processing multiple formats' :
               'Preparing exports...'}
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

      {/* Overall Progress Bar */}
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

        {/* Format Summary */}
        <div className="flex items-center justify-between mt-3">
          <div className="flex items-center space-x-6 text-xs">
            <div className="flex items-center space-x-1">
              <span>✅</span>
              <span className="text-green-600">{formatSummary.successful}</span>
            </div>
            <div className="flex items-center space-x-1">
              <span>⏳</span>
              <span className="text-blue-600">{formatSummary.running}</span>
            </div>
            <div className="flex items-center space-x-1">
              <span>⏸️</span>
              <span className="text-gray-600">{formatSummary.pending}</span>
            </div>
            {formatSummary.failed > 0 && (
              <div className="flex items-center space-x-1">
                <span>❌</span>
                <span className="text-red-600">{formatSummary.failed}</span>
              </div>
            )}
            {formatSummary.cancelled > 0 && (
              <div className="flex items-center space-x-1">
                <span>🚫</span>
                <span className="text-yellow-600">{formatSummary.cancelled}</span>
              </div>
            )}
          </div>
          <div className="text-xs text-gray-500">
            {formatSummary.successful}/{formatSummary.total} completed
          </div>
        </div>
      </div>

      {/* Format Details */}
      {showFormatDetails && progress.formats.length > 0 && (
        <div className="px-4 py-3 border-t border-gray-100">
          <h4 className="font-medium text-gray-900 mb-3">Format Exports</h4>
          <div className="space-y-2">
            {progress.formats.map((format) => {
              const formatProgress = progress.export_progress[format];
              const formatIcon = exportProgressService.getExportFormatIcon(format);
              const formatColor = exportProgressService.getFormatColor(format);

              if (!formatProgress) return null;

              return (
                <div key={format} className="flex items-center space-x-3 py-2">
                  <span className="text-lg">{formatIcon}</span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium capitalize">{format}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full text-white ${
                        exportProgressService.getStatusColor(formatProgress.status)
                      }`}>
                        {formatProgress.status}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex-1 mr-3">
                        <div className="w-full bg-gray-200 rounded-full h-1">
                          <div
                            className={`h-full rounded-full transition-all duration-300 ${formatColor}`}
                            style={{ width: `${formatProgress.overall_progress}%` }}
                          />
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        <span>{formatProgress.overall_progress.toFixed(1)}%</span>
                        {formatProgress.file_size_bytes && (
                          <span>{exportProgressService.formatFileSize(formatProgress.file_size_bytes)}</span>
                        )}
                      </div>
                    </div>
                    {formatProgress.current_step && (
                      <p className="text-xs text-gray-500 mt-1">
                        {formatProgress.current_step.name}: {formatProgress.current_step.progress !== undefined ? formatProgress.current_step.message : ''}
                      </p>
                    )}
                    {formatProgress.error_message && (
                      <p className="text-xs text-red-600 mt-1">{formatProgress.error_message}</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Download Section */}
      {isCompleted && progress.download_zip_path && (
        <div className="px-4 py-3 bg-green-50 border-t border-green-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-green-600">🎉</span>
              <div>
                <h4 className="text-sm font-medium text-green-900">Bulk Export Complete!</h4>
                <p className="text-xs text-green-700">
                  {formatSummary.successful} formats ready for download
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {/* Download individual formats */}
              {progress.successful_exports.map((format) => {
                const formatProgress = progress.export_progress[format];
                if (!formatProgress || !formatProgress.filename) return null;

                return (
                  <button
                    key={format}
                    onClick={() => exportProgressService.downloadExportedFile(formatProgress.export_id)}
                    className="px-2 py-1 text-xs bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
                  >
                    {format.toUpperCase()}
                  </button>
                );
              })}
              {/* Download ZIP */}
              <button
                onClick={() => exportProgressService.downloadBulkExportZip(bulkExportId)}
                className="px-3 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors flex items-center space-x-1"
              >
                <span>📦</span>
                <span>Download ZIP</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error Section */}
      {error && (
        <div className="px-4 py-3 bg-red-50 border-t border-red-100">
          <div className="flex items-start space-x-3">
            <span>⚠️</span>
            <div className="flex-1">
              <h4 className="font-medium text-red-900">Bulk Export Error</h4>
              <p className="text-sm text-red-700">{error}</p>
              {formatSummary.failed > 0 && (
                <p className="text-xs text-red-600 mt-1">
                  {formatSummary.failed} format(s) failed to export
                </p>
              )}
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
              onClick={() => exportProgressService.cancelBulkExport(bulkExportId)}
              className="px-3 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
            >
              Cancel All
            </button>
          )}
          {isFailed && (
            <button
              className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
            >
              Retry Failed
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default BulkExportProgressIndicator;