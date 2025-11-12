import { useCallback, useRef, useEffect, useState } from 'react';

interface UseAutoSaveOptions {
  onSave: (content: string) => Promise<void>;
  debounceMs?: number;
  intervalMs?: number;
  enabled?: boolean;
}

interface UseAutoSaveReturn {
  triggerSave: (content: string) => void;
  saveImmediately: (content: string) => Promise<void>;
  isSaving: boolean;
}

/**
 * Custom hook for handling auto-save functionality with debouncing
 */
export function useAutoSave({
  onSave,
  debounceMs = 2000,
  intervalMs = 30000,
  enabled = true,
}: UseAutoSaveOptions): UseAutoSaveReturn {
  const [isSaving, setIsSaving] = useState(false);
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const intervalTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastContentRef = useRef<string>('');

  const saveContent = useCallback(async (content: string) => {
    if (!enabled || content === lastContentRef.current) return;
    
    setIsSaving(true);
    
    try {
      await onSave(content);
      lastContentRef.current = content;
    } catch (error) {
      console.error('Auto-save failed:', error);
      throw error;
    } finally {
      setIsSaving(false);
    }
  }, [onSave, enabled]);

  const triggerSave = useCallback((content: string) => {
    if (!enabled) return;

    // Clear existing timeouts to prevent memory leaks
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
      debounceTimeoutRef.current = null;
    }

    if (intervalTimeoutRef.current) {
      clearTimeout(intervalTimeoutRef.current);
      intervalTimeoutRef.current = null;
    }

    // Set new debounce timeout
    debounceTimeoutRef.current = setTimeout(() => {
      saveContent(content);
      debounceTimeoutRef.current = null; // Clear reference after execution
    }, debounceMs);

    // Set interval timeout for periodic saves
    intervalTimeoutRef.current = setTimeout(() => {
      saveContent(content);
      intervalTimeoutRef.current = null; // Clear reference after execution
    }, intervalMs);
  }, [enabled, debounceMs, intervalMs, saveContent]);

  const saveImmediately = useCallback(async (content: string) => {
    // Clear pending saves to prevent memory leaks
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
      debounceTimeoutRef.current = null;
    }
    if (intervalTimeoutRef.current) {
      clearTimeout(intervalTimeoutRef.current);
      intervalTimeoutRef.current = null;
    }

    return saveContent(content);
  }, [saveContent]);

  // Cleanup on unmount and when dependencies change
  useEffect(() => {
    return () => {
      // Clear timeout references to prevent memory leaks
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
        debounceTimeoutRef.current = null;
      }
      if (intervalTimeoutRef.current) {
        clearTimeout(intervalTimeoutRef.current);
        intervalTimeoutRef.current = null;
      }
    };
  }, [enabled, onSave]); // Add dependencies to ensure cleanup when they change

  return {
    triggerSave,
    saveImmediately,
    isSaving,
  };
}