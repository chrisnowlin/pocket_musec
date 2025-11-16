import { useState, useCallback } from 'react';
import { apiClient } from '../lib/api';
import type {
  PresentationDetail,
  PresentationSummary,
  PresentationGenerateResponse,
  PresentationJobInfo,
  PresentationStatus,
} from '../types/presentations';

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export interface GenerateOptions {
  style?: string;
  use_llm_polish?: boolean;
  timeout_seconds?: number;
}

export function usePresentations() {
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const getLessonPresentationStatus = useCallback(
    async (lessonId: string): Promise<PresentationSummary | null> => {
      setError(null);
      const result = await apiClient.get<PresentationSummary>(
        `/presentations/lessons/${lessonId}/latest`
      );
      if (!result.ok) {
        if (result.status && result.status !== 404) {
          setError(result.message || 'Failed to fetch presentation status');
        }
        return null;
      }
      return result.data;
    },
    []
  );

  const listLessonPresentations = useCallback(
    async (lessonId: string, includeStale = false): Promise<PresentationSummary[]> => {
      setError(null);
      const result = await apiClient.get<PresentationSummary[]>(
        `/presentations/lessons/${lessonId}/presentations`,
        { params: { include_stale: includeStale } }
      );
      if (!result.ok) {
        setError(result.message || 'Failed to list presentations');
        return [];
      }
      return result.data;
    },
    []
  );

  const getPresentation = useCallback(
    async (presentationId: string): Promise<PresentationDetail | null> => {
      setError(null);
      const result = await apiClient.get<PresentationDetail>(
        `/presentations/${presentationId}`
      );
      if (!result.ok) {
        setError(result.message || 'Failed to load presentation');
        return null;
      }
      return result.data;
    },
    []
  );

  const generatePresentation = useCallback(
    async (lessonId: string, options?: GenerateOptions): Promise<PresentationGenerateResponse | null> => {
      setIsGenerating(true);
      setError(null);
      try {
        const payload = {
          lesson_id: lessonId,
          style: options?.style ?? 'default',
          use_llm_polish: options?.use_llm_polish ?? true,
          timeout_seconds: options?.timeout_seconds ?? 30,
        };
        const result = await apiClient.post<PresentationGenerateResponse>(
          '/presentations/generate',
          payload
        );
        if (!result.ok) {
          setError(result.message || 'Failed to start presentation generation');
          return null;
        }
        return result.data;
      } catch (err: any) {
        setError(err?.message || 'Failed to start presentation generation');
        return null;
      } finally {
        setIsGenerating(false);
      }
    },
    []
  );

  const getJobStatus = useCallback(
    async (jobId: string): Promise<PresentationJobInfo | null> => {
      setError(null);
      const result = await apiClient.get<PresentationJobInfo>(
        `/presentations/jobs/${jobId}`
      );
      if (!result.ok) {
        setError(result.message || 'Failed to fetch job status');
        return null;
      }
      return result.data;
    },
    []
  );

  const waitForJobCompletion = useCallback(
    async (
      jobId: string,
      lessonId: string,
      {
        pollIntervalMs = 2000,
        maxAttempts = 30,
      }: { pollIntervalMs?: number; maxAttempts?: number } = {}
    ): Promise<PresentationSummary | null> => {
      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        const job = await getJobStatus(jobId);
        if (!job) {
          return null;
        }

        if (job.status === 'completed') {
          return await getLessonPresentationStatus(lessonId);
        }

        if (job.status === 'failed') {
          setError(job.error || 'Presentation generation failed');
          return null;
        }

        await sleep(pollIntervalMs);
      }

      setError('Timed out while waiting for presentation generation');
      return null;
    },
    [getJobStatus, getLessonPresentationStatus]
  );

  const exportPresentation = useCallback(
    async (presentationId: string, format: 'json' | 'markdown' | 'pptx' | 'pdf'): Promise<void> => {
      setIsExporting(true);
      setError(null);
      try {
        const response = await fetch(
          `/api/presentations/${presentationId}/export?format=${format}`
        );
        if (!response.ok) {
          throw new Error('Failed to export presentation');
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const extension = format === 'markdown' ? 'md' : format;
        const filename = `presentation_${presentationId}.${extension}`;
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = filename;
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
        window.URL.revokeObjectURL(url);
      } catch (err: any) {
        setError(err?.message || 'Failed to export presentation');
      } finally {
        setIsExporting(false);
      }
    },
    []
  );

  const clearError = useCallback(() => setError(null), []);

  const getStatusDisplay = useCallback((status: PresentationStatus): string => {
    switch (status) {
      case 'complete':
        return 'Ready';
      case 'pending':
        return 'Pending';
      case 'error':
        return 'Error';
      case 'stale':
        return 'Stale';
      default:
        return 'Unknown';
    }
  }, []);

  const canViewPresentation = useCallback(
    (status?: PresentationStatus): boolean => status === 'complete',
    []
  );

  return {
    error,
    isGenerating,
    isExporting,
    generatePresentation,
    waitForJobCompletion,
    getLessonPresentationStatus,
    listLessonPresentations,
    getPresentation,
    getJobStatus,
    exportPresentation,
    clearError,
    getStatusDisplay,
    canViewPresentation,
  };
}

export default usePresentations;
