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
  const debounceTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const intervalIdRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastContentRef = useRef<string>('');
  const latestContentRef = useRef<string>('');
  const pendingSaveRef = useRef(false);

  const saveContent = useCallback(async (content: string, force = false) => {
    if ((!enabled && !force) || content === lastContentRef.current) return;
    
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

  const flushPendingSave = useCallback(async () => {
    if (!pendingSaveRef.current) return;
    pendingSaveRef.current = false;
    await saveContent(latestContentRef.current);
  }, [saveContent]);

  const triggerSave = useCallback((content: string) => {
    if (!enabled) return;
    latestContentRef.current = content;
    pendingSaveRef.current = true;

    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    debounceTimeoutRef.current = setTimeout(() => {
      flushPendingSave().catch(() => {
        // Errors are already logged inside saveContent
      });
      debounceTimeoutRef.current = null;
    }, debounceMs);
  }, [enabled, debounceMs, flushPendingSave]);

  const saveImmediately = useCallback(async (content: string) => {
    // Clear pending saves to prevent memory leaks
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
      debounceTimeoutRef.current = null;
    }
    pendingSaveRef.current = false;
    latestContentRef.current = content;
    return saveContent(content, true);
  }, [saveContent]);

  // Cleanup on unmount and when dependencies change
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
        debounceTimeoutRef.current = null;
      }
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
    };
  }, [enabled, onSave]);

  useEffect(() => {
    if (!enabled || intervalMs <= 0) {
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
      return;
    }

    intervalIdRef.current = setInterval(() => {
      flushPendingSave().catch(() => {
        // Errors already handled in saveContent
      });
    }, intervalMs);

    return () => {
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
    };
  }, [enabled, intervalMs, flushPendingSave]);

  return {
    triggerSave,
    saveImmediately,
    isSaving,
  };
}