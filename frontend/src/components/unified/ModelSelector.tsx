import { useState, useEffect } from 'react';
import type { ModelAvailability } from '../../types/unified';
import type { SessionResponsePayload } from '../../lib/types';

interface ModelSelectorProps {
  sessionId: string;
  currentModel: string | null;
  onModelChange: (model: string | null, updatedSession?: SessionResponsePayload) => void;
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
  const [localSelectedModel, setLocalSelectedModel] = useState<string | null>(currentModel);
  
  // Always sync to the latest prop so other components stay in control of the selection
  useEffect(() => {
    setLocalSelectedModel(currentModel ?? null);
  }, [currentModel, sessionId]);

  // Fetch available models when component mounts or session changes
  useEffect(() => {
    if (processingMode !== 'cloud' || !sessionId) {
      setIsLoading(false);
      return;
    }

    fetchAvailableModels();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
      
      // API now always returns a currentModel (defaults to Kimi K2 if not set)
      // Use currentModel from API response as the source of truth
      const modelToUse = data.currentModel;
      if (modelToUse) {
        setLocalSelectedModel(modelToUse);
      }
    } catch (err) {
      console.error('Error fetching models:', err);
      setError(err instanceof Error ? err.message : 'Failed to load models');
    } finally {
      setIsLoading(false);
    }
  };

  const handleModelChange = async (newModel: string) => {
    // Don't allow empty selection - always have a model selected
    if (!newModel || newModel === '') {
      return;
    }
    
    if (disabled || newModel === localSelectedModel) {
      return;
    }

    // Optimistically update local state immediately for instant UI feedback
    setLocalSelectedModel(newModel);

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
        // Revert optimistic update on error
        setLocalSelectedModel(currentModel || modelAvailability?.currentModel || '');
        throw new Error(`Failed to update model: ${response.statusText}`);
      }

      // Parse the response to get the updated session
      const updatedSession = await response.json();
      
      // Use the selectedModel from the response to ensure consistency
      const actualSelectedModel = updatedSession.selectedModel || newModel;
      
      // Update local state with the actual value from server
      setLocalSelectedModel(actualSelectedModel);
      
      // Call parent callback with both the model and the full updated session
      onModelChange(actualSelectedModel, updatedSession);
    } catch (err) {
      console.error('Error updating model:', err);
      setError(err instanceof Error ? err.message : 'Failed to update model');
      // Revert to current model or default from API
      setLocalSelectedModel(currentModel || modelAvailability?.currentModel || '');
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

  if (!modelAvailability || modelAvailability.availableModels.length === 0) {
    return (
      <div className="mb-2">
        <div className="text-xs text-ink-500 bg-ink-50 border border-ink-200 rounded px-2 py-1">
          No models available
        </div>
      </div>
    );
  }

  // Always have a selected value - use localSelectedModel or fall back to API currentModel
  const selectValue = localSelectedModel || modelAvailability?.currentModel || '';

  return (
    <select
      value={selectValue}
      onChange={(e) => handleModelChange(e.target.value)}
      disabled={disabled}
      className="w-28 border border-ink-300 rounded-lg px-2 py-1.5 text-xs bg-parchment-50 text-ink-800 focus:outline-none focus:ring-2 focus:ring-ink-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {modelAvailability.availableModels.map((model) => (
        <option
          key={model.id}
          value={model.id}
          disabled={!model.available}
        >
          {model.name} {model.is_default && '(Default)'} {!model.available && '(Unavailable)'}
          {model.recommended && ' ⭐'}
        </option>
      ))}
    </select>
  );
}
