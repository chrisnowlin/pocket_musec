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

      // Call parent callback to update session state in parent component
      onModelChange(newModel);
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
      <div className="mb-2">
        <div className="flex items-center space-x-2 text-xs text-ink-500">
          <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-ink-500"></div>
          <span>Loading models...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mb-2">
        <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-2 py-1">
          {error}
        </div>
      </div>
    );
  }

  if (!modelAvailability || modelAvailability.available_models.length === 0) {
    return (
      <div className="mb-2">
        <div className="text-xs text-ink-500 bg-ink-50 border border-ink-200 rounded px-2 py-1">
          No models available
        </div>
      </div>
    );
  }

  return (
    <select
      value={currentModel || ''}
      onChange={(e) => handleModelChange(e.target.value)}
      disabled={disabled}
      className="w-28 border border-ink-300 rounded-lg px-2 py-1.5 text-xs bg-parchment-50 text-ink-800 focus:outline-none focus:ring-2 focus:ring-ink-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
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
  );
}