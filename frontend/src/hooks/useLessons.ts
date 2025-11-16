import { useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import { useLessonStore, type LessonItem } from '../stores/lessonStore';

export function useLessons() {
  const lessons = useLessonStore((state) => state.lessons);
  const lessonCount = useLessonStore((state) => state.lessonCount);
  const error = useLessonStore((state) => state.error);
  const setLessons = useLessonStore((state) => state.setLessons);
  const setError = useLessonStore((state) => state.setError);
  const upsertLesson = useLessonStore((state) => state.upsertLesson);
  const removeLesson = useLessonStore((state) => state.removeLesson);
  const selectedLessonId = useLessonStore((state) => state.selectedLessonId);
  const setSelectedLessonId = useLessonStore((state) => state.setSelectedLessonId);
  const queryClient = useQueryClient();
  const selectedLesson = lessons.find((lesson) => lesson.id === selectedLessonId) || null;

  const {
    isFetching: isLoading,
    refetch: refetchLessons,
  } = useQuery({
    queryKey: ['lessons'],
    queryFn: async () => {
      const result = await api.getLessons();
      if (!result.ok) {
        throw new Error(result.message || 'Failed to load lessons');
      }
      return result.data as LessonItem[];
    },
    onSuccess: (data) => {
      setLessons(data);
      setError(null);
    },
    onError: (err: any) => {
      setError(err?.message || 'Failed to load lessons');
    },
  });

  const loadLessons = useCallback(async () => {
    setError(null);
    const result = await refetchLessons();
    if (result.error) {
      setError((result.error as Error).message || 'Failed to load lessons');
      return [];
    }
    return result.data ?? [];
  }, [refetchLessons, setError]);

  const getLesson = useCallback(async (lessonId: string): Promise<LessonItem | null> => {
    const cachedLesson = lessons.find((lesson) => lesson.id === lessonId);
    if (cachedLesson) {
      return cachedLesson;
    }

    try {
      const result = await api.getPermanentLesson(lessonId);
      if (result.ok) {
    upsertLesson(result.data);
        return result.data;
      } else {
        setError(result.message || 'Failed to load lesson');
        return null;
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load lesson';
      setError(errorMessage);
      return null;
    }
  }, [lessons, setError, upsertLesson]);

  const deleteLesson = useCallback(async (lessonId: string): Promise<boolean> => {
    try {
      const result = await api.deleteLesson(lessonId);

      if (result.ok) {
        removeLesson(lessonId);
        if (selectedLessonId === lessonId) {
          setSelectedLessonId(null);
        }
        return true;
      } else {
        setError(result.message || 'Failed to delete lesson');
        return false;
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to delete lesson';
      setError(errorMessage);
      return false;
    }
  }, [removeLesson, selectedLessonId, setSelectedLessonId, setError]);

  const promoteFromDraft = useCallback(async (draftId: string): Promise<LessonItem | null> => {
    try {
      const result = await api.promoteLesson(draftId);

      if (result.ok) {
        upsertLesson(result.data);
        return result.data;
      } else {
        setError(result.message || 'Failed to promote draft');
        return null;
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to promote draft';
      setError(errorMessage);
      return null;
    }
  }, [setError, upsertLesson]);

  const demoteToLesson = useCallback(async (lessonId: string): Promise<LessonItem | null> => {
    try {
      const result = await api.demoteLesson(lessonId);

      if (result.ok) {
        removeLesson(lessonId);
        if (selectedLessonId === lessonId) {
          setSelectedLessonId(null);
        }
        return result.data;
      } else {
        setError(result.message || 'Failed to demote lesson');
        return null;
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to demote lesson';
      setError(errorMessage);
      return null;
    }
  }, [removeLesson, selectedLessonId, setSelectedLessonId, setError]);

  const clearError = useCallback(() => {
    setError(null);
  }, [setError]);

  const invalidateLessons = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['lessons'] });
  }, [queryClient]);

  return {
    lessons,
    isLoading,
    error,
    lessonCount,
    selectedLesson,
    selectedLessonId,
    setSelectedLessonId,
    loadLessons,
    getLesson,
    deleteLesson,
    promoteFromDraft,
    demoteToLesson,
    clearError,
    invalidateLessons,
  };
}
