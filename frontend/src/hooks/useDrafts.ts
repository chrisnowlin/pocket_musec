import { useState, useCallback, useEffect } from 'react';
import api from '../lib/api';
import type { DraftItem } from '../types/unified';

export function useDrafts() {
  const [drafts, setDrafts] = useState<DraftItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [draftCount, setDraftCount] = useState<number>(0);
  
  // Edit mode state management
  const [editingDraftId, setEditingDraftId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState<boolean>(false);

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

  // Edit mode management functions
  const setEditMode = useCallback((draftId: string | null) => {
    setEditingDraftId(draftId);
  }, []);

  const getEditingDraft = useCallback((): DraftItem | null => {
    if (!editingDraftId) return null;
    return drafts.find(draft => draft.id === editingDraftId) || null;
  }, [editingDraftId, drafts]);

  const isEditingDraft = useCallback((draftId: string): boolean => {
    return editingDraftId === draftId;
  }, [editingDraftId]);

  const clearEditMode = useCallback(() => {
    setEditingDraftId(null);
  }, []);

  const getDraftWithUpdates = useCallback((
    draftId: string,
    updates: Partial<DraftItem>
  ): DraftItem | null => {
    const draft = drafts.find(d => d.id === draftId);
    if (!draft) return null;
    return { ...draft, ...updates };
  }, [drafts]);

  const saveEditedLesson = useCallback(async (
    draftId: string,
    content: string,
    title?: string
  ): Promise<DraftItem | null> => {
    setIsSaving(true);
    setError(null);
    
    try {
      // Optimistic update - update local state immediately
      const currentDraft = drafts.find(d => d.id === draftId);
      if (!currentDraft) {
        setError('Draft not found');
        return null;
      }

      // Capture draft data outside to prevent stale closures
      const capturedDraft = { ...currentDraft };

      const optimisticUpdates: Partial<DraftItem> = {
        content,
        updatedAt: new Date().toISOString()
      };
      
      if (title !== undefined) {
        optimisticUpdates.title = title;
      }

      // Apply optimistic updates
      setDrafts(prev =>
        prev.map(draft =>
          draft.id === draftId
            ? { ...draft, ...optimisticUpdates }
            : draft
        )
      );

      // Make API call
      const result = await api.updateDraft(draftId, optimisticUpdates);
      
      if (result.ok) {
        // Update with server response
        setDrafts(prev =>
          prev.map(draft =>
            draft.id === draftId ? result.data : draft
          )
        );
        return result.data;
      } else {
        // Revert optimistic update on error using captured draft
        setDrafts(prev =>
          prev.map(draft =>
            draft.id === draftId ? capturedDraft : draft
          )
        );
        setError(result.message || 'Failed to save lesson');
        return null;
      }
    } catch (err: any) {
      // Revert optimistic update on error - use captured draft reference
      // instead of re-fetching from drafts array to prevent race conditions
      const capturedDraft = drafts.find(d => d.id === draftId);
      if (capturedDraft) {
        const stableDraft = { ...capturedDraft };
        setDrafts(prev =>
          prev.map(draft =>
            draft.id === draftId ? stableDraft : draft
          )
        );
      }
      const errorMessage = err.message || 'Failed to save lesson';
      setError(errorMessage);
      return null;
    } finally {
      setIsSaving(false);
    }
  }, [drafts]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Load drafts on mount
  useEffect(() => {
    loadDrafts();
  }, [loadDrafts]);

  return {
    // Existing state and functions
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
    
    // Edit mode state and functions
    editingDraftId,
    isSaving,
    setEditMode,
    getEditingDraft,
    isEditingDraft,
    clearEditMode,
    saveEditedLesson,
    getDraftWithUpdates,
  };
}