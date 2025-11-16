import { Routes, Route, Navigate } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import FileOperationErrorBoundary from './components/FileOperationErrorBoundary';
import UnifiedPage from './pages/UnifiedPage';
import PocketPlannerPage from './pages/PocketPlannerPage';
import MusecDBPage from './pages/MusecDBPage';
import MusecTrackerPage from './pages/MusecTrackerPage';

function App() {
  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // Log application-level errors
        console.error('Application error:', error, errorInfo);
        // In production, you could send this to an error tracking service
        if (import.meta.env.PROD) {
          // Example: window.Sentry?.captureException(error, { contexts: { react: { componentStack: errorInfo.componentStack } } });
        }
      }}
    >
      <Routes>
        <Route
          path="/"
          element={
            <FileOperationErrorBoundary>
              <UnifiedPage />
            </FileOperationErrorBoundary>
          }
        />
        <Route
          path="/planner"
          element={
            <ErrorBoundary
              fallback={
                <div className="min-h-screen flex items-center justify-center bg-ink-900">
                  <div className="text-center text-parchment-300">
                    <h2 className="text-xl font-semibold mb-2">Planner Unavailable</h2>
                    <p className="mb-4">The planner component encountered an error.</p>
                    <button
                      onClick={() => window.location.href = '/'}
                      className="px-4 py-2 bg-ink-600 rounded hover:bg-ink-500"
                    >
                      Return to Home
                    </button>
                  </div>
                </div>
              }
            >
              <PocketPlannerPage />
            </ErrorBoundary>
          }
        />
        <Route
          path="/db"
          element={
            <FileOperationErrorBoundary>
              <MusecDBPage />
            </FileOperationErrorBoundary>
          }
        />
        <Route
          path="/tracker"
          element={
            <ErrorBoundary
              fallback={
                <div className="min-h-screen flex items-center justify-center bg-ink-900">
                  <div className="text-center text-parchment-300">
                    <h2 className="text-xl font-semibold mb-2">Tracker Unavailable</h2>
                    <p className="mb-4">The tracker component encountered an error.</p>
                    <button
                      onClick={() => window.location.href = '/'}
                      className="px-4 py-2 bg-ink-600 rounded hover:bg-ink-500"
                    >
                      Return to Home
                    </button>
                  </div>
                </div>
              }
            >
              <MusecTrackerPage />
            </ErrorBoundary>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ErrorBoundary>
  );
}

export default App;
