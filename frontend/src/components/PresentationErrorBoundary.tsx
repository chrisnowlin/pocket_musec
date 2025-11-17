import React, { Component, ReactNode } from 'react';
import { usePresentationErrorHandler, PresentationError } from '../errors/presentationErrors';

interface PresentationErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: PresentationError, resetError: () => void) => ReactNode;
  onError?: (error: PresentationError) => void;
}

interface PresentationErrorBoundaryState {
  hasError: boolean;
  error: PresentationError | null;
}

const DefaultErrorFallback: React.FC<{
  error: PresentationError;
  resetError: () => void;
}> = ({ error, resetError }) => {
  const { getRecoveryActions } = usePresentationErrorHandler();

  const recoveryActions = getRecoveryActions(error);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-lg w-full bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center mb-4">
          <div className="flex-shrink-0">
            <svg className="h-6 w-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-lg font-medium text-gray-900">
              Presentation Generation Error
            </h3>
          </div>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
          <p className="text-sm text-red-800">
            {error.error.user_message}
          </p>
        </div>

        {error.recovery?.retry_recommended && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
            <p className="text-sm text-blue-800 mb-2">
              <strong>Recommended actions:</strong>
            </p>
            <ul className="text-sm text-blue-700 space-y-1">
              {error.recovery.actions.map((action, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  <span>{action}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="space-y-2">
          {recoveryActions.map((action, index) => (
            <button
              key={index}
              onClick={() => action.action()}
              className={`w-full px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                action.type === 'primary'
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : action.type === 'danger'
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-900'
              }`}
            >
              {action.label}
            </button>
          ))}

          <button
            onClick={resetError}
            className="w-full px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-900 rounded-md text-sm font-medium transition-colors"
          >
            Dismiss and Continue
          </button>
        </div>

        {import.meta.env.DEV && (
          <details className="mt-4">
            <summary className="text-xs text-gray-500 cursor-pointer">Technical Details</summary>
            <div className="mt-2 p-2 bg-gray-100 rounded text-xs text-gray-700 font-mono">
              <div><strong>Error Code:</strong> {error.error.code}</div>
              <div><strong>Technical Message:</strong> {error.error.technical_message}</div>
              <div><strong>Timestamp:</strong> {error.timestamp}</div>
            </div>
          </details>
        )}
      </div>
    </div>
  );
};

class PresentationErrorBoundary extends Component<PresentationErrorBoundaryProps, PresentationErrorBoundaryState> {
  constructor(props: PresentationErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: any): Partial<PresentationErrorBoundaryState> {
    // Try to extract structured error if available
    if (error?.error?.error) {
      return {
        hasError: true,
        error: error.error,
      };
    }

    // Create a generic error for unhandled exceptions
    const genericError: PresentationError = {
      error: {
        code: 'internal_error' as any,
        user_message: 'An unexpected error occurred. The application has encountered a problem that requires your attention.',
        technical_message: error.message || 'Unknown error occurred',
        retry_recommended: true,
        retry_after_seconds: 10,
        escalation_required: true,
      },
      timestamp: new Date().toISOString(),
      recovery: {
        retry_recommended: true,
        retry_after_seconds: 10,
        actions: ['Refresh the page', 'Try the operation again', 'Contact technical support'],
      },
    };

    return {
      hasError: true,
      error: genericError,
    };
  }

  componentDidCatch(error: any, errorInfo: React.ErrorInfo) {
    console.error('Presentation Error Boundary caught an error:', error, errorInfo);

    // Log the error to monitoring service in production
    if (import.meta.env.PROD) {
      // Example: Sentry.captureException(error, { extra: errorInfo });
    }

    // Call custom error handler if provided
    if (this.props.onError && this.state.error) {
      this.props.onError(this.state.error);
    }
  }

  resetError = () => {
    this.setState({
      hasError: false,
      error: null,
    });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.resetError);
      }

      return (
        <DefaultErrorFallback
          error={this.state.error}
          resetError={this.resetError}
        />
      );
    }

    return this.props.children;
  }
}

export default PresentationErrorBoundary;

/**
 * Hook-based wrapper for easier usage in functional components
 */
export function withPresentationErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  fallbackProps?: Partial<Omit<PresentationErrorBoundaryProps, 'children'>>
) {
  return function WithErrorBoundaryWrapper(props: P) {
    return (
      <PresentationErrorBoundary {...fallbackProps}>
        <WrappedComponent {...props} />
      </PresentationErrorBoundary>
    );
  };
}