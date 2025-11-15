import { useState, useCallback, useEffect } from 'react';
import api from '../lib/api';
import type { DraftItem } from '../types/unified';

// Using DraftItem type for LessonItem since they have the same structure
type LessonItem = DraftItem;

export function useLessons() {
  const [lessons, setLessons] = useState<LessonItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lessonCount, setLessonCount] = useState<number>(0);

  const loadLessons = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await api.getLessons();
      if (result.ok) {
        setLessons(result.data);
        setLessonCount(result.data.length);
        return result.data;
      } else {
        setError(result.message || 'Failed to load lessons');
        return [];
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load lessons';
      setError(errorMessage);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getLesson = useCallback(async (lessonId: string): Promise<LessonItem | null> => {
    try {
      const result = await api.getPermanentLesson(lessonId);
      if (result.ok) {
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
  }, []);

  const deleteLesson = useCallback(async (lessonId: string): Promise<boolean> => {
    try {
      const result = await api.deleteLesson(lessonId);

      if (result.ok) {
        setLessons(prev => prev.filter(lesson => lesson.id !== lessonId));
        setLessonCount(prev => prev - 1);
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
  }, []);

  const promoteFromDraft = useCallback(async (draftId: string): Promise<LessonItem | null> => {
    try {
      const result = await api.promoteLesson(draftId);

      if (result.ok) {
        // Add the newly promoted lesson to the lessons list
        setLessons(prev => [result.data, ...prev]);
        setLessonCount(prev => prev + 1);
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
  }, []);

  const demoteToLesson = useCallback(async (lessonId: string): Promise<LessonItem | null> => {
    try {
      const result = await api.demoteLesson(lessonId);

      if (result.ok) {
        // Remove the demoted lesson from the lessons list
        setLessons(prev => prev.filter(lesson => lesson.id !== lessonId));
        setLessonCount(prev => prev - 1);
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
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Load lessons on mount
  useEffect(() => {
    loadLessons();
  }, [loadLessons]);

  return {
    lessons,
    isLoading,
    error,
    lessonCount,
    loadLessons,
    getLesson,
    deleteLesson,
    promoteFromDraft,
    demoteToLesson,
    clearError,
  };
}
