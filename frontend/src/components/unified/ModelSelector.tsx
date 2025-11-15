import { useState, useEffect } from 'react';
import type { ModelAvailability } from '../../types/unified';

interface ModelSelectorProps {
  sessionId: string;
  currentModel: string | null;
  onModelChange: (model: string | null) => void;
  disabled?: boolean;
  processingMode: string;
}

export default function ModelSelector({
  sessionId,
  currentModel,
  onModelChange,
  disabled = false,
  processingMode,
}: ModelSelectorProps) {
  const [modelAvailability, setModelAvailability] = useState<ModelAvailability | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch available models when component mounts or session changes
  useEffect(() => {
    if (processingMode !== 'cloud' || !sessionId) {
      setIsLoading(false);
      return;
    }

    fetchAvailableModels();
  }, [sessionId, processingMode]);

  const fetchAvailableModels = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(`/api/sessions/${sessionId}/models`);
      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.statusText}`);
      }
      
      const data: ModelAvailability = await response.json();
      setModelAvailability(data);
    } catch (err) {
      console.error('Error fetching models:', err);
      setError(err instanceof Error ? err.message : 'Failed to load models');
    } finally {
      setIsLoading(false);
    }
  };

  const handleModelChange = async (newModel: string) => {
    if (disabled || newModel === currentModel) return;

    try {
      setError(null);
      
      const response = await fetch(`/api/sessions/${sessionId}/models`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ selected_model: newModel }),
      });

      if (!response.ok) {
        throw new Error(`Failed to update model: ${response.statusText}`);
      }

      onModelChange(newModel);
      
      // Refresh model availability to update current model
      fetchAvailableModels();
    } catch (err) {
      console.error('Error updating model:', err);
      setError(err instanceof Error ? err.message : 'Failed to update model');
    }
  };

  // Don't render if not in cloud mode or no session
  if (processingMode !== 'cloud' || !sessionId) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="mb-3">
        <label className="block text-sm font-medium text-ink-700 mb-1">
          AI Model
        </label>
        <div className="flex items-center space-x-2 text-sm text-ink-500">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-ink-500"></div>
          <span>Loading models...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mb-3">
        <label className="block text-sm font-medium text-ink-700 mb-1">
          AI Model
        </label>
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-2 py-1">
          {error}
        </div>
      </div>
    );
  }

  if (!modelAvailability || modelAvailability.available_models.length === 0) {
    return (
      <div className="mb-3">
        <label className="block text-sm font-medium text-ink-700 mb-1">
          AI Model
        </label>
        <div className="text-sm text-ink-500 bg-ink-50 border border-ink-200 rounded px-2 py-1">
          No models available
        </div>
      </div>
    );
  }

  return (
    <div className="mb-3">
      <label className="block text-sm font-medium text-ink-700 mb-1">
        AI Model
      </label>
      <select
        value={currentModel || ''}
        onChange={(e) => handleModelChange(e.target.value)}
        disabled={disabled}
        className="w-full border border-ink-300 rounded-lg px-3 py-2 text-sm bg-parchment-50 text-ink-800 focus:outline-none focus:ring-2 focus:ring-ink-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <option value="">Select a model...</option>
        {modelAvailability.available_models.map((model) => (
          <option
            key={model.id}
            value={model.id}
            disabled={!model.available}
          >
            {model.name} {!model.available && '(Unavailable)'}
            {model.recommended && ' ⭐'}
          </option>
        ))}
      </select>
      
      {/* Model description */}
      {currentModel && (
        <div className="mt-1 text-xs text-ink-600">
          {(() => {
            const selectedModel = modelAvailability.available_models.find(m => m.id === currentModel);
            return selectedModel?.description || '';
          })()}
        </div>
      )}
      
      {/* Model capabilities */}
      {currentModel && (
        <div className="mt-1 flex flex-wrap gap-1">
          {(() => {
            const selectedModel = modelAvailability.available_models.find(m => m.id === currentModel);
            return selectedModel?.capabilities.map(capability => (
              <span
                key={capability}
                className="inline-block px-2 py-1 text-xs bg-ink-100 text-ink-700 rounded"
              >
                {capability}
              </span>
            )) || [];
          })()}
        </div>
      )}
    </div>
  );
}