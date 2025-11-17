import React, { useState, useEffect } from 'react';
import apiClient from '../../services/presentationApiClient';

interface Lesson {
  id: string;
  title: string;
  description?: string;
  content?: string;
}

interface PresentationCreatorProps {
  onPresentationGenerated?: (presentationId: string) => void;
}

interface GenerationOptions {
  style: string;
  useLlmPolish: boolean;
  timeoutSeconds: number;
  priority: string;
  maxRetries: number;
}

const PresentationCreator: React.FC<PresentationCreatorProps> = ({ onPresentationGenerated }) => {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [selectedLesson, setSelectedLesson] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [progress, setProgress] = useState<{ message: string; progress: number } | null>(null);

  const [options, setOptions] = useState<GenerationOptions>({
    style: 'default',
    useLlmPolish: true,
    timeoutSeconds: 30,
    priority: 'normal',
    maxRetries: 2
  });

  // Available styles
  const availableStyles = [
    { value: 'default', label: 'Default', description: 'Standard professional presentation' },
    { value: 'minimal', label: 'Minimal', description: 'Clean and simple design' },
    { value: 'corporate', label: 'Corporate', description: 'Business-oriented style' },
    { value: 'educational', label: 'Educational', description: 'Optimized for teaching' },
    { value: 'creative', label: 'Creative', description: 'Modern and artistic design' }
  ];

  const priorities = [
    { value: 'low', label: 'Low', description: 'Process when resources are available' },
    { value: 'normal', label: 'Normal', description: 'Standard processing queue' },
    { value: 'high', label: 'High', description: 'Priority processing' },
    { value: 'urgent', label: 'Urgent', description: 'Immediate processing' }
  ];

  const timeouts = [
    { value: 15, label: '15 seconds', description: 'Fast generation, basic quality' },
    { value: 30, label: '30 seconds', description: 'Standard generation time' },
    { value: 60, label: '60 seconds', description: 'Higher quality, longer wait' },
    { value: 120, label: '2 minutes', description: 'Maximum quality' }
  ];

  useEffect(() => {
    loadLessons();
  }, []);

  const loadLessons = async () => {
    try {
      setLoading(true);
      // This would be implemented in your API client
      // For now, we'll use a mock list or fetch from your lessons endpoint
      const response = await fetch('/api/lessons', {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setLessons(data);
      } else {
        // Fallback to empty array if no lessons endpoint exists
        setLessons([]);
      }
    } catch (err: any) {
      console.error('Failed to load lessons:', err);
      setError('Failed to load lessons');
      setLessons([]);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePresentation = async () => {
    if (!selectedLesson) {
      setError('Please select a lesson');
      return;
    }

    try {
      setGenerating(true);
      setError(null);
      setSuccess(null);
      setProgress({ message: 'Starting presentation generation...', progress: 0 });

      // Create presentation generation job
      const generationResult = await apiClient.generatePresentation(selectedLesson, {
        style: options.style,
        useLlmPolish: options.useLlmPolish,
        timeoutSeconds: options.timeoutSeconds,
        priority: options.priority,
        maxRetries: options.maxRetries
      });

      setProgress({ message: generationResult.message, progress: 10 });

      if (generationResult.accepted) {
        // Poll for job completion
        const pollResult = await apiClient.pollJobStatus(generationResult.jobId, {
          onProgress: (status, attempt) => {
            const progressMap: Record<string, number> = {
              'pending': 20 + (attempt * 5),
              'running': 50 + (attempt * 10),
              'completed': 90,
              'failed': 100
            };

            const messageMap: Record<string, string> = {
              'pending': 'Waiting to start...',
              'running': `Generating presentation (attempt ${attempt})...`,
              'completed': 'Finalizing presentation...',
              'failed': 'Generation failed'
            };

            setProgress({
              message: messageMap[status.status] || `Processing... (attempt ${attempt})`,
              progress: Math.min(progressMap[status.status] || 50, 90)
            });
          }
        });

        if (pollResult.success && pollResult.status.presentationId) {
          setProgress({ message: 'Presentation generated successfully!', progress: 100 });
          setSuccess(`Presentation "${pollResult.status.presentationId}" has been created successfully!`);

          if (onPresentationGenerated) {
            onPresentationGenerated(pollResult.status.presentationId);
          }

          // Reset form after 3 seconds
          setTimeout(() => {
            setSuccess(null);
            setProgress(null);
            setSelectedLesson('');
          }, 5000);
        } else {
          throw new Error('Presentation generation failed');
        }
      }
    } catch (err: any) {
      console.error('Presentation generation failed:', err);
      setError(err.message || 'Failed to generate presentation');
      setProgress(null);
    } finally {
      setGenerating(false);
    }
  };

  const handleOptionChange = (key: keyof GenerationOptions, value: any) => {
    setOptions(prev => ({ ...prev, [key]: value }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ink-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6 min-h-full">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-ink-800">Create New Presentation</h2>
        <p className="text-ink-600 mt-2">Generate an engaging presentation from your lesson content</p>
      </div>

      {/* Success Message */}
      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex items-start">
            <svg className="h-5 w-5 text-green-400 mt-0.5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-green-800">Success!</h3>
              <p className="mt-1 text-sm text-green-700">{success}</p>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex items-start">
            <svg className="h-5 w-5 text-red-400 mt-0.5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
              <button
                onClick={() => setError(null)}
                className="mt-2 text-sm text-red-600 hover:text-red-800"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Progress Display */}
      {progress && (
        <div className="mb-6 bg-parchment-100 border border-ink-200 rounded-md p-4">
          <div className="flex items-center">
            <svg className="animate-spin h-5 w-5 text-ink-600 mr-3" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <div className="flex-1">
              <p className="text-sm text-ink-600 font-medium">{progress.message}</p>
              <div className="mt-2 w-full bg-parchment-300 rounded-full h-2">
                <div
                  className="bg-ink-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress.progress}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="workspace-card shadow rounded-lg">
        <div className="p-6 space-y-6">
          {/* Lesson Selection */}
          <div>
            <label htmlFor="lesson" className="block text-sm font-medium text-ink-700 mb-2">
              Select Lesson
            </label>
            <select
              id="lesson"
              value={selectedLesson}
              onChange={(e) => setSelectedLesson(e.target.value)}
              disabled={generating}
              className="w-full border border-ink-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-ink-500 focus:border-ink-500 disabled:bg-parchment-200"
            >
              <option value="">Choose a lesson...</option>
              {lessons.map((lesson) => (
                <option key={lesson.id} value={lesson.id}>
                  {lesson.title} {lesson.description && `- ${lesson.description}`}
                </option>
              ))}
            </select>
            {lessons.length === 0 && !loading && (
              <p className="mt-2 text-sm text-ink-500">
                No lessons available. Create some lessons first to generate presentations.
              </p>
            )}
          </div>

          {/* Style Selection */}
          <div>
            <label className="block text-sm font-medium text-ink-700 mb-2">
              Presentation Style
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {availableStyles.map((style) => (
                <label
                  key={style.value}
                  className={`relative border rounded-lg p-3 cursor-pointer transition-colors ${
                    options.style === style.value
                      ? 'border-ink-500 bg-parchment-200'
                      : 'border-ink-300 hover:border-ink-400'
                  }`}
                >
                  <input
                    type="radio"
                    name="style"
                    value={style.value}
                    checked={options.style === style.value}
                    onChange={(e) => handleOptionChange('style', e.target.value)}
                    disabled={generating}
                    className="sr-only"
                  />
                  <div className="flex items-start">
                    <div className={`flex items-center justify-center w-4 h-4 rounded-full border-2 mr-3 mt-0.5 ${
                      options.style === style.value ? 'border-ink-500' : 'border-ink-300'
                    }`}>
                      {options.style === style.value && (
                        <div className="w-2 h-2 rounded-full bg-ink-500"></div>
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-ink-800">{style.label}</p>
                      <p className="text-xs text-ink-500 mt-1">{style.description}</p>
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Advanced Options */}
          <details className="border border-ink-200 rounded-lg">
            <summary className="px-4 py-3 cursor-pointer hover:bg-parchment-100 font-medium text-sm text-ink-700">
              Advanced Options
            </summary>
            <div className="p-4 pt-0 space-y-4">
              {/* AI Polishing */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="use_llm_polish"
                  checked={options.useLlmPolish}
                  onChange={(e) => handleOptionChange('useLlmPolish', e.target.checked)}
                  disabled={generating}
                  className="rounded border-ink-300 text-ink-600 focus:ring-ink-500"
                />
                <label htmlFor="use_llm_polish" className="ml-2 text-sm text-ink-700">
                  Use AI polishing to enhance content quality
                </label>
              </div>

              {/* Priority */}
              <div>
                <label className="block text-sm font-medium text-ink-700 mb-2">
                  Processing Priority
                </label>
                <select
                  value={options.priority}
                  onChange={(e) => handleOptionChange('priority', e.target.value)}
                  disabled={generating}
                  className="w-full border border-ink-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-ink-500 focus:border-ink-500"
                >
                  {priorities.map((priority) => (
                    <option key={priority.value} value={priority.value}>
                      {priority.label} - {priority.description}
                    </option>
                  ))}
                </select>
              </div>

              {/* Timeout */}
              <div>
                <label className="block text-sm font-medium text-ink-700 mb-2">
                  Generation Timeout
                </label>
                <select
                  value={options.timeoutSeconds}
                  onChange={(e) => handleOptionChange('timeoutSeconds', parseInt(e.target.value))}
                  disabled={generating}
                  className="w-full border border-ink-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-ink-500 focus:border-ink-500"
                >
                  {timeouts.map((timeout) => (
                    <option key={timeout.value} value={timeout.value}>
                      {timeout.label} - {timeout.description}
                    </option>
                  ))}
                </select>
              </div>

              {/* Max Retries */}
              <div>
                <label className="block text-sm font-medium text-ink-700 mb-2">
                  Maximum Retries: {options.maxRetries}
                </label>
                <input
                  type="range"
                  min="0"
                  max="5"
                  value={options.maxRetries}
                  onChange={(e) => handleOptionChange('maxRetries', parseInt(e.target.value))}
                  disabled={generating}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-ink-500">
                  <span>No retries</span>
                  <span>5 retries</span>
                </div>
              </div>
            </div>
          </details>
        </div>

        {/* Action Buttons */}
        <div className="bg-parchment-100 px-6 py-4 rounded-b-lg flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => {
              setSelectedLesson('');
              setOptions({
                style: 'default',
                useLlmPolish: true,
                timeoutSeconds: 30,
                priority: 'normal',
                maxRetries: 2
              });
            }}
            disabled={generating}
            className="px-4 py-2 border border-ink-300 rounded-md text-sm font-medium text-ink-700 hover:bg-parchment-200 focus:outline-none focus:ring-2 focus:ring-ink-500 focus:border-ink-500 disabled:opacity-50"
          >
            Reset Form
          </button>
          <button
            type="button"
            onClick={handleGeneratePresentation}
            disabled={generating || !selectedLesson}
            className="px-6 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-ink-600 hover:bg-ink-700 focus:outline-none focus:ring-2 focus:ring-ink-500 focus:border-ink-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating ? 'Generating...' : 'Generate Presentation'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PresentationCreator;