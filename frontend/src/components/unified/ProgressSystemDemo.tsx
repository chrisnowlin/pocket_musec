import React, { useState, useEffect } from 'react';
import { ProgressSystemIntegration } from './ProgressSystemIntegration';

/*
 * This is a demonstration component that shows how to use the complete
 * progress system in a real application scenario.
 */

export function ProgressSystemDemo() {
  const [currentDemo, setCurrentDemo] = useState<'generate' | 'view' | 'error'>('generate');
  const [jobId, setJobId] = useState<string | null>(null);
  const [presentationId, setPresentationId] = useState<string | null>(null);

  const handlePresentationCreated = (newJobId: string) => {
    setJobId(newJobId);
    setCurrentDemo('view');
  };

  const handlePresentationComplete = (id: string) => {
    setPresentationId(id);
  };

  const handleBackToGenerate = () => {
    setCurrentDemo('generate');
    setJobId(null);
    setPresentationId(null);
  };

  const handleErrorDemo = () => {
    setCurrentDemo('error');
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Presentation Progress System Demo
        </h1>
        <p className="text-lg text-gray-600">
          Comprehensive progress tracking, real-time updates, and error handling
        </p>
      </header>

      {/* Demo Navigation */}
      <div className="flex flex-wrap gap-4 mb-8">
        <button
          onClick={() => setCurrentDemo('generate')}
          className={`px-4 py-2 rounded-md transition-colors ${
            currentDemo === 'generate'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Generation Demo
        </button>
        <button
          onClick={() => setCurrentDemo('view')}
          className={`px-4 py-2 rounded-md transition-colors ${
            currentDemo === 'view'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
          disabled={!presentationId}
        >
          Viewer Demo (Requires complete presentation)
        </button>
        <button
          onClick={handleErrorDemo}
          className={`px-4 py-2 rounded-md transition-colors ${
            currentDemo === 'error'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Error Recovery Demo
        </button>
      </div>

      {/* Demo Content */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <ProgressSystemIntegration
          mode={currentDemo}
          jobId={jobId}
          presentationId={presentationId}
          onPresentationCreated={handlePresentationCreated}
          onPresentationComplete={handlePresentationComplete}
          onBackToGenerate={handleBackToGenerate}
        />
      </div>

      {/* Performance Metrics (development only) */}
      {import.meta.env.DEV && (
        <div className="mt-8 bg-gray-900 text-white rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-2">Performance Metrics</h2>
          <p className="text-sm text-gray-400">
            Open the browser console to see detailed performance metrics and progress updates.
          </p>
        </div>
      )}
    </div>
  );
}

export default ProgressSystemDemo;