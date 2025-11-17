export interface EmbeddingStats {
  standard_embeddings: number;
  objective_embeddings: number;
  embedding_dimension: number;
}

export interface EmbeddingGenerateRequest {
  force?: boolean;
  batch_size?: number;
}

export interface EmbeddingGenerateResponse {
  success: number;
  failed: number;
  skipped: number;
  message: string;
}

export interface SemanticSearchRequest {
  query: string;
  gradeLevel?: string;
  strandCode?: string;
  limit?: number;
  threshold?: number;
  offset?: number;
}

export interface SemanticSearchResult {
  standard_id: string;
  gradeLevel: string;
  strandCode: string;
  strandName: string;
  standard_text: string;
  similarity: number;
}

export interface SemanticSearchResponse {
  results: SemanticSearchResult[];
  total_count: number;
  limit: number;
  offset: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface PreparedTexts {
  standards: string[];
  objectives: string[];
}

export interface ShowTextResponse {
  text: string;
  item_id: string;
  item_type: string;
}

export interface GenerationProgress {
  status: 'idle' | 'running' | 'completed' | 'error';
  progress: number;
  message: string;
}

export interface UsageStats {
  total_searches: number;
  total_generations: number;
  searches_this_week: number;
  generations_this_week: number;
  last_search: string | null;
  last_generation: string | null;
}

export interface BatchOperationRequest {
  operation: 'regenerate' | 'delete' | 'refresh';
  filters?: Record<string, any>;
}

export interface BatchOperationResponse {
  success: number;
  failed: number;
  skipped: number;
  message: string;
}

class EmbeddingsService {
  private baseUrl = (import.meta.env?.VITE_API_BASE_URL as string) || '/api';

  // Simple in-memory cache with TTL
  private statsCache: { data: EmbeddingStats | null; timestamp: number } = {
    data: null,
    timestamp: 0
  };
  private readonly STATS_CACHE_TTL = 5 * 60 * 1000; // 5 minutes in milliseconds

  private async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private isStatsCacheValid(): boolean {
    return this.statsCache.data !== null &&
           Date.now() - this.statsCache.timestamp < this.STATS_CACHE_TTL;
  }

  private setStatsCache(data: EmbeddingStats): void {
    this.statsCache.data = data;
    this.statsCache.timestamp = Date.now();
  }

  private clearStatsCache(): void {
    this.statsCache.data = null;
    this.statsCache.timestamp = 0;
  }

