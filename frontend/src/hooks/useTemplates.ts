import { useState, useCallback, useEffect } from 'react';
import type { TemplateItem } from '../types/unified';
import type { StandardRecord } from '../lib/types';

const TEMPLATES_STORAGE_KEY = 'pocketmusec-templates';

interface CreateTemplateData {
  name: string;
  description: string;
  content: string;
  grade: string;
  strand: string;
  standardId?: string;
  standardCode?: string;
  standardTitle?: string;
  objective?: string;
  lessonDuration?: string;
  classSize?: string;
}

export function useTemplates() {
  const [templates, setTemplates] = useState<TemplateItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [templateCount, setTemplateCount] = useState<number>(0);

  const generateId = () => {
    return `template-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  const loadTemplates = useCallback(() => {
    setIsLoading(true);
    setError(null);
    
    try {
      const stored = localStorage.getItem(TEMPLATES_STORAGE_KEY);
      const parsedTemplates = stored ? JSON.parse(stored) : [];
      setTemplates(parsedTemplates);
      setTemplateCount(parsedTemplates.length);
      return parsedTemplates;
    } catch (err: any) {
      const errorMessage = 'Failed to load templates from storage';
      setError(errorMessage);
      console.error('Failed to load templates:', err);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  const saveTemplates = useCallback((templatesToSave: TemplateItem[]) => {
    try {
      localStorage.setItem(TEMPLATES_STORAGE_KEY, JSON.stringify(templatesToSave));
      setTemplates(templatesToSave);
      setTemplateCount(templatesToSave.length);
    } catch (err: any) {
      const errorMessage = 'Failed to save templates to storage';
      setError(errorMessage);
      console.error('Failed to save templates:', err);
      throw err;
    }
  }, []);

  const createTemplate = useCallback((
    data: CreateTemplateData
  ): TemplateItem => {
    const now = new Date().toISOString();
    const newTemplate: TemplateItem = {
      id: generateId(),
      ...data,
      createdAt: now,
      updatedAt: now,
    };

    try {
      const currentTemplates = loadTemplates();
      const updatedTemplates = [newTemplate, ...currentTemplates];
      saveTemplates(updatedTemplates);
      
      setError(null);
      return newTemplate;
    } catch (err: any) {
      const errorMessage = 'Failed to create template';
      setError(errorMessage);
      console.error('Failed to create template:', err);
      throw err;
    }
  }, [loadTemplates, saveTemplates]);

  const getTemplate = useCallback((templateId: string): TemplateItem | null => {
    try {
      const currentTemplates = templates.length > 0 ? templates : loadTemplates();
      const template = currentTemplates.find((t: TemplateItem) => t.id === templateId);
      return template || null;
    } catch (err: any) {
      const errorMessage = 'Failed to get template';
      setError(errorMessage);
      console.error('Failed to get template:', err);
      return null;
    }
  }, [templates, loadTemplates]);

  const deleteTemplate = useCallback((templateId: string): boolean => {
    try {
      const currentTemplates = templates.length > 0 ? templates : loadTemplates();
      const updatedTemplates = currentTemplates.filter((t: TemplateItem) => t.id !== templateId);
      saveTemplates(updatedTemplates);
      
      setError(null);
      return true;
    } catch (err: any) {
      const errorMessage = 'Failed to delete template';
      setError(errorMessage);
      console.error('Failed to delete template:', err);
      return false;
    }
  }, [templates, loadTemplates, saveTemplates]);

  const createTemplateFromLesson = useCallback((
    lessonContent: string,
    selectedStandard: StandardRecord | null,
    lessonSettings: {
      grade: string;
      strand: string;
      objective?: string | null;
      lessonContext: string;
      lessonDuration: string;
      classSize: string;
    },
    templateName: string,
    templateDescription: string
  ): TemplateItem => {
    return createTemplate({
      name: templateName,
      description: templateDescription,
      content: lessonContent,
      grade: lessonSettings.grade,
      strand: lessonSettings.strand,
      standardId: selectedStandard?.id,
      standardCode: selectedStandard?.code,
      standardTitle: selectedStandard?.title,
      objective: lessonSettings.objective || undefined,
      lessonDuration: lessonSettings.lessonDuration,
      classSize: lessonSettings.classSize,
    });
  }, [createTemplate]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Load templates on mount
  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  return {
    templates,
    isLoading,
    error,
    templateCount,
    loadTemplates,
    getTemplate,
    createTemplate,
    createTemplateFromLesson,
    deleteTemplate,
    clearError,
  };
}