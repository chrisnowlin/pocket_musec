/** Comprehensive frontend error handling for presentation generation system. */

// Error types matching backend error codes
export enum PresentationErrorCode {
  LESSON_NOT_FOUND = 'lesson_not_found',
  LESSON_ACCESS_DENIED = 'lesson_access_denied',
  LESSON_INVALID_FORMAT = 'lesson_invalid_format',
  LESSON_PARSE_FAILED = 'lesson_parse_failed',
  LLM_TIMEOUT = 'llm_timeout',
  LLM_RATE_LIMITED = 'llm_rate_limited',
  LLM_UNAVAILABLE = 'llm_unavailable',
  LLM_QUOTA_EXCEEDED = 'llm_quota_exceeded',
  LLM_CONTENT_FILTERED = 'llm_content_filtered',
  LLM_INVALID_RESPONSE = 'llm_invalid_response',
  EXPORT_PPTX_FAILED = 'export_pptx_failed',
  EXPORT_PDF_FAILED = 'export_pdf_failed',
  EXPORT_JSON_FAILED = 'export_json_failed',
  EXPORT_MARKDOWN_FAILED = 'export_markdown_failed',
  EXPORT_PERMISSION_DENIED = 'export_permission_denied',
  EXPORT_STORAGE_FAILED = 'export_storage_failed',
  JOB_NOT_FOUND = 'job_not_found',
  JOB_ACCESS_DENIED = 'job_access_denied',
  JOB_TIMEOUT = 'job_timeout',
  JOB_CANCELLED = 'job_cancelled',
  JOB_ALREADY_RUNNING = 'job_already_running',
  VALIDATION_FAILED = 'validation_failed',
  INVALID_STYLE = 'invalid_style',
  INVALID_TIMEOUT = 'invalid_timeout',
  INVALID_EXPORT_FORMAT = 'invalid_export_format',
  DATABASE_ERROR = 'database_error',
  NETWORK_ERROR = 'network_error',
  PERMISSION_DENIED = 'permission_denied',
  INTERNAL_ERROR = 'internal_error',
  SERVICE_UNAVAILABLE = 'service_unavailable',
}

export interface PresentationErrorDetail {
  code: PresentationErrorCode;
  user_message: string;
  technical_message: string;
  retry_recommended: boolean;
  retry_after_seconds?: number;
  escalation_required: boolean;
  context?: Record<string, any>;
}

export interface PresentationError {
  error: PresentationErrorDetail;
  timestamp: string;
  recovery?: {
    retry_recommended: boolean;
    retry_after_seconds?: number;
    actions: string[];
  };
}

export interface ErrorRecoveryAction {
  label: string;
  action: () => Promise<void> | void;
  type: 'primary' | 'secondary' | 'danger';
}

export class PresentationErrorHandler {
  private static instance: PresentationErrorHandler;
  private retryTimeouts: Map<string, NodeJS.Timeout> = new Map();

  static getInstance(): PresentationErrorHandler {
    if (!PresentationErrorHandler.instance) {
      PresentationErrorHandler.instance = new PresentationErrorHandler();
    }
    return PresentationErrorHandler.instance;
  }

  /**
   * Handle API errors and convert them to user-friendly messages
   */
  handleError(error: any, context: Record<string, any> = {}): PresentationError | null {
    // Check if it's our structured error response
    if (error?.response?.data?.error) {
      const errorData = error.response.data;

      // Log structured error for monitoring
      this.logError(errorData, context);

      return {
        error: errorData.error,
        timestamp: errorData.timestamp,
        recovery: errorData.recovery,
      };
    }

    // Handle network/connectivity errors
    if (error.code === 'NETWORK_ERROR' || !error.response) {
      const networkError: PresentationError = {
        error: {
          code: PresentationErrorCode.NETWORK_ERROR,
          user_message: 'Unable to connect to the server. Please check your internet connection and try again.',
          technical_message: error.message || 'Network connection failed',
          retry_recommended: true,
          retry_after_seconds: 5,
          escalation_required: false,
        },
        timestamp: new Date().toISOString(),
        recovery: {
          retry_recommended: true,
          retry_after_seconds: 5,
          actions: ['Retry the operation', 'Check internet connection', 'Contact support if issue persists'],
        },
      };

      this.logError(networkError, context);
      return networkError;
    }

    // Handle HTTP status errors
    if (error.response?.status) {
      const httpError = this.createHttpError(error.response.status, error.response.data, context);
      this.logError(httpError, context);
      return httpError;
    }

    // Unknown error
    const unknownError: PresentationError = {
      error: {
        code: PresentationErrorCode.INTERNAL_ERROR,
        user_message: 'An unexpected error occurred. Please try again or contact support.',
        technical_message: error.message || 'Unknown error',
        retry_recommended: true,
        retry_after_seconds: 10,
        escalation_required: true,
      },
      timestamp: new Date().toISOString(),
      recovery: {
        retry_recommended: true,
        retry_after_seconds: 10,
        actions: ['Retry the operation', 'Refresh the page', 'Contact technical support'],
      },
    };

    this.logError(unknownError, context);
    return unknownError;
  }

