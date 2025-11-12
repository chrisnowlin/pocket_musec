interface SettingsPanelProps {
  processingMode: string;
  onProcessingModeChange: (mode: string) => void;
  onClearChatHistory?: () => void;
}

export default function SettingsPanel({
  processingMode,
  onProcessingModeChange,
  onClearChatHistory,
}: SettingsPanelProps) {
  return (
    <div className="h-full overflow-y-auto px-6 py-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-ink-800">Settings</h2>
          <p className="text-ink-600 mt-2">
            Configure your processing preferences and system settings
          </p>
        </div>

        <div className="space-y-6">
          {/* Account Information */}
          <div className="workspace-card p-6">
            <h3 className="text-lg font-semibold text-ink-800 mb-4">Account Information</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-ink-600">Name:</span>
                <span className="font-medium text-ink-800">Demo User</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-ink-600">Email:</span>
                <span className="font-medium text-ink-800">demo@example.com</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-ink-600">Role:</span>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-parchment-200 text-ink-800 capitalize">
                  Admin
                </span>
              </div>
            </div>
          </div>

          {/* Processing Mode */}
          <div className="workspace-card p-6">
            <h3 className="text-lg font-semibold text-ink-800 mb-4">Processing Mode</h3>
            <p className="text-sm text-ink-600 mb-4">
              Choose how AI processing is performed for lesson generation and image analysis
            </p>
            <div className="space-y-3">
              <div
                className={`border-2 rounded-lg p-4 ${
                  processingMode === 'cloud' ? 'border-ink-500 bg-parchment-200' : 'border-ink-300'
                }`}
              >
                <div className="flex items-center">
                  <input
                    type="radio"
                    name="processing_mode"
                    checked={processingMode === 'cloud'}
                    onChange={() => onProcessingModeChange('cloud')}
                    className="h-4 w-4 text-ink-600 focus:ring-ink-500 border-ink-300"
                  />
                  <label className="ml-3">
                    <span className="text-lg font-medium text-ink-800">Cloud Mode</span>
                    {processingMode === 'cloud' && (
                      <span className="ml-2 inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-ink-600 text-parchment-100">
                        Current
                      </span>
                    )}
                  </label>
                </div>
                <p className="ml-7 mt-2 text-sm text-ink-600">
                  Fast processing with cloud AI API. No local setup required.
                </p>
              </div>
              <div
                className={`border-2 rounded-lg p-4 ${
                  processingMode === 'local' ? 'border-ink-500 bg-parchment-200' : 'border-ink-300'
                }`}
              >
                <div className="flex items-center">
                  <input
                    type="radio"
                    name="processing_mode"
                    checked={processingMode === 'local'}
                    onChange={() => onProcessingModeChange('local')}
                    className="h-4 w-4 text-ink-600 focus:ring-ink-500 border-ink-300"
                  />
                  <label className="ml-3">
                    <span className="text-lg font-medium text-ink-800">Local Mode</span>
                    {processingMode === 'local' && (
                      <span className="ml-2 inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-ink-600 text-parchment-100">
                        Current
                      </span>
                    )}
                  </label>
                </div>
                <p className="ml-7 mt-2 text-sm text-ink-600">
                  Private processing with local AI model. Data stays on your machine.
                </p>
              </div>
            </div>
          </div>

          {/* System Status */}
          <div className="workspace-card p-6">
            <h3 className="text-lg font-semibold text-ink-800 mb-4">System Status</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-ink-600">Backend API:</span>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-parchment-200 text-ink-800">
                  Connected
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-ink-600">Database:</span>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-parchment-200 text-ink-800">
                  Ready
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-ink-600">AI Services:</span>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-parchment-200 text-ink-800">
                  Online
                </span>
              </div>
            </div>
          </div>

          {/* Data Management */}
          <div className="workspace-card p-6">
            <h3 className="text-lg font-semibold text-ink-800 mb-4">Data Management</h3>
            <p className="text-sm text-ink-600 mb-4">
              Manage your chat history and conversation data
            </p>
            {onClearChatHistory && (
              <button
                onClick={onClearChatHistory}
                className="px-4 py-2 bg-red-600 text-parchment-100 rounded-md hover:bg-red-700 transition-colors flex items-center gap-2"
              >
                <svg
                  className="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
                Clear All Chat History
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
