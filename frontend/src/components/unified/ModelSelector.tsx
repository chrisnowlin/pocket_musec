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
      
      // Use current_model from API response if available, otherwise fall back to prop
      // This ensures we have the correct value even if the prop hasn't updated yet
      const modelToUse = data.current_model || currentModel || null;
      console.log('[ModelSelector] Fetched models:');
      console.log('  - current_model_from_api:', data.current_model);
      console.log('  - currentModel_prop:', currentModel);
      console.log('  - modelToUse:', modelToUse);
      console.log('  - available_model_ids:', data.available_models.map(m => m.id));
      console.log('  - select_will_show:', modelToUse || '(empty - will show "Select a model...")');
      setLocalSelectedModel(modelToUse);
    } catch (err) {
      console.error('Error fetching models:', err);
      setError(err instanceof Error ? err.message : 'Failed to load models');
    } finally {
      setIsLoading(false);
    }
  };

  const handleModelChange = async (newModel: string) => {
    // Convert empty string to null for consistency
    const modelValue = newModel === '' ? null : newModel;
    
    console.log('[ModelSelector] Model change requested:');
    console.log('  - newModel:', newModel);
    console.log('  - modelValue:', modelValue);
    console.log('  - localSelectedModel:', localSelectedModel);
    console.log('  - currentModel:', currentModel);
    console.log('  - disabled:', disabled);
    
    if (disabled || modelValue === localSelectedModel) {
      console.log('[ModelSelector] Change skipped - disabled:', disabled, 'sameValue:', modelValue === localSelectedModel);
      return;
    }

    // Optimistically update local state immediately for instant UI feedback
    console.log('[ModelSelector] Optimistically updating to:', modelValue);
    setLocalSelectedModel(modelValue);

    try {
      setError(null);
      
      const response = await fetch(`/api/sessions/${sessionId}/models`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ selected_model: modelValue }),
      });

      if (!response.ok) {
        // Revert optimistic update on error
        setLocalSelectedModel(currentModel);
        throw new Error(`Failed to update model: ${response.statusText}`);
      }

      // Parse the response to get the updated session
      const updatedSession = await response.json();
      
      // Use the selected_model from the response to ensure consistency
      const actualSelectedModel = updatedSession.selected_model || null;
      
      console.log('[ModelSelector] API update successful:');
      console.log('  - updatedSession.selected_model:', updatedSession.selected_model);
      console.log('  - actualSelectedModel:', actualSelectedModel);
      console.log('  - Updating local state to:', actualSelectedModel);
      
      // Update local state with the actual value from server
      setLocalSelectedModel(actualSelectedModel);
      
      // Call parent callback with both the model and the full updated session
      // This allows the parent to update state without making a redundant API call
      console.log('[ModelSelector] Calling onModelChange with:', actualSelectedModel);
      onModelChange(actualSelectedModel, updatedSession);
    } catch (err) {
      console.error('Error updating model:', err);
      setError(err instanceof Error ? err.message : 'Failed to update model');
      // Ensure local state matches currentModel prop after error
      setLocalSelectedModel(currentModel);
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

  const selectValue = localSelectedModel || '';
  console.log('[ModelSelector] Rendering select:');
  console.log('  - localSelectedModel:', localSelectedModel);
  console.log('  - selectValue:', selectValue);
  console.log('  - currentModel prop:', currentModel);
  console.log('  - availableOptions:', modelAvailability.available_models.map(m => ({ id: m.id, name: m.name })));

  return (
    <select
      value={selectValue}
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
