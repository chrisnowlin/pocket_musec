import ErrorBoundary from '../components/ErrorBoundary';
import FileOperationErrorBoundary from '../components/FileOperationErrorBoundary';
import DocumentIngestion from '../components/DocumentIngestion';

export default function IngestionPage() {
  return (
    <ErrorBoundary
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-ink-900">
          <div className="text-center text-parchment-300">
            <h2 className="text-2xl font-semibold mb-4">Document Ingestion Unavailable</h2>
            <p className="mb-6">The document ingestion component encountered an error and is temporarily unavailable.</p>
            <button
              onClick={() => window.location.href = '/'}
              className="px-6 py-3 bg-ink-600 rounded-lg hover:bg-ink-500 transition-colors"
            >
              Return to Home
            </button>
          </div>
        </div>
      }
      onError={(error, errorInfo) => {
        console.error('IngestionPage error:', error, errorInfo);
      }}
    >
      <FileOperationErrorBoundary
        onFileError={(error, operation) => {
          console.error(`Ingestion file operation error in ${operation}:`, error);
        }}
      >
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Document Ingestion</h1>
            <p className="mt-2 text-gray-600">
              Upload and process music education documents with AI-powered analysis
            </p>
          </div>
          
          <DocumentIngestion />
        </div>
      </FileOperationErrorBoundary>
    </ErrorBoundary>
  );
}