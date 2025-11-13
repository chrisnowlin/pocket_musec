import type {
  Citation,
  EnhancedCitation,
  FileCitation,
  CitationServiceResponse,
  FileMetadata
} from '../types/fileStorage';
import { formatCitationFileInfo } from '../types/fileStorage';
import { ingestionService } from './ingestionService';
import {
  handleCitationError,
  createFallbackCitation,
  validateCitation,
  sanitizeCitationText,
  normalizeCitations,
  debounce
} from '../utils/citationUtils';

class CitationService {
  private baseUrl = (import.meta.env?.VITE_API_BASE_URL as string) || '/api';
  private fileMetadataCache = new Map<string, FileMetadata>();
  private citationCache = new Map<string, EnhancedCitation[]>();

  /**
   * Fetch citations for a lesson with enhanced file information
   */
  async getLessonCitations(lessonId: string): Promise<CitationServiceResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/citations/lesson/${lessonId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch citations: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Failed to fetch citations');
      }

      // Validate and normalize citations
      const rawCitations = data.citations || [];
      const validCitations = rawCitations.filter(validateCitation) as Citation[];
      const normalizedCitations = normalizeCitations(validCitations);
      const citationObjects = normalizedCitations.filter(c => typeof c === 'object') as Citation[];

      // Enhance citations with file metadata
      const enhancedCitations = await this.enhanceCitationsWithFileData(citationObjects);

      return {
        success: true,
        citations: citationObjects,
        enhanced_citations: enhancedCitations,
      };
    } catch (error) {
      const errorInfo = handleCitationError(error instanceof Error ? error : new Error('Unknown error'), 'getLessonCitations');
      return {
        success: false,
        error: errorInfo.message,
      };
    }
  }

  /**
   * Get citation by ID with file information
   */
  async getCitationById(citationId: string): Promise<CitationServiceResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/citations/${citationId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch citation: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Failed to fetch citation');
      }

      // Enhance citation with file metadata
      const enhancedCitations = await this.enhanceCitationsWithFileData([data.citation]);

      return {
        success: true,
        citations: [data.citation],
        enhanced_citations: enhancedCitations,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch citation',
      };
    }
  }

  /**
   * Get citations by file ID
   */
  async getCitationsByFileId(fileId: string): Promise<CitationServiceResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/citations/file/${fileId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch file citations: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Failed to fetch file citations');
      }

      // Enhance citations with file metadata
      const enhancedCitations = await this.enhanceCitationsWithFileData(data.citations || []);

      return {
        success: true,
        citations: data.citations,
        enhanced_citations: enhancedCitations,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch file citations',
      };
    }
  }

  /**
   * Download file from citation
   */
  async downloadCitationFile(fileId: string, filename?: string): Promise<void> {
    try {
      const blob = await ingestionService.downloadFile(fileId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `file_${fileId}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Failed to download file');
    }
  }

  /**
   * Enhance citations with file metadata
   */
  private async enhanceCitationsWithFileData(citations: Citation[]): Promise<EnhancedCitation[]> {
    const enhancedCitations: EnhancedCitation[] = [];

    for (const citation of citations) {
      let fileMetadata: FileMetadata | undefined;

      // Try to get file metadata if file_id is present
      if (citation.file_id) {
        fileMetadata = await this.getFileMetadata(citation.file_id);
      }

      // Create enhanced citation
      const fileInfo = formatCitationFileInfo(citation, fileMetadata);
      
      const enhancedCitation: EnhancedCitation = {
        id: citation.id,
        citation_number: citation.citation_number,
        source_title: citation.source_title,
        source_type: citation.source_type,
        citation_text: citation.citation_text,
        page_number: citation.page_number,
        excerpt: citation.excerpt,
        file_metadata: fileInfo.file_metadata,
        is_file_available: fileInfo.is_file_available || false,
        can_download: fileInfo.can_download || false,
        formatted_date: fileInfo.formatted_date,
        relative_time: fileInfo.relative_time,
      };

      enhancedCitations.push(enhancedCitation);
    }

    return enhancedCitations;
  }

  /**
   * Get file metadata with caching
   */
  private async getFileMetadata(fileId: string): Promise<FileMetadata | undefined> {
    // Check cache first
    if (this.fileMetadataCache.has(fileId)) {
      return this.fileMetadataCache.get(fileId);
    }

    try {
      const response = await ingestionService.getFileMetadata(fileId);
      
      if (response.success && response.file) {
        // Cache the result
        this.fileMetadataCache.set(fileId, response.file);
        return response.file;
      }
    } catch (error) {
      console.warn(`Failed to fetch file metadata for ${fileId}:`, error);
    }

    return undefined;
  }

  /**
   * Get cached enhanced citations for a lesson
   */
  getCachedCitations(lessonId: string): EnhancedCitation[] | null {
    return this.citationCache.get(lessonId) || null;
  }

  /**
   * Cache enhanced citations for a lesson
   */
  cacheCitations(lessonId: string, citations: EnhancedCitation[]): void {
    this.citationCache.set(lessonId, citations);
  }

  /**
   * Clear citation cache for a lesson
   */
  clearCitationCache(lessonId?: string): void {
    if (lessonId) {
      this.citationCache.delete(lessonId);
    } else {
      this.citationCache.clear();
    }
  }

  /**
   * Clear file metadata cache
   */
  clearFileMetadataCache(fileId?: string): void {
    if (fileId) {
      this.fileMetadataCache.delete(fileId);
    } else {
      this.fileMetadataCache.clear();
    }
  }

  /**
   * Get download URL for a file (for direct linking)
   */
  getDownloadUrl(fileId: string): string {
    return `${this.baseUrl}/ingestion/files/${fileId}/download`;
  }

  /**
   * Handle legacy citation format (string array)
   * Convert string citations to basic Citation objects
   */
  handleLegacyCitations(legacyCitations: string[]): Citation[] {
    return legacyCitations.map((citation, index) => ({
      id: `legacy-${index}`,
      lesson_id: 'unknown',
      source_type: 'document' as const,
      source_id: citation,
      source_title: citation,
      citation_text: citation,
      citation_number: index + 1,
      created_at: new Date().toISOString(),
    }));
  }

  /**
   * Create basic enhanced citations from legacy format
   */
  handleLegacyEnhancedCitations(legacyCitations: string[]): EnhancedCitation[] {
    return legacyCitations.map((citation, index) => ({
      id: `legacy-${index}`,
      citation_number: index + 1,
      source_title: citation,
      source_type: 'document',
      citation_text: citation,
      is_file_available: false,
      can_download: false,
    }));
  }

  /**
   * Batch download multiple files from citations
   */
  async downloadMultipleCitationFiles(citations: EnhancedCitation[]): Promise<void> {
    const downloadableCitations = citations.filter(
      c => c.is_file_available && c.can_download && c.file_metadata
    );

    if (downloadableCitations.length === 0) {
      throw new Error('No files available for download');
    }

    // Download files with a small delay between each to avoid overwhelming the server
    for (const citation of downloadableCitations) {
      if (citation.file_metadata) {
        try {
          await this.downloadCitationFile(
            citation.file_metadata.file_id,
            citation.file_metadata.original_filename
          );
          // Small delay between downloads
          await new Promise(resolve => setTimeout(resolve, 500));
        } catch (error) {
          console.error(`Failed to download ${citation.file_metadata.original_filename}:`, error);
          // Continue with other files even if one fails
        }
      }
    }
  }
}

export const citationService = new CitationService();