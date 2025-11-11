import { useState, useEffect } from 'react';
import api from '../lib/api';

interface ProcessingModeInfo {
  mode: string;
  display_name: string;
  description: string;
  is_available: boolean;
  features: string[];
}

interface LocalModelStatus {
  is_installed: boolean;
  model_name: string;
  model_size?: string;
  is_running: boolean;
  error?: string;
}

interface ProcessingModesResponse {
  modes: ProcessingModeInfo[];
}

export default function SettingsPage() {
  const [modes, setModes] = useState<ProcessingModeInfo[]>([]);
  const [localModelStatus, setLocalModelStatus] = useState<LocalModelStatus | null>(null);
  const [currentProcessingMode, setCurrentProcessingMode] = useState<string>('cloud');
  const [isUpdating, setIsUpdating] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadModes();
    loadLocalModelStatus();
  }, []);

  const loadModes = async () => {
    try {
      const result = await api.getProcessingModes();
      if (result.ok) {
        const data = result.data as ProcessingModesResponse;
        setModes(data.modes);
      } else {
        setError(result.message || 'Failed to load processing modes');
      }
    } catch (err) {
      console.error('Failed to load modes:', err);
      setError('Failed to load processing modes');
    }
  };

  const loadLocalModelStatus = async () => {
    try {
      const result = await api.getLocalModelStatus();
      if (result.ok) {
        setLocalModelStatus(result.data as LocalModelStatus);
      }
    } catch (err) {
      console.error('Failed to load local model status:', err);
    }
  };

  const handleModeChange = async (newMode: string) => {
    setIsUpdating(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await api.updateProcessingMode(newMode);
      if (result.ok) {
        setCurrentProcessingMode(newMode);
        setSuccess(`Processing mode updated to ${newMode}`);
      } else {
        setError(result.message || 'Failed to update processing mode');
      }
    } catch (err: any) {
      console.error('Failed to update mode:', err);
      setError(err.message || 'Failed to update processing mode');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDownloadModel = async () => {
    setIsDownloading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await api.downloadLocalModel();
      if (result.ok) {
        setSuccess('Local model download initiated. This may take several minutes.');

        // Poll for status updates
        const pollInterval = setInterval(async () => {
          await loadLocalModelStatus();
        }, 5000);

        // Stop polling after 5 minutes
        setTimeout(() => {
          clearInterval(pollInterval);
          setIsDownloading(false);
        }, 300000);
      } else {
        setError(result.message || 'Failed to download local model');
        setIsDownloading(false);
      }
    } catch (err: any) {
      console.error('Failed to download model:', err);
      setError(err.message || 'Failed to download local model');
      setIsDownloading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-gray-600">
          Configure your processing preferences and account settings
        </p>
      </div>

      {/* Account Information */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Account Information</h2>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Name:</span>
            <span className="font-medium">Demo User</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Email:</span>
            <span className="font-medium">demo@example.com</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Role:</span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800 capitalize">
              Admin
            </span>
          </div>
        </div>
      </div>

      {/* Processing Mode Configuration */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Processing Mode</h2>
        <p className="text-sm text-gray-600 mb-6">
          Choose how AI processing is performed for lesson generation and image analysis
        </p>

        <div className="space-y-4">
          {modes.map((mode) => (
            <div
              key={mode.mode}
              className={`border-2 rounded-lg p-4 transition-all ${
                currentProcessingMode === mode.mode
                  ? 'border-blue-500 bg-blue-50'
                  : mode.is_available
                  ? 'border-gray-300 hover:border-gray-400'
                  : 'border-gray-200 bg-gray-50 opacity-60'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center">
                    <input
                      type="radio"
                      name="processing_mode"
                      checked={currentProcessingMode === mode.mode}
                      onChange={() => mode.is_available && handleModeChange(mode.mode)}
                      disabled={!mode.is_available || isUpdating}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    />
                    <label className="ml-3 block">
                      <span className="text-lg font-medium text-gray-900">
                        {mode.display_name}
                      </span>
                      {currentProcessingMode === mode.mode && (
                        <span className="ml-2 inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-600 text-white">
                          Current
                        </span>
                      )}
                    </label>
                  </div>

                  <p className="ml-7 mt-2 text-sm text-gray-600">{mode.description}</p>

                  <div className="ml-7 mt-3">
                    <p className="text-xs font-medium text-gray-700 mb-1">Features:</p>
                    <ul className="space-y-1">
                      {mode.features.map((feature, idx) => (
                        <li key={idx} className="flex items-start text-sm text-gray-600">
                          <svg
                            className="h-4 w-4 text-green-500 mr-2 mt-0.5"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                              clipRule="evenodd"
                            />
                          </svg>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {!mode.is_available && (
                    <div className="ml-7 mt-3">
                      <p className="text-sm text-red-600 font-medium">
                        Local model not available
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Local Model Status */}
      {localModelStatus && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Local Model Status</h2>

          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Model:</span>
              <span className="font-medium">{localModelStatus.model_name}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-gray-600">Status:</span>
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  localModelStatus.is_installed
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}
              >
                {localModelStatus.is_installed ? 'Installed' : 'Not Installed'}
              </span>
            </div>

            {localModelStatus.model_size && (
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Size:</span>
                <span className="font-medium">{localModelStatus.model_size}</span>
              </div>
            )}

            <div className="flex justify-between items-center">
              <span className="text-gray-600">Ollama:</span>
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  localModelStatus.is_running
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {localModelStatus.is_running ? 'Running' : 'Not Running'}
              </span>
            </div>

            {localModelStatus.error && (
              <div className="rounded-md bg-red-50 p-4">
                <div className="text-sm text-red-800">{localModelStatus.error}</div>
              </div>
            )}

            {!localModelStatus.is_installed && !isDownloading && (
              <div className="pt-4">
                <button
                  onClick={handleDownloadModel}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Download Local Model
                </button>
                <p className="mt-2 text-xs text-gray-500">
                  This will download the Qwen3 8B model (~4.7GB). Requires Ollama to be installed
                  and running.
                </p>
              </div>
            )}

            {isDownloading && (
              <div className="pt-4">
                <div className="flex items-center justify-center">
                  <svg
                    className="animate-spin h-5 w-5 text-blue-600 mr-3"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <span className="text-gray-600">Downloading model...</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Messages */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      {success && (
        <div className="rounded-md bg-green-50 p-4">
          <div className="text-sm text-green-800">{success}</div>
        </div>
      )}

      {/* Privacy Notice */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">Processing Mode Comparison</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium text-blue-800 mb-2">Cloud Mode</h4>
            <ul className="space-y-1 text-sm text-blue-700">
              <li>• Fast processing with Chutes AI API</li>
              <li>• No local setup required</li>
              <li>• Best for quick results</li>
              <li>• Requires internet connection</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-blue-800 mb-2">Local Mode</h4>
            <ul className="space-y-1 text-sm text-blue-700">
              <li>• Private processing with Ollama</li>
              <li>• Data stays on your machine</li>
              <li>• Requires model download (~4.7GB)</li>
              <li>• Works offline after setup</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