  private createHttpError(status: number, data: any, context: Record<string, any>): PresentationError {
    const errorCode = this.getErrorCodeFromHttpStatus(status);
    const baseMessage = this.getBaseMessageFromHttpStatus(status);

    return {
      error: {
        code: errorCode,
        user_message: data?.error?.user_message || baseMessage,
        technical_message: data?.error?.technical_message || `HTTP ${status}: ${data?.message || 'No message'}`,
        retry_recommended: this.isRetryable(status),
        retry_after_seconds: data?.error?.retry_after_seconds || this.getDefaultRetryDelay(status),
        escalation_required: status >= 500,
      },
      timestamp: new Date().toISOString(),
      recovery: {
        retry_recommended: this.isRetryable(status),
        retry_after_seconds: data?.error?.retry_after_seconds || this.getDefaultRetryDelay(status),
        actions: this.getRecoveryActionsForStatus(status, data?.error?.code),
      },
    };
  }

  private getErrorCodeFromHttpStatus(status: number): PresentationErrorCode {
    switch (status) {
      case 400: return PresentationErrorCode.VALIDATION_FAILED;
      case 403: return PresentationErrorCode.PERMISSION_DENIED;
      case 404: return PresentationErrorCode.LESSON_NOT_FOUND;
      case 408: return PresentationErrorCode.JOB_TIMEOUT;
      case 409: return PresentationErrorCode.JOB_ALREADY_RUNNING;
      case 422: return PresentationErrorCode.LESSON_PARSE_FAILED;
      case 429: return PresentationErrorCode.LLM_RATE_LIMITED;
      case 500: return PresentationErrorCode.INTERNAL_ERROR;
      case 503: return PresentationErrorCode.SERVICE_UNAVAILABLE;
      case 507: return PresentationErrorCode.EXPORT_STORAGE_FAILED;
      default: return PresentationErrorCode.INTERNAL_ERROR;
    }
  }

  private getBaseMessageFromHttpStatus(status: number): string {
    switch (status) {
      case 400: return 'Invalid request. Please check your input and try again.';
      case 403: return 'You don\'t have permission to perform this action.';
      case 404: return 'The requested resource was not found.';
      case 408: return 'The operation timed out. Please try again.';
      case 409: return 'The operation conflicts with an existing one.';
      case 422: return 'The request data is invalid or incomplete.';
      case 429: return 'Too many requests. Please wait a moment before trying again.';
      case 500: return 'Server error occurred. Please try again later.';
      case 503: return 'The service is temporarily unavailable. Please try again later.';
      case 507: return 'Insufficient storage. Please free up space and try again.';
      default: return 'An error occurred. Please try again.';
    }
  }

  private isRetryable(status: number): boolean {
    const retryableStatuses = [408, 429, 500, 502, 503, 504, 507];
    return retryableStatuses.includes(status);
  }

  private getDefaultRetryDelay(status: number): number {
    switch (status) {
      case 429: return 60; // Rate limiting
      case 503: return 30; // Service unavailable
      case 500: return 10; // Server error
      default: return 5;
    }
  }

  private getRecoveryActionsForStatus(status: number, errorCode?: string): string[] {
    const baseActions = [
      'Retry the operation',
      'Check your inputs',
      'Contact support if the issue persists'
    ];

    switch (status) {
      case 429:
        return [
          'Wait and retry automatically',
          'Reduce request frequency',
          'Upgrade plan for higher limits'
        ];
      case 403:
        return [
          'Check your permissions',
          'Login again',
          'Contact administrator'
        ];
      case 404:
        return [
          'Verify the resource exists',
          'Check the URL',
          'Refresh page and try again'
        ];
      case 503:
        return [
          'Wait for service recovery',
          'Try alternative method',
          'Contact support for ETA'
        ];
      case 500:
        return [
          'Refresh and retry',
          'Try different parameters',
          'Report issue to support'
        ];
      default:
        return baseActions;
    }
  }

