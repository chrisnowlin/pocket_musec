import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  onFileError?: (error: Error, operation: string) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  operation: string | null;
}

class FileOperationErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      operation: null
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      operation: null
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Extract operation from component stack or error message
    const operation = this.extractOperation(error, errorInfo);
    
    console.error(`File operation error in ${operation}:`, error, errorInfo);
    
    // Call custom error handler if provided
    if (this.props.onFileError) {
      this.props.onFileError(error, operation);
    }

    this.setState({
      operation
    });
  }

  private extractOperation(error: Error, errorInfo: ErrorInfo): string {
    const stack = errorInfo.componentStack || '';
    const errorMessage = error.message.toLowerCase();
    
    // Try to determine the operation based on error message and stack
    if (errorMessage.includes('upload') || stack.includes('upload')) {
      return 'file upload';
    } else if (errorMessage.includes('download') || stack.includes('download')) {
      return 'file download';
    } else if (errorMessage.includes('delete') || stack.includes('delete')) {
      return 'file deletion';
    } else if (errorMessage.includes('ingestion') || stack.includes('ingestion')) {
      return 'file ingestion';
    } else if (errorMessage.includes('storage') || stack.includes('storage')) {
      return 'file storage operation';
    } else {
      return 'file operation';
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      operation: null
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-red-900 border border-red-700 rounded-lg p-4 m-4">
          <div className="flex items-center gap-3">
            <div className="text-2xl">📁</div>
            <div className="flex-1">
              <h3 className="text-red-200 font-semibold mb-1">
                File Operation Failed
              </h3>
              <p className="text-red-300 text-sm">
                {this.state.operation && (
                  <>An error occurred during {this.state.operation}. </>
                )}
                Please check your file and try again.
              </p>
              
              {/* Show error details in development */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-2">
                  <summary className="text-red-400 cursor-pointer text-xs">
                    Technical Details
                  </summary>
                  <pre className="text-red-400 text-xs mt-1 bg-red-950 p-2 rounded overflow-auto">
                    {this.state.error.toString()}
                  </pre>
                </details>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={this.handleRetry}
                className="px-3 py-1 bg-red-700 text-white rounded hover:bg-red-600 transition-colors text-sm"
              >
                Retry
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-3 py-1 bg-red-800 text-white rounded hover:bg-red-700 transition-colors text-sm"
              >
                Reload
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook for handling file operation errors
export const useFileOperationError = () => {
  const handleError = (error: Error, operation: string) => {
    // Log to error tracking service in production
    if (process.env.NODE_ENV === 'production') {
      // Could integrate with error tracking service like Sentry
      console.error(`File operation error tracked: ${operation}`, error);
    }
    
    // Show user-friendly notification
    const userMessages: Record<string, string> = {
      'file upload': 'Failed to upload file. Please check the file format and size.',
      'file download': 'Failed to download file. Please try again.',
      'file deletion': 'Failed to delete file. Please check permissions.',
      'file ingestion': 'Failed to process file. The file may be corrupted or in an unsupported format.',
      'file storage operation': 'A storage operation failed. Please check your connection and try again.'
    };
    
    const message = userMessages[operation] || 'A file operation failed. Please try again.';
    
    // Here you could integrate with a toast notification system
    console.warn('User message:', message);
  };

  return { handleError };
};

export default FileOperationErrorBoundary;