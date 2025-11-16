import { useState, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import type { DraftItem } from '../types/unified';

const DRAFTS_QUERY_KEY = ['drafts'];

export function useDrafts() {
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [editingDraftId, setEditingDraftId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const {
    data: draftsData,
    isFetching: isLoading,
    refetch: refetchDrafts,
  } = useQuery({
    queryKey: DRAFTS_QUERY_KEY,
    queryFn: async () => {
      const result = await api.getDrafts();
      if (!result.ok) {
        throw new Error(result.message || 'Failed to load drafts');
      }
      return result.data;
    },
    onError: (err: any) => {
      setError(err?.message || 'Failed to load drafts');
    },
  });

  const drafts = draftsData ?? [];
  const draftCount = drafts.length;

  const updateDraftsCache = useCallback((updater: (drafts: DraftItem[]) => DraftItem[]) => {
    queryClient.setQueryData<DraftItem[]>(DRAFTS_QUERY_KEY, (prev = []) => updater(prev));
  }, [queryClient]);

  const loadDrafts = useCallback(async () => {
    setError(null);
    const result = await refetchDrafts();
    if (result.error) {
      setError((result.error as Error).message || 'Failed to load drafts');
      return [];
    }
    return result.data ?? [];
  }, [refetchDrafts]);

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
        updateDraftsCache(prev => [result.data, ...prev]);
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
  }, [updateDraftsCache]);

  const updateDraft = useCallback(async (
    draftId: string,
    updates: { title?: string; content?: string; metadata?: Record<string, unknown> }
  ): Promise<DraftItem | null> => {
    try {
      const result = await api.updateDraft(draftId, updates);

      if (result.ok) {
        updateDraftsCache(prev =>
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
  }, [updateDraftsCache]);

  const deleteDraft = useCallback(async (draftId: string): Promise<boolean> => {
    try {
      const result = await api.deleteDraft(draftId);

      if (result.ok) {
        updateDraftsCache(prev => prev.filter(draft => draft.id !== draftId));
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
  }, [updateDraftsCache]);

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
    let capturedDraft: DraftItem | null = null;

    try {
      const currentDraft = drafts.find(d => d.id === draftId);
      if (!currentDraft) {
        setError('Draft not found');
        return null;
      }

      capturedDraft = { ...currentDraft };
      const optimisticUpdates: Partial<DraftItem> = {
        content,
        updatedAt: new Date().toISOString()
      };

      if (!currentDraft.originalContent) {
        optimisticUpdates.originalContent = currentDraft.content;
      }

      if (title !== undefined) {
        optimisticUpdates.title = title;
      }

      if (currentDraft.metadata && 'lesson_document' in currentDraft.metadata) {
        const lessonDocument: any = (currentDraft.metadata as any).lesson_document;
        if (lessonDocument && lessonDocument.content) {
          optimisticUpdates.metadata = {
            ...currentDraft.metadata,
            lesson_document: {
              ...lessonDocument,
              content: {
                ...lessonDocument.content,
                notes: content,
              },
            },
          } as any;
        }
      }

      updateDraftsCache(prev =>
        prev.map(draft =>
          draft.id === draftId ? { ...draft, ...optimisticUpdates } : draft
        )
      );

      const result = await api.updateDraft(draftId, optimisticUpdates);

      if (result.ok) {
        updateDraftsCache(prev =>
          prev.map(draft =>
            draft.id === draftId ? result.data : draft
          )
        );
        return result.data;
      } else {
        if (capturedDraft) {
          updateDraftsCache(prev =>
            prev.map(draft =>
              draft.id === draftId ? capturedDraft : draft
            )
          );
        }
        setError(result.message || 'Failed to save lesson');
        return null;
      }
    } catch (err: any) {
      if (capturedDraft) {
        const stableDraft = { ...capturedDraft };
        updateDraftsCache(prev =>
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
  }, [drafts, updateDraftsCache]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

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
