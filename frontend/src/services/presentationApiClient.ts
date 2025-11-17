import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { API_BASE_URL } from '../lib/api';
import { presentationErrorHandler, PresentationError, PresentationErrorCode } from '../errors/presentationErrors';
import { pollJobStatus as pollJobStatusUtil } from '../lib/streaming';

/**
 * Enhanced API client with automatic error handling and retry logic
 */
export class PresentationApiClient {
  private client: AxiosInstance;
  private errorHandler = presentationErrorHandler;
  private retryConfigs: Map<string, { maxRetries: number; baseDelay: number }> = new Map();

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      timeout: 30000, // 30 seconds default timeout
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
    this.setupRetryConfigs();
  }

  private setupInterceptors(): void {
    // Request interceptor for logging and authentication
    this.client.interceptors.request.use(
      (config) => {
        console.debug(`API Request: ${config.method?.toUpperCase()} ${config.url}`, {
          params: config.params,
          hasData: !!config.data,
        });

        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
      },
      (error) => {
        console.error('Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        console.debug(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean; _retryKey?: string };

        console.error('API Error:', {
          url: originalRequest.url,
          method: originalRequest.method,
          status: error.response?.status,
          message: error.message,
        });

        // Convert to structured error
        const structuredError = this.errorHandler.handleError(error, {
          url: originalRequest.url,
          method: originalRequest.method,
          hasData: !!originalRequest.data,
        });

        if (!structuredError) {
          return Promise.reject(error);
        }

        // Check if we should retry this request
        if (structuredError.error.retry_recommended && !originalRequest._retry) {
          const retryKey = this.getRetryKey(originalRequest);
          const retryConfig = this.retryConfigs.get(retryKey);

          if (retryConfig && retryConfig.maxRetries > 0) {
            originalRequest._retry = true;
            originalRequest._retryKey = retryKey;

            try {
              await this.errorHandler.scheduleRetry(
                retryKey,
                retryConfig.maxRetries,
                retryConfig.baseDelay
              );

              console.log(`Retrying request: ${originalRequest.method} ${originalRequest.url}`);
              return this.client(originalRequest);
            } catch (retryError) {
              console.error('Retry failed:', retryError);
            }
          }
        }

        // Return structured error to calling code
        const enhancedError = {
          ...error,
          structuredError,
        };

        return Promise.reject(enhancedError);
      }
    );
  }

  private setupRetryConfigs(): void {
    // Configure retry behavior for different endpoints
    this.retryConfigs.set('/generate', { maxRetries: 2, baseDelay: 5000 });
    this.retryConfigs.set('/jobs', { maxRetries: 1, baseDelay: 2000 });
    this.retryConfigs.set('/export', { maxRetries: 1, baseDelay: 3000 });
  }

  private getRetryKey(config: AxiosRequestConfig): string {
    // Create a unique key for retry tracking based on URL and method
    const urlPath = new URL(config.url || '', this.client.defaults.baseURL).pathname;
    return `${config.method}:${urlPath}`;
  }

  /**
   * Enhanced presentation generation with progress tracking
   */
  async generatePresentation(
    lessonId: string,
    options: {
      style?: string;
      useLlmPolish?: boolean;
      timeoutSeconds?: number;
      priority?: string;
      maxRetries?: number;
    } = {}
  ) {
    return this.withProgress(
      async () => {
        const response = await this.client.post('/generate', {
          lessonId: lessonId,
          style: options.style || 'default',
          useLlmPolish: options.useLlmPolish ?? true,
          timeoutSeconds: options.timeoutSeconds || 30,
          priority: options.priority || 'normal',
          maxRetries: options.maxRetries || 2,
        });

        const data: any = response.data || {};

        return {
          accepted: true,
          jobId: data.job_id,
          status: data.status || 'pending',
          message: data.message || 'Presentation generation started',
          estimatedDuration: this.estimateGenerationDuration(options),
        };
      },
      ' Generating presentation...'
    );
  }

  /**
   * Poll job status using standardized streaming utilities
   */
  async pollJobStatus(
    jobId: string,
    options: {
      maxAttempts?: number;
      initialDelay?: number;
      maxDelay?: number;
      onProgress?: (status: any, attempt: number) => void;
      onComplete?: (result: any) => void;
    } = {}
  ) {
    const {
      maxAttempts = 60, // 10 minutes with 10s max delay
      initialDelay = 1000,
      maxDelay = 10000,
      onProgress,
      onComplete,
    } = options;

    try {
      const result = await pollJobStatusUtil(jobId, this.client, {
        maxAttempts,
        initialDelay,
        maxDelay,
        onProgress: (status: any, attempt: number) => {
          if (onProgress) {
            // Convert envelope format to expected format for backward compatibility
            const legacyStatus = {
              ...status,
              progress: status.progress?.completion_percentage || 0,
              message: status.progress?.step || status.status,
              error: status.error?.message,
              error_code: status.error?.code,
            };
            onProgress(legacyStatus, attempt);
          }
        },
        onError: (error: any) => {
          // Convert to structured error format
          if (error.message) {
            const structuredError = this.errorHandler.handleError({
              response: {
                status: 500,
                data: {
                  error: {
                    code: 'job_failed',
                    user_message: error.message,
                    technical_message: error.message,
                    retry_recommended: true,
                    escalation_required: false,
                  },
                },
              },
            });
            throw { structuredError };
          }
        },
      });

      if (onComplete && result.status) {
        // Convert envelope format to expected format for backward compatibility
        const legacyStatus = {
          ...result.status,
          progress: result.status.progress?.completion_percentage || 0,
          message: result.status.progress?.step || result.status.status,
          error: result.status.error?.message,
          error_code: result.status.error?.code,
        };
        onComplete(legacyStatus);
      }

      return result;

    } catch (error: any) {
      if (error.structuredError) {
        throw error;
      }

      // Fallback error handling
      throw {
        structuredError: this.errorHandler.handleError({
          response: {
            status: 500,
            data: {
              error: {
                code: PresentationErrorCode.JOB_TIMEOUT,
                user_message: error.message || 'Job polling failed',
                technical_message: error.message,
                retry_recommended: true,
                retry_after_seconds: 30,
                escalation_required: false,
              },
            },
          },
        }),
      };
    }
  }

  /**
   * Export presentation with progress tracking and fallback options
   */
  async exportPresentation(
    presentationId: string,
    format: 'json' | 'markdown' | 'pptx' | 'pdf',
    options: {
      fallbackFormats?: string[];
      onProgress?: (format: string, progress: number) => void;
    } = {}
  ): Promise<Blob> {
    const { fallbackFormats = ['json', 'markdown'], onProgress } = options;

    const tryExport = async (targetFormat: string): Promise<Blob> => {
      try {
        if (onProgress) {
          onProgress(targetFormat, 25);
        }

        const response = await this.client.get(
          `/${presentationId}/export`,
          {
            params: { format: targetFormat },
            responseType: 'blob',
          }
        );

        if (onProgress) {
          onProgress(targetFormat, 100);
        }

        return response.data;
      } catch (error: any) {
        if (error.structuredError?.error?.code?.includes(`${targetFormat}_failed`)) {
          throw error; // Re-throw format-specific errors
        }
        throw { structuredError: error.structuredError || this.errorHandler.handleError(error) };
      }
    };

    // Try requested format first
    try {
      return await tryExport(format);
    } catch (error: any) {
      console.warn(`Export to ${format} failed:`, error.structuredError?.error?.user_message);

      // Try fallback formats
      for (const fallbackFormat of fallbackFormats) {
        if (fallbackFormat === format) continue; // Skip same format

        try {
          console.log(`Trying fallback export to ${fallbackFormat}...`);
          return await tryExport(fallbackFormat);
        } catch (fallbackError: any) {
          console.warn(`Fallback export to ${fallbackFormat} also failed:`, fallbackError.structuredError?.error?.user_message);
        }
      }

      // All formats failed, return the original error
      throw error;
    }
  }

  /**
   * Generic method with progress indicator support
   */
  private async withProgress<T>(operation: () => Promise<T>, message: string): Promise<T> {
    // This could integrate with a global progress indicator system
    console.log(`Progress: ${message}`);

    try {
      const result = await operation();
      console.log('Progress: Operation completed successfully');
      return result;
    } catch (error: any) {
      if (error.structuredError) {
        throw error;
      }

      // Convert unstructured errors
      const structuredError = this.errorHandler.handleError(error);
      throw { structuredError };
    } finally {
      console.log('Progress: Operation finished');
    }
  }

  private wait(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private estimateGenerationDuration(options: {
    useLlmPolish?: boolean;
    timeoutSeconds?: number;
  }): number {
    const baseTime = 10; // Base generation time in seconds
    const polishTime = options.useLlmPolish ? 20 : 0;
    const safetyMargin = 1.5; // 50% safety margin

    return Math.ceil((baseTime + polishTime) * safetyMargin);
  }

  /**
   * Cancel a running job
   */
  async cancelJob(jobId: string): Promise<void> {
    try {
      await this.client.delete(`/jobs/${jobId}`);
    } catch (error: any) {
      throw { structuredError: this.errorHandler.handleError(error) };
    }
  }

  /**
    * Get all jobs
    */
  async getJobs(): Promise<any[]> {
    try {
      const response = await this.client.get('/jobs');
      return response.data;
    } catch (error: any) {
      throw { structuredError: this.errorHandler.handleError(error) };
    }
  }

  /**
    * Get presentation with error handling for missing files
    */
  async getPresentation(presentationId: string): Promise<any> {
    try {
      const response = await this.client.get(`/${presentationId}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        throw {
          structuredError: this.errorHandler.handleError({
            response: {
              status: 404,
              data: {
                error: {
                  code: PresentationErrorCode.LESSON_NOT_FOUND,
                  user_message: 'The presentation you requested was not found. It may have been deleted or the link is incorrect.',
                  technical_message: `Presentation ${presentationId} not found`,
                  retry_recommended: false,
                  escalation_required: false,
                },
              },
            },
          }),
        };
      }
      throw { structuredError: this.errorHandler.handleError(error) };
    }
  }
}

// Create singleton instance
const normalizedBase = (() => {
  const base = (API_BASE_URL || '/api').replace(/\/$/, '');
  return `${base}/presentations`;
})();

const apiClient = new PresentationApiClient(normalizedBase);

export default apiClient;
