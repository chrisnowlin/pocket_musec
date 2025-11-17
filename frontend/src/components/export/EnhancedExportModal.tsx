import React, { useState, useEffect } from 'react';
import { exportProgressService, ExportRequest, BulkExportRequest, ExportOptions } from '../../services/exportProgressService';
import ExportProgressIndicator from './ExportProgressIndicator';
import BulkExportProgressIndicator from './BulkExportProgressIndicator';

interface EnhancedExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  presentationId: string;
  presentationTitle?: string;
}

interface FormatOption {
  format: 'json' | 'markdown' | 'pptx' | 'pdf';
  label: string;
  description: string;
  icon: string;
  estimatedTime: string;
  features: string[];
}

export const EnhancedExportModal: React.FC<EnhancedExportModalProps> = ({
  isOpen,
  onClose,
  presentationId,
  presentationTitle = 'Untitled Presentation',
}) => {
  const [selectedFormats, setSelectedFormats] = useState<string[]>(['markdown']);
  const [exportMode, setExportMode] = useState<'single' | 'bulk'>('single');
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState<any>(null);
  const [bulkExportProgress, setBulkExportProgress] = useState<any>(null);
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    include_metadata: true,
    include_teacher_script: true,
    batch_size: 2,
    max_retries: 3,
    timeout_seconds: 300,
  });
  const [error, setError] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const formatOptions: FormatOption[] = [
    {
      format: 'json',
      label: 'JSON',
      description: 'Structured data format for developers',
      icon: '📄',
      estimatedTime: '~5 seconds',
      features: ['Complete data structure', 'Metadata included', 'Machine readable'],
    },
    {
      format: 'markdown',
      label: 'Markdown',
      description: 'Plain text format for documentation',
      icon: '📝',
      estimatedTime: '~10 seconds',
      features: ['Human readable', 'Version control friendly', 'Portable'],
    },
    {
      format: 'pptx',
      label: 'PowerPoint',
      description: 'Professional presentation format',
      icon: '📊',
      estimatedTime: '~30 seconds',
      features: ['Professional layout', 'Slide animations', 'Print ready'],
    },
    {
      format: 'pdf',
      label: 'PDF',
      description: 'Universal document format',
      icon: '📋',
      estimatedTime: '~45 seconds',
      features: ['Cross-platform', 'Print optimized', 'Secure sharing'],
    },
  ];

  const handleFormatToggle = (format: string) => {
    if (exportMode === 'single') {
      setSelectedFormats([format]);
    } else {
      if (selectedFormats.includes(format)) {
        setSelectedFormats(selectedFormats.filter(f => f !== format));
      } else {
        setSelectedFormats([...selectedFormats, format]);
      }
    }
  };

  const handleSingleExport = async (format: string) => {
    setIsExporting(true);
    setError(null);

    try {
      const request: ExportRequest = { presentationId: presentationId,
        format: format as any,
        options: exportOptions,
        track_progress: true,
      };

      const response = await exportProgressService.startExport(request);

      if (response.export_id) {
        setExportProgress({
          exportId: response.export_id,
          format: format,
        });
      } else {
        // Simple export without progress tracking
        await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate completion
        await exportProgressService.downloadExportedFile(response.export_id! || 'temp');
        onClose();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to start export');
    }
  };

  const handleBulkExport = async () => {
    setIsExporting(true);
    setError(null);

    try {
      const request: BulkExportRequest = { presentationId: presentationId,
        formats: selectedFormats,
        options: exportOptions,
        create_zip: true,
        track_progress: true,
      };

      const response = await exportProgressService.startBulkExport(request);

      setBulkExportProgress({
        bulkExportId: response.bulk_export_id,
        formats: response.formats,
      });
    } catch (err: any) {
      setError(err.message || 'Failed to start bulk export');
    }
  };

  const handleExportComplete = (progress: any) => {
    setIsExporting(false);
    // Progress handled by indicators
  };

  const handleExportError = (err: Error) => {
    setIsExporting(false);
    setError(err.message);
  };

  const handleDownloadReady = (exportId: string) => {
    // Download ready notification
    console.log('Download ready for:', exportId);
  };

  const resetState = () => {
    setSelectedFormats(['markdown']);
    setExportMode('single');
    setIsExporting(false);
    setExportProgress(null);
    setBulkExportProgress(null);
    setError(null);
    setShowAdvanced(false);
  };

  useEffect(() => {
    if (isOpen) {
      resetState();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100]">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Export Presentation</h2>
              <p className="text-sm text-gray-500 mt-1">{presentationTitle}</p>
            </div>
            <button
              onClick={onClose}
              disabled={isExporting}
              className="p-2 hover:bg-gray-100 rounded-md transition-colors disabled:opacity-50"
            >
              ✕
            </button>
          </div>

          {/* Export Mode Selector */}
          <div className="flex items-center space-x-4 mt-4">
            <button
              onClick={() => setExportMode('single')}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                exportMode === 'single'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Single Format
            </button>
            <button
              onClick={() => setExportMode('bulk')}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                exportMode === 'bulk'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Multiple Formats
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {!isExporting ? (
            <div className="space-y-6">
              {/* Format Selection */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  {exportMode === 'single' ? 'Select Export Format' : 'Select Export Formats'}
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {formatOptions.map((option) => {
                    const isSelected = selectedFormats.includes(option.format);
                    const isSingle = exportMode === 'single';

                    return (
                      <div
                        key={option.format}
                        onClick={() => handleFormatToggle(option.format)}
                        className={`border rounded-lg p-4 cursor-pointer transition-all ${
                          isSelected
                            ? 'border-blue-500 bg-blue-50 shadow-md'
                            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-start space-x-3">
                          <div className="mt-1">
                            {isSingle ? (
                              <input
                                type="radio"
                                name="format"
                                checked={isSelected}
                                onChange={() => {}}
                                className="text-blue-600 focus:ring-blue-500"
                              />
                            ) : (
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => {}}
                                className="text-blue-600 focus:ring-blue-500 rounded"
                              />
                            )}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <span className="text-2xl">{option.icon}</span>
                              <div>
                                <h4 className="font-semibold text-gray-900">{option.label}</h4>
                                <p className="text-sm text-gray-600">{option.description}</p>
                              </div>
                            </div>
                            <div className="mt-2 space-y-1">
                              <p className="text-xs font-medium text-blue-600">{option.estimatedTime}</p>
                              <ul className="text-xs text-gray-500 space-y-0.5">
                                {option.features.map((feature, index) => (
                                  <li key={index}>• {feature}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Advanced Options */}
              <div>
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-700"
                >
                  <span>{showAdvanced ? 'Hide' : 'Show'} advanced options</span>
                  <span>{showAdvanced ? '▲' : '▼'}</span>
                </button>

                {showAdvanced && (
                  <div className="mt-4 space-y-4 bg-gray-50 rounded-lg p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="flex items-center space-x-2 text-sm">
                          <input
                            type="checkbox"
                            checked={exportOptions.include_metadata}
                            onChange={(e) =>
                              setExportOptions({
                                ...exportOptions,
                                include_metadata: e.target.checked,
                              })
                            }
                            className="text-blue-600 focus:ring-blue-500 rounded"
                          />
                          <span>Include metadata</span>
                        </label>
                      </div>
                      <div>
                        <label className="flex items-center space-x-2 text-sm">
                          <input
                            type="checkbox"
                            checked={exportOptions.include_teacher_script}
                            onChange={(e) =>
                              setExportOptions({
                                ...exportOptions,
                                include_teacher_script: e.target.checked,
                              })
                            }
                            className="text-blue-600 focus:ring-blue-500 rounded"
                          />
                          <span>Include teacher script</span>
                        </label>
                      </div>
                    </div>

                    {exportMode === 'bulk' && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Concurrent exports
                        </label>
                        <select
                          value={exportOptions.batch_size}
                          onChange={(e) =>
                            setExportOptions({
                              ...exportOptions,
                              batch_size: parseInt(e.target.value),
                            })
                          }
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                        >
                          <option value={1}>1 (Slow)</option>
                          <option value={2}>2 (Balanced)</option>
                          <option value={4}>4 (Fast)</option>
                        </select>
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Max retries
                      </label>
                      <select
                        value={exportOptions.max_retries}
                        onChange={(e) =>
                          setExportOptions({
                            ...exportOptions,
                            max_retries: parseInt(e.target.value),
                          })
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value={0}>No retries</option>
                        <option value={1}>1 retry</option>
                        <option value={3}>3 retries</option>
                        <option value={5}>5 retries</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3">
                <button
                  onClick={onClose}
                  disabled={isExporting}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-md transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() =>
                    exportMode === 'single'
                      ? handleSingleExport(selectedFormats[0])
                      : handleBulkExport()
                  }
                  disabled={
                    isExporting ||
                    (exportMode === 'single' && selectedFormats.length === 0) ||
                    (exportMode === 'bulk' && selectedFormats.length === 0)
                  }
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors disabled:opacity-50 flex items-center space-x-2"
                >
                  {exportMode === 'single' ? (
                    <>
                      <span>Export {selectedFormats[0]?.toUpperCase()}</span>
                    </>
                  ) : (
                    <>
                      <span>Export {selectedFormats.length} Formats</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Export Progress */}
              {exportProgress && (
                <ExportProgressIndicator
                  exportId={exportProgress.exportId}
                  showSteps={true}
                  onExportComplete={handleExportComplete}
                  onExportError={handleExportError}
                  onDownloadReady={handleDownloadReady}
                />
              )}

              {bulkExportProgress && (
                <BulkExportProgressIndicator
                  bulkExportId={bulkExportProgress.bulkExportId}
                  showFormatDetails={true}
                  onBulkExportComplete={handleExportComplete}
                  onBulkExportError={handleExportError}
                  onDownloadReady={handleDownloadReady}
                />
              )}

              {/* Error Display */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-md p-4">
                  <div className="flex items-start space-x-3">
                    <span>❌</span>
                    <div className="flex-1">
                      <h4 className="font-medium text-red-900">Export Failed</h4>
                      <p className="text-sm text-red-700">{error}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Actions during export */}
              <div className="flex justify-between">
                <button
                  onClick={() => {
                    if (exportProgress) {
                      exportProgressService.unsubscribeFromProgress(exportProgress.exportId);
                    }
                    if (bulkExportProgress) {
                      exportProgressService.unsubscribeFromProgress(undefined, bulkExportProgress.bulkExportId);
                    }
                    resetState();
                  }}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-md transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedExportModal;