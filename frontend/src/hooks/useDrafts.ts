import { useState, useCallback, useEffect } from 'react';
import api from '../lib/api';
import type { DraftItem } from '../types/unified';

export function useDrafts() {
  const [drafts, setDrafts] = useState<DraftItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [draftCount, setDraftCount] = useState<number>(0);

  const loadDrafts = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await api.getDrafts();
      if (result.ok) {
        setDrafts(result.data);
        setDraftCount(result.data.length);
        return result.data;
      } else {
        setError(result.message || 'Failed to load drafts');
        return [];
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load drafts';
      setError(errorMessage);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getDraft = useCallback(async (draftId: string): Promise<DraftItem | null> => {
    try {
      const result = await api.getDraft(draftId);
      if (result.ok) {
        return result.data;
      } else {
        setError(result.message || 'Failed to load draft');
        return null;
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load draft';
      setError(errorMessage);
      return null;
    }
  }, []);

  const createDraft = useCallback(async (
    sessionId: string,
    title: string,
    content: string,
    metadata?: Record<string, unknown>
  ): Promise<DraftItem | null> => {
    try {
      const result = await api.createDraft({
        session_id: sessionId,
        title,
        content,
        metadata,
      });
      
      if (result.ok) {
        setDrafts(prev => [result.data, ...prev]);
        setDraftCount(prev => prev + 1);
        return result.data;
      } else {
        setError(result.message || 'Failed to create draft');
        return null;
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to create draft';
      setError(errorMessage);
      return null;
    }
  }, []);

  const updateDraft = useCallback(async (
    draftId: string,
    updates: { title?: string; content?: string; metadata?: Record<string, unknown> }
  ): Promise<DraftItem | null> => {
    try {
      const result = await api.updateDraft(draftId, updates);
      
      if (result.ok) {
        setDrafts(prev => 
          prev.map(draft => 
            draft.id === draftId ? result.data : draft
          )
        );
        return result.data;
      } else {
        setError(result.message || 'Failed to update draft');
        return null;
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to update draft';
      setError(errorMessage);
      return null;
    }
  }, []);

  const deleteDraft = useCallback(async (draftId: string): Promise<boolean> => {
    try {
      const result = await api.deleteDraft(draftId);
      
      if (result.ok) {
        setDrafts(prev => prev.filter(draft => draft.id !== draftId));
        setDraftCount(prev => prev - 1);
        return true;
      } else {
        setError(result.message || 'Failed to delete draft');
        return false;
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to delete draft';
      setError(errorMessage);
      return false;
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Load drafts on mount
  useEffect(() => {
    loadDrafts();
  }, [loadDrafts]);

  return {
    drafts,
    isLoading,
    error,
    draftCount,
    loadDrafts,
    getDraft,
    createDraft,
    updateDraft,
    deleteDraft,
    clearError,
  };
}