  private async retryWithBackoff<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    baseDelayMs: number = 1000,
    maxDelayMs: number = 10000
  ): Promise<T> {
    let lastError: Error;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        
        // Don't retry on client errors (4xx) or specific status codes
        if (error instanceof Response && error.status >= 400 && error.status < 500) {
          throw lastError;
        }
        
        // If this is the last attempt, throw the error
        if (attempt === maxRetries) {
          throw lastError;
        }
        
        // Calculate exponential backoff delay with jitter
        const exponentialDelay = Math.min(baseDelayMs * Math.pow(2, attempt), maxDelayMs);
        const jitter = Math.random() * 0.1 * exponentialDelay; // Add 10% jitter
        const delay = exponentialDelay + jitter;
        
        console.warn(`Attempt ${attempt + 1} failed, retrying in ${Math.round(delay)}ms:`, lastError.message);
        await this.sleep(delay);
      }
    }
    
    throw lastError!;
  }

  async getEmbeddingStats(forceRefresh: boolean = false): Promise<EmbeddingStats> {
    // Check cache first unless force refresh is requested
    if (!forceRefresh && this.isStatsCacheValid() && this.statsCache.data) {
      return this.statsCache.data;
    }

    return this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/api/embeddings/stats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to get embedding stats: ${response.statusText}`);
      }

      const data = await response.json();
      this.setStatsCache(data);
      return data;
    });
  }

  async generateEmbeddings(request: EmbeddingGenerateRequest = {}): Promise<EmbeddingGenerateResponse> {
    const result = await this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/api/embeddings/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          force: request.force || false,
          batch_size: request.batch_size || 10,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate embeddings: ${response.statusText}`);
      }

      return await response.json();
    });

    // Clear stats cache after generating embeddings since stats will have changed
    this.clearStatsCache();
    return result;
  }

  async getGenerationProgress(): Promise<GenerationProgress> {
    return this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/api/embeddings/generate/progress`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to get generation progress: ${response.statusText}`);
      }

      return await response.json();
    }, 2, 500, 3000); // Fewer retries for progress polling since it's frequent
  }

  async semanticSearch(request: SemanticSearchRequest): Promise<SemanticSearchResponse> {
    return this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/api/embeddings/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: request.query,
          grade_level: request.gradeLevel,
          strand_code: request.strandCode,
          limit: request.limit || 10,
          threshold: request.threshold || 0.5,
          offset: request.offset || 0,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to search standards: ${response.statusText}`);
      }

      return await response.json();
    });
  }

  // Legacy method for backward compatibility
  async semanticSearchLegacy(request: SemanticSearchRequest): Promise<SemanticSearchResult[]> {
    const response = await this.semanticSearch(request);
    return response.results;
  }

  async clearEmbeddings(): Promise<{ message: string }> {
    const result = await this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/api/embeddings/clear`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to clear embeddings: ${response.statusText}`);
      }

      return await response.json();
    });

    // Clear stats cache after clearing embeddings since stats will have changed
    this.clearStatsCache();
    return result;
  }

  async listPreparedTexts(): Promise<PreparedTexts> {
    return this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/api/embeddings/texts`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to list prepared texts: ${response.statusText}`);
      }

      return await response.json();
    });
  }

  async showPreparedText(itemId: string, itemType: 'standard' | 'objective' = 'standard'): Promise<ShowTextResponse> {
    return this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/api/embeddings/texts/${itemId}?item_type=${itemType}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to retrieve prepared text: ${response.statusText}`);
      }

      return await response.json();
    });
  }

  async clearPreparedTexts(): Promise<{ message: string }> {
    return this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/api/embeddings/texts/clear`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to clear prepared texts: ${response.statusText}`);
      }

      return await response.json();
    });
  }

  // Helper method to poll generation progress
  async pollGenerationProgress(
    onProgress: (progress: GenerationProgress) => void,
    interval: number = 2000,
    maxAttempts: number = 60
  ): Promise<void> {
    let attempts = 0;
    
    const poll = async (): Promise<void> => {
      try {
        const progress = await this.getGenerationProgress();
        onProgress(progress);
        
        // Continue polling if still running
        if (progress.status === 'running' && attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, interval);
        }
      } catch (error) {
        console.error('Error polling generation progress:', error);
        if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, interval);
        }
      }
    };
    
    await poll();
  }

  // Helper method to generate embeddings with progress tracking
  async generateEmbeddingsWithProgress(
    request: EmbeddingGenerateRequest = {},
    onProgress?: (progress: GenerationProgress) => void
  ): Promise<EmbeddingGenerateResponse> {
    // Start generation
    const response = await this.generateEmbeddings(request);
    
    // If generation started in background, poll for progress
    if (response.message.includes('started in background') && onProgress) {
      await this.pollGenerationProgress(onProgress);
    }
    
    return response;
  }

  // Usage tracking methods
  async getUsageStats(): Promise<UsageStats> {
    return this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/api/embeddings/usage/stats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to get usage stats: ${response.statusText}`);
      }

      return await response.json();
    }, 2, 500, 2000); // Fewer retries for usage tracking
  }

  async trackSearchUsage(query: string, resultCount: number): Promise<{ message: string }> {
    const params = new URLSearchParams({
      query: query.substring(0, 100), // Limit query length
      result_count: resultCount.toString(),
    });

    const response = await fetch(`${this.baseUrl}/api/embeddings/usage/track/search?${params}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to track search usage: ${response.statusText}`);
    }

    return await response.json();
  }

  async trackGenerationUsage(
    success: number,
    failed: number,
    skipped: number
  ): Promise<{ message: string }> {
    const params = new URLSearchParams({
      success: success.toString(),
      failed: failed.toString(),
      skipped: skipped.toString(),
    });

    const response = await fetch(`${this.baseUrl}/api/embeddings/usage/track/generation?${params}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to track generation usage: ${response.statusText}`);
    }

    return await response.json();
  }

  // Export methods
  async exportStatsAsCSV(): Promise<string> {
    return this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/api/embeddings/stats/export/csv`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to export stats as CSV: ${response.statusText}`);
      }

      // Get the filename from the response headers or create a default one
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `embedding_statistics_${new Date().toISOString().split('T')[0]}.csv`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Create a download link for the blob
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      return filename;
    });
  }

  async exportStatsAsJSON(): Promise<any> {
    return this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/api/embeddings/stats/export/json`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to export stats as JSON: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Create and download JSON file
      const jsonString = JSON.stringify(data, null, 2);
      const blob = new Blob([jsonString], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `embedding_statistics_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      return data;
    });
  }

  async exportUsageAsCSV(): Promise<string> {
    return this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/api/embeddings/usage/export/csv`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to export usage as CSV: ${response.statusText}`);
      }

      // Get the filename from the response headers or create a default one
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `usage_statistics_${new Date().toISOString().split('T')[0]}.csv`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Create a download link for the blob
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      return filename;
    });
  }

  // Batch operations methods
  async executeBatchOperation(request: BatchOperationRequest): Promise<BatchOperationResponse> {
    return this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/api/embeddings/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          operation: request.operation,
          filters: request.filters || {},
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to execute batch operation: ${response.statusText}`);
      }

      return await response.json();
    });
  }

  async executeBatchOperationWithProgress(
    request: BatchOperationRequest,
    onProgress?: (progress: GenerationProgress) => void
  ): Promise<BatchOperationResponse> {
    // Start batch operation
    const response = await this.executeBatchOperation(request);
    
    // If operation started in background, poll for progress
    if (response.message.includes('started in background') && onProgress) {
      await this.pollGenerationProgress(onProgress);
    }
    
    return response;
  }
}

export const embeddingsService = new EmbeddingsService();