  /**
   * Get user-friendly error recovery actions
   */
  getRecoveryActions(error: PresentationError): ErrorRecoveryAction[] {
    const actions: ErrorRecoveryAction[] = [];

    if (error.recovery?.retry_recommended) {
      actions.push({
        label: 'Retry',
        action: async () => {
          if (error.recovery?.retry_after_seconds) {
            await this.wait(error.recovery.retry_after_seconds!);
          }
          // This would be implemented by the calling component
          console.log('Retrying operation...');
        },
        type: 'primary',
      });
    }

    if (error.error.code === PresentationErrorCode.LLM_UNAVAILABLE ||
        error.error.code === PresentationErrorCode.LLM_TIMEOUT) {
      actions.push({
        label: 'Try without AI',
        action: () => {
          console.log('Retrying without AI polishing...');
        },
        type: 'secondary',
      });
    }

    if (error.error.code === PresentationErrorCode.EXPORT_PPTX_FAILED ||
        error.error.code === PresentationErrorCode.EXPORT_PDF_FAILED) {
      actions.push({
        label: 'Export as JSON',
        action: () => {
          console.log('Exporting as alternative format...');
        },
        type: 'secondary',
      });
    }

    actions.push({
      label: 'Contact Support',
      action: () => {
        window.location.href = 'mailto:support@example.com?subject=Presentation Generation Error';
      },
      type: 'danger',
    });

    return actions;
  }

  /**
   * Auto-retry functionality with exponential backoff
   */
  scheduleRetry(
    key: string,
    maxRetries: number = 3,
    baseDelay: number = 1000
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      let attempt = 0;

      const retry = () => {
        if (attempt >= maxRetries) {
          reject(new Error('Max retries exceeded'));
          return;
        }

        const delay = baseDelay * Math.pow(2, attempt);
        const timeoutId = setTimeout(() => {
          attempt++;
          this.retryTimeouts.delete(key);
          resolve();
        }, delay);

        this.retryTimeouts.set(key, timeoutId);
      };

      retry();
    });
  }

  cancelRetry(key: string): void {
    const timeoutId = this.retryTimeouts.get(key);
    if (timeoutId) {
      clearTimeout(timeoutId);
      this.retryTimeouts.delete(key);
    }
  }

  private wait(seconds: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, seconds * 1000));
  }

  private logError(error: PresentationError, context: Record<string, any>): void {
    // Log to console for development
    console.error('Presentation Error:', {
      error: error.error,
      timestamp: error.timestamp,
      context,
    });

    // In production, send to monitoring service
    if (import.meta.env.PROD) {
      // Example: Send to Sentry, LogRocket, etc.
      // monitoring.captureException(error, { extra: context });
    }
  }

  /**
   * Check if error is recoverable based on its characteristics
   */
  isRecoverable(error: PresentationError): boolean {
    return error.error.retry_recommended ||
           error.error.escalation_required ||
           this.hasWorkarounds(error.error.code);
  }

  private hasWorkarounds(errorCode: PresentationErrorCode): boolean {
    const workableErrors = [
      PresentationErrorCode.LLM_TIMEOUT,
      PresentationErrorCode.LLM_UNAVAILABLE,
      PresentationErrorCode.EXPORT_PPTX_FAILED,
      PresentationErrorCode.EXPORT_PDF_FAILED,
    ];
    return workableErrors.includes(errorCode);
  }
}

export const presentationErrorHandler = PresentationErrorHandler.getInstance();

/**
 * Hook for handling presentation errors in React components
 */
export function usePresentationErrorHandler() {
  const handleError = (error: any, context?: Record<string, any>) => {
    return presentationErrorHandler.handleError(error, context);
  };

  const getRecoveryActions = (error: PresentationError) => {
    return presentationErrorHandler.getRecoveryActions(error);
  };

  const scheduleRetry = (key: string, maxRetries?: number, baseDelay?: number) => {
    return presentationErrorHandler.scheduleRetry(key, maxRetries, baseDelay);
  };

  const cancelRetry = (key: string) => {
    presentationErrorHandler.cancelRetry(key);
  };

  return {
    handleError,
    getRecoveryActions,
    scheduleRetry,
    cancelRetry,
  };
}