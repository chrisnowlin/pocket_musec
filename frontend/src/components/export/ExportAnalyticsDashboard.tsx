import React, { useState, useEffect } from 'react';
import { exportProgressService, ExportAnalytics, ExportFormatProgress } from '../../services/exportProgressService';

interface ExportAnalyticsDashboardProps {
  className?: string;
  timeWindowHours?: number;
  refreshInterval?: number;
}

export const ExportAnalyticsDashboard: React.FC<ExportAnalyticsDashboardProps> = ({
  className = '',
  timeWindowHours = 24,
  refreshInterval = 30000, // 30 seconds
}) => {
  const [analytics, setAnalytics] = useState<ExportAnalytics | null>(null);
  const [activeExports, setActiveExports] = useState<ExportFormatProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadAnalytics = async () => {
    try {
      setError(null);
      const data = await exportProgressService.getExportAnalytics(timeWindowHours);
      setAnalytics(data);
    } catch (err: any) {
      console.error('Failed to load analytics:', err);
      setError(err.message || 'Failed to load analytics');
    }
  };

  const loadActiveExports = async () => {
    try {
      const data = await exportProgressService.listActiveExports();
      setActiveExports(data);
    } catch (err: any) {
      console.error('Failed to load active exports:', err);
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    await Promise.all([loadAnalytics(), loadActiveExports()]);
    setRefreshing(false);
  };

  useEffect(() => {
    const initialLoad = async () => {
      setLoading(true);
      await refreshData();
      setLoading(false);
    };

    initialLoad();

    const interval = setInterval(refreshData, refreshInterval);

    return () => clearInterval(interval);
  }, [timeWindowHours, refreshInterval]);

  if (loading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center justify-center space-x-3">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          <span className="text-gray-600">Loading export analytics...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center space-x-3">
          <span>❌</span>
          <div className="flex-1">
            <h3 className="font-medium text-red-900">Analytics Error</h3>
            <p className="text-sm text-red-700">{error}</p>
          </div>
          <button
            onClick={refreshData}
            className="px-3 py-1 text-sm bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
      <p className="text text-gray-500">No analytics data available</p>
    </div>;
  }

  const formatUsageChart = () => {
    const total = Object.values(analytics.formats_used).reduce((sum, count) => sum + count, 0);
    if (total === 0) return null;

    const maxCount = Math.max(...Object.values(analytics.formats_used));

    return (
      <div className="space-y-3">
        {Object.entries(analytics.formats_used).map(([format, count]) => {
          const percentage = (count / total) * 100;
          const width = (count / maxCount) * 100;

          return (
            <div key={format} className="flex items-center space-x-3">
              <div className="w-20 text-sm font-medium capitalize">{format}</div>
              <div className="flex-1">
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className={`h-full rounded-full ${
                      exportProgressService.getFormatColor(format)
                    }`}
                    style={{ width: `${width}%` }}
                  />
                </div>
              </div>
              <div className="w-16 text-sm text-right">
                {count} ({percentage.toFixed(1)}%)
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const getStatusIndicator = (value: number, thresholds: { good: number; warning: number; bad: number }) => {
    if (value >= thresholds.good) return 'text-green-600';
    if (value >= thresholds.warning) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getStatusIcon = (status: 'good' | 'warning' | 'error') => {
    const icons = {
      good: '✅',
      warning: '⚠️',
      error: '❌',
    };
    return icons[status];
  };

  const successRateStatus = analytics.success_rate >= 90 ? 'good' :
                           analytics.success_rate >= 75 ? 'warning' : 'error';

  const performanceStatus = analytics.average_processing_time_seconds <= 30 ? 'good' :
                           analytics.average_processing_time_seconds <= 60 ? 'warning' : 'error';

  const sizeStatus = analytics.average_file_size_bytes <= 5_000_000 ? 'good' :
                    analytics.average_file_size_bytes <= 10_000_000 ? 'warning' : 'error';

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Export Analytics</h2>
          <p className="text-sm text-gray-500">
            Last {timeWindowHours} hours • {analytics.total_exports} total exports
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={refreshData}
            disabled={refreshing}
            className={`px-3 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors flex items-center space-x-1 ${
              refreshing ? 'opacity-50' : ''
            }`}
          >
            <span>{refreshing ? '🔄' : '🔃'}</span>
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Success Rate</p>
              <p className={`text-2xl font-bold ${getStatusIndicator(analytics.success_rate, { good: 90, warning: 75, bad: 0 })}`}>
                {analytics.success_rate.toFixed(1)}%
              </p>
            </div>
            <span className="text-2xl">{getStatusIcon(successRateStatus)}</span>
          </div>
          <div className="mt-2 text-xs text-gray-500">
            {analytics.successful_exports}/{analytics.total_exports} successful
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Avg. Time</p>
              <p className={`text-2xl font-bold ${getStatusIndicator(100 - analytics.average_processing_time_seconds, { good: 70, warning: 40, bad: 0 })}`}>
                {analytics.average_processing_time_seconds.toFixed(0)}s
              </p>
            </div>
            <span className="text-2xl">{getStatusIcon(performanceStatus)}</span>
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Per export
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Avg. Size</p>
              <p className={`text-2xl font-bold ${getStatusIndicator(100 - (analytics.average_file_size_bytes / 1000000), { good: 90, warning: 70, bad: 0 })}`}>
                {(analytics.average_file_size_bytes / 1000000).toFixed(1)}MB
              </p>
            </div>
            <span className="text-2xl">{getStatusIcon(sizeStatus)}</span>
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Per export
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Popular</p>
              <p className="text-2xl font-bold text-gray-900">
                {analytics.most_popular_format?.toUpperCase() || 'N/A'}
              </p>
            </div>
            <span>{analytics.most_popular_format ? exportProgressService.getExportFormatIcon(analytics.most_popular_format) : '📊'}</span>
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Most used format
          </div>
        </div>
      </div>

      {/* Format Usage */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Format Usage</h3>
        {formatUsageChart() || (
          <p className="text-sm text-gray-500">No usage data available</p>
        )}
      </div>

      {/* Performance Summary */}
      {Object.keys(analytics.performance_summary).length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-yellow-900 mb-4">Performance Insights</h3>
          <div className="space-y-2">
            {Object.entries(analytics.performance_summary).map(([key, value]) => (
              <div key={key} className="flex items-center space-x-2">
                <span className="text-yellow-600">⚠️</span>
                <span className="text-sm text-yellow-800">
                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: {value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Exports */}
      {activeExports.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Active Exports ({activeExports.length})
          </h3>
          <div className="space-y-3">
            {activeExports.slice(0, 10).map((exportItem) => (
              <div key={exportItem.export_id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <div className="flex items-center space-x-3">
                  <span>{exportProgressService.getExportFormatIcon(exportItem.format)}</span>
                  <div>
                    <p className="text-sm font-medium capitalize">{exportItem.format}</p>
                    <p className="text-xs text-gray-500">
                      Status: {exportItem.status} • {exportItem.overall_progress.toFixed(1)}%
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-full rounded-full ${
                        exportProgressService.getStatusColor(exportItem.status)
                      }`}
                      style={{ width: `${exportItem.overall_progress}%` }}
                    />
                  </div>
                  <button
                    onClick={() => exportProgressService.cancelExport(exportItem.export_id)}
                    className="text-xs text-red-600 hover:text-red-700"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ))}
            {activeExports.length > 10 && (
              <p className="text-xs text-gray-500 pt-2">
                +{activeExports.length - 10} more active exports
              </p>
            )}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <button
            onClick={() => exportProgressService.listActiveExports('failed')}
            className="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-md transition-colors text-sm"
          >
            View Failed Exports
          </button>
          <button
            onClick={() => {}}
            className="px-4 py-2 bg-yellow-100 hover:bg-yellow-200 text-yellow-700 rounded-md transition-colors text-sm"
          >
            Cleanup Old Data
          </button>
          <button
            onClick={() => exportProgressService.getExportAnalytics(168)} // 7 days
            className="px-4 py-2 bg-green-100 hover:bg-green-200 text-green-700 rounded-md transition-colors text-sm"
          >
            View Weekly Stats
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExportAnalyticsDashboard;