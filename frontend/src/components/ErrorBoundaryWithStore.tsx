import React, { Component, ReactNode } from 'react';
import { errorActions } from '../stores/errorStore';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  source?: string; // Identify which part of the app this boundary covers
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error boundary that integrates with the global error store.
 * Catches React component errors and reports them to the error store.
 */
export class ErrorBoundaryWithStore extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Report to error store
    errorActions.addError(error.message, 'error', {
      source: this.props.source || 'ErrorBoundary',
      action: 'render',
      data: {
        stack: error.stack,
        componentStack: errorInfo.componentStack,
      },
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log to console
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex items-center justify-center min-h-screen bg-parchment-100">
          <div className="max-w-md p-8 bg-white rounded-lg shadow-lg">
            <div className="flex items-center mb-4">
              <svg
                className="w-6 h-6 text-red-600 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <h2 className="text-xl font-bold text-ink-800">Something went wrong</h2>
            </div>
            <p className="text-ink-600 mb-4">
              We encountered an unexpected error. Please try refreshing the page.
            </p>
            {this.state.error && (
              <details className="mt-4 p-4 bg-parchment-100 rounded text-sm">
                <summary className="cursor-pointer font-medium text-ink-700">
                  Error details
                </summary>
                <pre className="mt-2 text-xs text-ink-600 overflow-auto">
                  {this.state.error.message}
                  {'\n\n'}
                  {this.state.error.stack}
                </pre>
              </details>
            )}
            <button
              onClick={() => window.location.reload()}
              className="mt-4 w-full bg-ink-600 hover:bg-ink-700 text-parchment-100 rounded-lg px-4 py-2 font-medium transition-colors"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundaryWithStore;