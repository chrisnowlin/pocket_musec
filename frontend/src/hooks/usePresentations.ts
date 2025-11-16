import { useState, useCallback } from 'react';
import { apiClient } from '../lib/api';
import type { 
  PresentationDocument, 
  PresentationSummary, 
  PresentationExport,
  PresentationGenerationRequest,
  PresentationStatus 
} from '../types/presentations';

export function usePresentations() {
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isExporting, setIsExporting] = useState<boolean>(false);

  const loadPresentations = useCallback(async (lessonId?: string): Promise<PresentationSummary[]> => {
    setError(null);
    
    try {
      const url = lessonId ? `/presentations?lesson_id=${lessonId}` : '/presentations';
      const result = await apiClient.get<PresentationSummary[]>(url);
      
      if (result.ok) {
        return result.data;
      } else {
        setError((result as any).message || 'Failed to load presentations');
        return [];
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load presentations';
      setError(errorMessage);
      return [];
    }
  }, []);

  const getPresentation = useCallback(async (presentationId: string): Promise<PresentationDocument | null> => {
    setError(null);
    
    try {
      const result = await apiClient.get<PresentationDocument>(`/presentations/${presentationId}`);
      
      if (result.ok) {
        return result.data;
      } else {
        setError((result as any).message || 'Failed to load presentation');
        return null;
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load presentation';
      setError(errorMessage);
      return null;
    }
  }, []);

  const generatePresentation = useCallback(async (
    lessonId: string, 
    options?: PresentationGenerationRequest['options']
  ): Promise<PresentationSummary | null> => {
    setIsGenerating(true);
    setError(null);
    
    try {
      const payload: PresentationGenerationRequest = {
        lesson_id: lessonId,
        options
      };
      
      const result = await apiClient.post<PresentationSummary>('/presentations/generate', payload);
      
      if (result.ok) {
        return result.data;
      } else {
        setError((result as any).message || 'Failed to generate presentation');
        return null;
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to generate presentation';
      setError(errorMessage);
      return null;
    } finally {
      setIsGenerating(false);
    }
  }, []);

  const getPresentationStatus = useCallback(async (presentationId: string): Promise<PresentationStatus | null> => {
    setError(null);
    
    try {
      const result = await apiClient.get<{ status: PresentationStatus }>(`/presentations/${presentationId}/status`);
      
      if (result.ok) {
        return result.data.status;
      } else {
        setError((result as any).message || 'Failed to get presentation status');
        return null;
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to get presentation status';
      setError(errorMessage);
      return null;
    }
  }, []);

  const deletePresentation = useCallback(async (presentationId: string): Promise<boolean> => {
    setError(null);
    
    try {
      const result = await apiClient.delete(`/presentations/${presentationId}`);
      
      if (result.ok) {
        return true;
      } else {
        setError((result as any).message || 'Failed to delete presentation');
        return false;
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to delete presentation';
      setError(errorMessage);
      return false;
    }
  }, []);

  const exportPresentation = useCallback(async (
    presentationId: string, 
    format: 'json' | 'markdown'
  ): Promise<PresentationExport | null> => {
    setIsExporting(true);
    setError(null);
    
    try {
      const result = await apiClient.post<PresentationExport>(`/presentations/${presentationId}/export`, { format });
      
      if (result.ok) {
        return result.data;
      } else {
        setError((result as any).message || 'Failed to export presentation');
        return null;
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to export presentation';
      setError(errorMessage);
      return null;
    } finally {
      setIsExporting(false);
    }
  }, []);

  const downloadExport = useCallback(async (exportUrl: string, filename: string): Promise<void> => {
    try {
      const response = await fetch(exportUrl);
      if (!response.ok) {
        throw new Error('Failed to download export');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to download export';
      setError(errorMessage);
    }
  }, []);

  const refreshPresentation = useCallback(async (presentationId: string): Promise<PresentationDocument | null> => {
    setError(null);
    
    try {
      const result = await apiClient.post<PresentationDocument>(`/presentations/${presentationId}/refresh`);
      
      if (result.ok) {
        return result.data;
      } else {
        setError((result as any).message || 'Failed to refresh presentation');
        return null;
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to refresh presentation';
      setError(errorMessage);
      return null;
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Helper function to get status display text
  const getStatusDisplay = useCallback((status: PresentationStatus): string => {
    switch (status) {
      case 'pending':
        return 'Pending';
      case 'generating':
        return 'Generating...';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      default:
        return 'Unknown';
    }
  }, []);

  // Helper function to check if status allows viewing
  const canViewPresentation = useCallback((status: PresentationStatus): boolean => {
    return status === 'completed';
  }, []);

  // Helper function to check if status allows generation
  const canGeneratePresentation = useCallback((status?: PresentationStatus): boolean => {
    return !status || status === 'failed' || status === 'completed';
  }, []);

  return {
    // State
    error,
    isGenerating,
    isExporting,
    
    // API methods
    loadPresentations,
    getPresentation,
    generatePresentation,
    getPresentationStatus,
    deletePresentation,
    exportPresentation,
    downloadExport,
    refreshPresentation,
    clearError,
    
    // Helper methods
    getStatusDisplay,
    canViewPresentation,
    canGeneratePresentation,
  };
}

export default usePresentations;