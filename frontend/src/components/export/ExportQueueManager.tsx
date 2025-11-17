import React, { useState, useEffect } from 'react';
import { exportProgressService, ExportFormatProgress, BulkExportProgress } from '../../services/exportProgressService';

interface ExportQueueManagerProps {
  className?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const ExportQueueManager: React.FC<ExportQueueManagerProps> = ({
  className = '',
  autoRefresh = true,
  refreshInterval = 5000, // 5 seconds
}) => {
  const [activeExports, setActiveExports] = useState<ExportFormatProgress[]>([]);
  const [bulkExports, setBulkExports] = useState<BulkExportProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'running' | 'failed' | 'completed'>('all');
  const [sortBy, setSortBy] = useState<'createdAt' | 'status' | 'format'>('createdAt');
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(autoRefresh);

  const loadExports = async () => {
    try {
      setError(null);

      // Load single exports
      const singleExports: ExportFormatProgress[] = [];
      const statusFilter = filter === 'all' ? undefined : filter;

      // Get exports with appropriate status filter
      const loadedExports = await exportProgressService.listActiveExports(statusFilter, 50);
      setActiveExports(loadedExports);

      // Note: In a real implementation, you'd have a method to get bulk exports
      // For now, we'll filter active exports for bulk exports
      const bulkExportIds = loadedExports
        .filter(exp => exp.export_id && exp.export_id.includes('bulk_export'))
        .reduce((acc, exp) => {
          const bulkId = exp.export_id?.replace('_bulk_', '').split('_')[2];
          if (bulkId && !acc.includes(bulkId)) acc.push(bulkId);
          return acc;
        }, [] as string[]);

      // For demo purposes, pretend we have bulk exports
      setBulkExports([]);

    } catch (err: any) {
      console.error('Failed to load exports:', err);
      setError(err.message || 'Failed to load exports');
    }
  };

  const refreshQueue = async () => {
    await loadExports();
  };

  useEffect(() => {
    loadExports();
  }, [filter]);

  useEffect(() => {
    if (autoRefreshEnabled) {
      const interval = setInterval(refreshQueue, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefreshEnabled, refreshInterval]);

  const handleCancelExport = async (exportId: string) => {
    try {
      await exportProgressService.cancelExport(exportId);
      await refreshQueue();
    } catch (err: any) {
      console.error('Failed to cancel export:', err);
      setError(err.message || 'Failed to cancel export');
    }
  };

  const handleRetryExport = async (exportId: string) => {
    try {
      await exportProgressService.retryExport(exportId);
      await refreshQueue();
    } catch (err: any) {
      console.error('Failed to retry export:', err);
      setError(err.message || 'Failed to retry export');
    }
  };

  const handleDownloadExport = async (exportId: string) => {
    try {
      await exportProgressService.downloadExportedFile(exportId);
    } catch (err: any) {
      console.error('Failed to download export:', err);
      setError(err.message || 'Failed to download export');
    }
  };

  const sortedExports = () => {
    return [...activeExports].sort((a, b) => {
      switch (sortBy) {
        case 'createdAt':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'status':
          return a.status.localeCompare(b.status);
        case 'format':
          return a.format.localeCompare(b.format);
        default:
          return 0;
      }
    });
  };

  const filteredAndSortedExports = sortedExports();

  const getQueueStats = () => {
    const running = activeExports.filter(exp => exp.status === 'running').length;
    const pending = activeExports.filter(exp => exp.status === 'pending').length;
    const completed = activeExports.filter(exp => exp.status === 'completed').length;
    const failed = activeExports.filter(exp => exp.status === 'failed').length;
    const total = activeExports.length;

    return { running, pending, completed, failed, total };
  };

  const stats = getQueueStats();

  return (
    <div className={`bg-white border border-gray-200 rounded-lg overflow-hidden ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Export Queue Manager</h2>
            <div className="flex items-center space-x-4 mt-1">
              <span className="text-sm text-gray-500">
                {stats.total} total exports
              </span>
              <div className="flex items-center space-x-3 text-sm">
                <span className="flex items-center space-x-1">
                  <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                  <span>{stats.running} running</span>
                </span>
                <span className="flex items-center space-x-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                  <span>{stats.pending} pending</span>
                </span>
                <span className="flex items-center space-x-1">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span>{stats.completed} completed</span>
                </span>
                <span className="flex items-center space-x-1">
                  <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                  <span>{stats.failed} failed</span>
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setAutoRefreshEnabled(!autoRefreshEnabled)}
              className={`px-3 py-2 text-sm rounded-md transition-colors ${
                autoRefreshEnabled
                  ? 'bg-green-100 text-green-700 hover:bg-green-200'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {autoRefreshEnabled ? '🔄 Auto-Refresh On' : '⏸️ Auto-Refresh Off'}
            </button>
            <button
              onClick={refreshQueue}
              disabled={loading}
              className={`px-3 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors flex items-center space-x-1 ${
                loading ? 'opacity-50' : ''
              }`}
            >
              <span>{loading ? '🔄' : '🔃'}</span>
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </div>

      {/* Filters and Controls */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Filter:</label>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as any)}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Exports</option>
                <option value="running">Running</option>
                <option value="failed">Failed</option>
                <option value="completed">Completed</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Sort by:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="createdAt">Created Time</option>
                <option value="status">Status</option>
                <option value="format">Format</option>
              </select>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => exportProgressService.cancelExport('all-temp')}
              className="px-3 py-1 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded-md transition-colors"
            >
              Cancel All
            </button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="px-6 py-4 bg-red-50 border-b border-red-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span>❌</span>
              <span className="text-sm text-red-700">{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Export List */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Export Details
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status & Progress
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                File Info
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Timing
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredAndSortedExports.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                  <div className="flex flex-col items-center space-y-2">
                    <span className="text-2xl">📭</span>
                    <span>No exports found</span>
                  </div>
                </td>
              </tr>
            ) : (
              filteredAndSortedExports.map((exportItem) => (
                <tr key={exportItem.export_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-3">
                      <span className="text-lg">
                        {exportProgressService.getExportFormatIcon(exportItem.format)}
                      </span>
                      <div>
                        <div className="text-sm font-medium text-gray-900 capitalize">
                          {exportItem.format} Export
                        </div>
                        <div className="text-xs text-gray-500">
                          ID: {exportItem.export_id.slice(0, 12)}...
                        </div>
                      </div>
                    </div>
                  </td>

                  <td className="px-6 py-4">
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs px-2 py-1 rounded-full text-white ${
                          exportProgressService.getStatusColor(exportItem.status)
                        }`}>
                          {exportItem.status}
                        </span>
                        {exportItem.retry_count > 0 && (
                          <span className="text-xs text-yellow-600">
                            Retry {exportItem.retry_count}/{exportItem.max_retries}
                          </span>
                        )}
                      </div>

                      {exportItem.status === 'running' && (
                        <div className="w-32 bg-gray-200 rounded-full h-1.5">
                          <div
                            className={`h-full rounded-full ${
                              exportProgressService.getStatusColor(exportItem.status)
                            }`}
                            style={{ width: `${exportItem.overall_progress}%` }}
                          />
                        </div>
                      )}

                      {exportItem.current_step && (
                        <div className="text-xs text-gray-500">
                          {exportProgressService.getStepIcon(exportItem.current_step.step)}{' '}
                          {exportItem.current_step.name}
                        </div>
                      )}

                      {exportItem.error_message && (
                        <div className="text-xs text-red-600 truncate max-w-xs" title={exportItem.error_message}>
                          ⚠️ {exportItem.error_message}
                        </div>
                      )}
                    </div>
                  </td>

                  <td className="px-6 py-4">
                    <div className="text-sm space-y-1">
                      {exportItem.filename && (
                        <div className="text-gray-900 truncate max-w-xs" title={exportItem.filename}>
                          📁 {exportItem.filename}
                        </div>
                      )}
                      {exportItem.file_size_bytes && (
                        <div className="text-xs text-gray-500">
                          {exportProgressService.formatFileSize(exportItem.file_size_bytes)}
                        </div>
                      )}
                      {exportItem.quality_score && (
                        <div className="text-xs text-green-600">
                          Quality: {(exportItem.quality_score * 100).toFixed(0)}%
                        </div>
                      )}
                    </div>
                  </td>

                  <td className="px-6 py-4">
                    <div className="text-sm space-y-1">
                      <div className="text-xs text-gray-500">
                        Created: {new Date(exportItem.created_at).toLocaleString()}
                      </div>
                      {exportItem.started_at && (
                        <div className="text-xs text-gray-500">
                          Started: {new Date(exportItem.started_at).toLocaleString()}
                        </div>
                      )}
                      {exportItem.completed_at && (
                        <div className="text-xs text-gray-500">
                          Completed: {new Date(exportItem.completed_at).toLocaleString()}
                        </div>
                      )}
                      {exportItem.estimated_time_remaining && exportItem.status === 'running' && (
                        <div className="text-xs text-blue-600">
                          ⏱️ {exportProgressService.formatTimeRemaining(exportItem.estimated_time_remaining)}
                        </div>
                      )}
                    </div>
                  </td>

                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-2">
                      {exportItem.status === 'running' && (
                        <button
                          onClick={() => handleCancelExport(exportItem.export_id)}
                          className="px-2 py-1 text-xs bg-red-100 hover:bg-red-200 text-red-700 rounded transition-colors"
                        >
                          Cancel
                        </button>
                      )}

                      {exportItem.status === 'failed' && exportItem.retry_count < exportItem.max_retries && (
                        <button
                          onClick={() => handleRetryExport(exportItem.export_id)}
                          className="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 rounded transition-colors"
                        >
                          Retry
                        </button>
                      )}

                      {exportItem.status === 'completed' && (
                        <button
                          onClick={() => handleDownloadExport(exportItem.export_id)}
                          className="px-2 py-1 text-xs bg-green-100 hover:bg-green-200 text-green-700 rounded transition-colors flex items-center space-x-1"
                        >
                          <span>📥</span>
                          <span>Download</span>
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="px-6 py-3 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div>
            Showing {filteredAndSortedExports.length} of {activeExports.length} exports
          </div>
          <div>
            Auto-refresh: {autoRefreshEnabled ? 'Every 5s' : 'Off'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExportQueueManager;