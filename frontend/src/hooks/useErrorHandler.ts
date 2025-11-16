import { useEffect } from 'react';
import { useErrorStore, errorSelectors, type ErrorSeverity, type ErrorMetadata } from '../stores/errorStore';
import { useToast } from './useToast';
import { toastActions } from '../stores/toastStore';

/**
 * Hook that bridges the global error store with the toast notification system.
 * Automatically displays toasts for new errors and provides error management functions.
 */
export function useErrorHandler() {
  const { error, warning, info, success } = useToast();
  const errors = useErrorStore(errorSelectors.activeErrors);
  const addError = useErrorStore((state) => state.addError);
  const dismissError = useErrorStore((state) => state.dismissError);
  const clearErrors = useErrorStore((state) => state.clearErrors);
  const clearErrorsBySource = useErrorStore((state) => state.clearErrorsBySource);

  // Auto-display toasts for new errors
  useEffect(() => {
    const recentErrors = errors.filter(
      (e) => Date.now() - e.metadata.timestamp < 100 // Recently added (within 100ms)
    );

    recentErrors.forEach((err) => {
      switch (err.severity) {
        case 'error':
          error(err.message);
          break;
        case 'warning':
          warning(err.message);
          break;
        case 'info':
          info(err.message);
          break;
      }
    });
  }, [errors, error, warning, info]);

  /**
   * Report an error to the global error store and optionally show a toast
   */
  const reportError = (
    message: string,
    options?: {
      severity?: ErrorSeverity;
      source?: string;
      action?: string;
      data?: any;
      silent?: boolean; // Don't show toast
    }
  ) => {
    const errorId = addError(message, options?.severity, {
      source: options?.source,
      action: options?.action,
      data: options?.data,
    });

    // If silent, immediately dismiss to prevent toast
    if (options?.silent) {
      setTimeout(() => dismissError(errorId), 0);
    }

    return errorId;
  };

  /**
   * Report a successful operation (shows success toast)
   */
  const reportSuccess = (message: string) => {
    success(message);
  };

  return {
    // State
    errors,
    hasErrors: errors.length > 0,

    // Actions
    reportError,
    reportSuccess,
    dismissError,
    clearErrors,
    clearErrorsBySource,

    // Direct toast functions
    showError: error,
    showWarning: warning,
    showInfo: info,
    showSuccess: success,
  };
}

/**
 * Higher-order function to wrap async operations with error handling
 */
export function withErrorHandler<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  options?: {
    source?: string;
    action?: string;
    errorMessage?: string;
    successMessage?: string;
  }
): T {
  return (async (...args: Parameters<T>) => {
    try {
      const result = await fn(...args);
      
      if (options?.successMessage) {
        toastActions.success(options.successMessage);
      }
      
      return result;
    } catch (err: any) {
      const { addError } = useErrorStore.getState();
      const message = options?.errorMessage || err.message || 'An error occurred';
      
      addError(message, 'error', {
        source: options?.source,
        action: options?.action,
        data: err,
      });
      
      throw err;
    }
  }) as T;
}
