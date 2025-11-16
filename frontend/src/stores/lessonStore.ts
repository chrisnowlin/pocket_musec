import { create } from 'zustand';
import type { DraftItem } from '../types/unified';

export type LessonItem = DraftItem;

interface LessonStoreState {
  lessons: LessonItem[];
  lessonCount: number;
  selectedLessonId: string | null;
  error: string | null;
  setLessons: (lessons: LessonItem[]) => void;
  setError: (error: string | null) => void;
  setSelectedLessonId: (lessonId: string | null) => void;
  upsertLesson: (lesson: LessonItem) => void;
  removeLesson: (lessonId: string) => void;
}

export const useLessonStore = create<LessonStoreState>((set) => ({
  lessons: [],
  lessonCount: 0,
  selectedLessonId: null,
  error: null,
  setLessons: (lessons) => set({ lessons, lessonCount: lessons.length }),
  setError: (error) => set({ error }),
  setSelectedLessonId: (lessonId) => set({ selectedLessonId: lessonId }),
  upsertLesson: (lesson) =>
    set((state) => {
      const existingIndex = state.lessons.findIndex((l) => l.id === lesson.id);
      let nextLessons: LessonItem[];
      if (existingIndex >= 0) {
        nextLessons = state.lessons.map((item, index) =>
          index === existingIndex ? lesson : item
        );
      } else {
        nextLessons = [lesson, ...state.lessons];
      }
      return {
        lessons: nextLessons,
        lessonCount: nextLessons.length,
      };
    }),
  removeLesson: (lessonId) =>
    set((state) => {
      const filtered = state.lessons.filter((lesson) => lesson.id !== lessonId);
      const selectedLessonId = state.selectedLessonId === lessonId ? null : state.selectedLessonId;
      return {
        lessons: filtered,
        lessonCount: filtered.length,
        selectedLessonId,
      };
    }),
}));
