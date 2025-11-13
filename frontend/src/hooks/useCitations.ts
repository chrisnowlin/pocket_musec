import { useState, useEffect, useCallback } from 'react';
import type { EnhancedCitation, Citation, CitationServiceResponse } from '../types/fileStorage';
import { citationService } from '../services/citationService';

interface UseCitationsOptions {
  lessonId?: string;
  autoLoad?: boolean;
  enableCache?: boolean;
}

interface UseCitationsReturn {
  citations: EnhancedCitation[];
  loading: boolean;
  error: string;
  
  // Actions
  loadCitations: (lessonId: string) => Promise<void>;
  refreshCitations: () => Promise<void>;
  downloadFile: (fileId: string, filename: string) => Promise<void>;
  downloadAllFiles: () => Promise<void>;
  clearCache: () => void;
  
  // Computed values
  hasCitations: boolean;
  availableCitationsCount: number;
  downloadableCitationsCount: number;
  downloadingFileIds: string[];
  isDownloading: boolean;
}

export function useCitations(options: UseCitationsOptions = {}): UseCitationsReturn {
  const {
    lessonId: initialLessonId,
    autoLoad = true,
    enableCache = true,
  } = options;

  const [citations, setCitations] = useState<EnhancedCitation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [currentLessonId, setCurrentLessonId] = useState<string | undefined>(initialLessonId);
  const [downloadingFileIds, setDownloadingFileIds] = useState<string[]>([]);

  const loadCitations = useCallback(async (lessonId: string) => {
    try {
      setLoading(true);
      setError('');
      
      // Try cache first if enabled
      if (enableCache) {
        const cachedCitations = citationService.getCachedCitations(lessonId);
        if (cachedCitations) {
          setCitations(cachedCitations);
          setCurrentLessonId(lessonId);
          return;
        }
      }

      // Fetch from service
      const response: CitationServiceResponse = await citationService.getLessonCitations(lessonId);
      
      if (response.success && response.enhanced_citations) {
        setCitations(response.enhanced_citations);
        
        // Cache the results if enabled
        if (enableCache) {
          citationService.cacheCitations(lessonId, response.enhanced_citations);
        }
        
        setCurrentLessonId(lessonId);
      } else {
        setError(response.error || 'Failed to load citations');
        setCitations([]);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load citations';
      setError(errorMessage);
      setCitations([]);
    } finally {
      setLoading(false);
    }
  }, [enableCache]);

  const refreshCitations = useCallback(async () => {
    if (currentLessonId) {
      // Clear cache for this lesson to force refresh
      if (enableCache) {
        citationService.clearCitationCache(currentLessonId);
      }
      await loadCitations(currentLessonId);
    }
  }, [currentLessonId, enableCache, loadCitations]);

  const downloadFile = useCallback(async (fileId: string, filename: string) => {
    try {
      setDownloadingFileIds(prev => [...prev, fileId]);
      await citationService.downloadCitationFile(fileId, filename);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to download file';
      setError(errorMessage);
      throw err;
    } finally {
      setDownloadingFileIds(prev => prev.filter(id => id !== fileId));
    }
  }, []);

  const downloadAllFiles = useCallback(async () => {
    const downloadableCitations = citations.filter(c => c.is_file_available && c.can_download);
    
    if (downloadableCitations.length === 0) {
      setError('No files available for download');
      return;
    }

    try {
      const fileIds = downloadableCitations.map(c => c.file_metadata?.file_id).filter(Boolean) as string[];
      setDownloadingFileIds(prev => [...prev, ...fileIds]);
      
      await citationService.downloadMultipleCitationFiles(downloadableCitations);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to download files';
      setError(errorMessage);
      throw err;
    } finally {
      setDownloadingFileIds([]);
    }
  }, [citations]);

  const clearCache = useCallback(() => {
    if (enableCache) {
      if (currentLessonId) {
        citationService.clearCitationCache(currentLessonId);
      } else {
        citationService.clearCitationCache();
      }
    }
  }, [enableCache, currentLessonId]);

  // Auto-load citations when lessonId changes
  useEffect(() => {
    if (autoLoad && initialLessonId) {
      loadCitations(initialLessonId);
    }
  }, [autoLoad, initialLessonId, loadCitations]);

  // Computed values
  const hasCitations = citations.length > 0;
  const availableCitationsCount = citations.filter(c => c.is_file_available).length;
  const downloadableCitationsCount = citations.filter(c => c.is_file_available && c.can_download).length;
  const isDownloading = downloadingFileIds.length > 0;

  return {
    citations,
    loading,
    error,
    
    loadCitations,
    refreshCitations,
    downloadFile,
    downloadAllFiles,
    clearCache,
    
    hasCitations,
    availableCitationsCount,
    downloadableCitationsCount,
    downloadingFileIds,
    isDownloading,
  };
}

// Hook for managing a single citation
export function useCitation(citationId?: string) {
  const [citation, setCitation] = useState<EnhancedCitation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadCitation = useCallback(async (id: string) => {
    try {
      setLoading(true);
      setError('');
      
      const response: CitationServiceResponse = await citationService.getCitationById(id);
      
      if (response.success && response.enhanced_citations && response.enhanced_citations.length > 0) {
        setCitation(response.enhanced_citations[0]);
      } else {
        setError(response.error || 'Failed to load citation');
        setCitation(null);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load citation';
      setError(errorMessage);
      setCitation(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (citationId) {
      loadCitation(citationId);
    }
  }, [citationId, loadCitation]);

  return {
    citation,
    loading,
    error,
    loadCitation,
  };
}

// Hook for handling legacy citation format (string arrays)
export function useLegacyCitations(legacyCitations: string[] = []) {
  const [enhancedCitations, setEnhancedCitations] = useState<EnhancedCitation[]>([]);

  useEffect(() => {
    const enhanced = citationService.handleLegacyEnhancedCitations(legacyCitations);
    setEnhancedCitations(enhanced);
  }, [legacyCitations]);

  return {
    enhancedCitations,
    hasLegacyCitations: legacyCitations.length > 0,
  };
}