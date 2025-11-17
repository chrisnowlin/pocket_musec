import React, { useState, useEffect } from 'react';
import apiClient from '../../services/presentationApiClient';

// Types
interface Job {
  jobId: string;
  status: string;
  priority: string;
  lessonId: string;
  progress: number;
  message: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  presentationId?: string;
  slideCount?: number;
  errorCode?: string;
  errorMessage?: string;
  retryCount: number;
  maxRetries: number;
  processingTimeSeconds?: number;
  style: string;
  useLlmPolish: boolean;
}

interface Presentation {
  id: string;
  presentationId: string;
  lessonId: string;
  lessonRevision: number;
  version: string;
  status: string;
  style: string;
  slideCount: number;
  createdAt: string;
  updatedAt: string;
  hasExports: boolean;
  errorCode?: string;
  errorMessage?: string;
  title?: string;
  description?: string;
  totalSlides?: number;
  totalDurationMinutes?: number;
  isStale?: boolean;
}

interface JobHealthMetrics {
  total_jobs: number;
  pending_jobs: number;
  running_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  cancelled_jobs: number;
  success_rate: number;
  avg_processing_time?: number;
  oldest_job_age_minutes?: number;
  total_user_jobs: number;
  user_pending_jobs: number;
  user_running_jobs: number;
  user_completed_jobs: number;
  user_failed_jobs: number;
  user_success_rate: number;
  user_failure_rate: number;
}

interface PresentationManagementProps {
  onViewPresentation?: (presentationId: string) => void;
}

const PresentationManagement: React.FC<PresentationManagementProps> = ({ onViewPresentation }) => {
  const [activeTab, setActiveTab] = useState<'jobs' | 'presentations' | 'health'>('jobs');
  const [jobs, setJobs] = useState<Job[]>([]);
  const [presentations, setPresentations] = useState<Presentation[]>([]);
  const [healthMetrics, setHealthMetrics] = useState<JobHealthMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  // Load data on component mount
  useEffect(() => {
    loadJobs();
    loadHealthMetrics();

    // Set up polling for jobs - increased to 30 seconds to avoid rate limiting
    const interval = setInterval(loadJobs, 30000); // Poll every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // Load presentations when jobs change - but only on the Presentations tab
  useEffect(() => {
    if (jobs.length > 0 && activeTab === 'presentations') {
      loadPresentations();
    }
  }, [jobs, activeTab]);

  const loadJobs = async () => {
    try {
      const jobsData = await apiClient.getJobs();
      setJobs(jobsData);
      setError(null);
    } catch (err: any) {
      console.error('Failed to load jobs:', err);
      // Check if it's a rate limit error
      if (err.message && err.message.includes('429')) {
        setError('Rate limit exceeded. Please wait a moment and refresh.');
      } else {
        setError(err.message || 'Failed to load jobs');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadPresentations = async () => {
    try {
      // Get all completed jobs with presentations
      const completedJobs = jobs.filter(j => j.status === 'completed' && j.presentationId);
      
      // Get unique presentation IDs to avoid duplicate fetches
      const uniquePresentationIds = [...new Set(completedJobs.map(j => j.presentationId))];
      
      // Fetch presentation details for each unique ID
      const presentationPromises = uniquePresentationIds.map(async (presentationId) => {
        try {
          const response = await fetch(`/api/presentations/${presentationId}`, {
            credentials: 'include'
          });
          if (response.ok) {
            return await response.json();
          }
          if (response.status === 429) {
            console.warn('Rate limit reached when fetching presentations');
          }
        } catch (err) {
          console.error(`Failed to fetch presentation ${presentationId}:`, err);
        }
        return null;
      });
      
      const presentationDetails = await Promise.all(presentationPromises);
      setPresentations(presentationDetails.filter(p => p !== null) as Presentation[]);
    } catch (err: any) {
      console.error('Failed to load presentations:', err);
    }
  };

  const loadHealthMetrics = async () => {
    try {
      const response = await fetch('/api/presentations/jobs/health', {
        credentials: 'include'
      });
      if (response.ok) {
        const metrics = await response.json();
        setHealthMetrics(metrics);
      }
    } catch (err: any) {
      console.error('Failed to load health metrics:', err);
    }
  };

  const cancelJob = async (jobId: string) => {
    try {
      const response = await fetch(`/api/presentations/jobs/${jobId}?reason=User cancelled`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        loadJobs(); // Refresh jobs list
      } else {
        const error = await response.json();
        setError(error.detail || 'Failed to cancel job');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to cancel job');
    }
  };

  const retryJob = async (jobId: string) => {
    try {
      const response = await fetch(`/api/presentations/jobs/${jobId}/retry`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ force_retry: false }),
        credentials: 'include'
      });

      if (response.ok) {
        loadJobs(); // Refresh jobs list
      } else {
        const error = await response.json();
        setError(error.detail || 'Failed to retry job');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to retry job');
    }
  };

  const deleteJob = async (jobId: string) => {
    if (!confirm('Are you sure you want to permanently delete this job? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/presentations/jobs/${jobId}/permanent`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        loadJobs(); // Refresh jobs list
      } else {
        const error = await response.json();
        setError(error.detail || 'Failed to delete job');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete job');
    }
  };

  const deletePresentation = async (presentationId: string) => {
    if (!confirm('Are you sure you want to delete this presentation? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/presentations/${presentationId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        loadPresentations(); // Refresh presentations list
        loadJobs(); // Also refresh jobs in case a job pointed to this presentation
      } else {
        const error = await response.json();
        setError(error.detail || 'Failed to delete presentation');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete presentation');
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      'pending': 'bg-parchment-200 text-ink-700',
      'running': 'bg-blue-100 text-blue-800',
      'completed': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800',
      'cancelled': 'bg-parchment-100 text-ink-600'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || 'bg-parchment-100 text-ink-600'}`}>
        {status}
      </span>
    );
  };

  const getPriorityBadge = (priority: string) => {
    const styles: Record<string, string> = {
      'low': 'bg-parchment-100 text-ink-600',
      'normal': 'bg-parchment-200 text-ink-700',
      'high': 'bg-orange-100 text-orange-800',
      'urgent': 'bg-red-100 text-red-800'
    };

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${styles[priority] || 'bg-parchment-100 text-ink-600'}`}>
        {priority}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds}s`;
    return `${(seconds / 60).toFixed(1)}m`;
  };

  if (loading && jobs.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ink-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto min-h-full">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-ink-800">Presentation Management</h1>
        <p className="text-ink-600 mt-2">Manage presentation generation jobs and view created presentations</p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-300 rounded-md p-4">
          <div className="flex items-start">
            <svg className="h-5 w-5 text-red-600 mt-0.5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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

      {/* Tabs */}
      <div className="border-b border-ink-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('jobs')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'jobs'
                ? 'border-ink-600 text-ink-800'
                : 'border-transparent text-ink-500 hover:text-ink-700 hover:border-ink-300'
            }`}
          >
            Generation Jobs
            {jobs.length > 0 && (
              <span className="ml-2 bg-parchment-200 text-ink-700 py-0.5 px-2 rounded-full text-xs">
                {jobs.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('presentations')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'presentations'
                ? 'border-ink-600 text-ink-800'
                : 'border-transparent text-ink-500 hover:text-ink-700 hover:border-ink-300'
            }`}
          >
            Presentations
          </button>
          <button
            onClick={() => setActiveTab('health')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'health'
                ? 'border-ink-600 text-ink-800'
                : 'border-transparent text-ink-500 hover:text-ink-700 hover:border-ink-300'
            }`}
          >
            System Health
          </button>
        </nav>
      </div>

      {/* Jobs Tab */}
      {activeTab === 'jobs' && (
        <div>
          {jobs.length === 0 ? (
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-ink-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
              </svg>
              <h3 className="mt-4 text-lg font-medium text-ink-800">No jobs found</h3>
              <p className="mt-2 text-ink-600">Get started by generating a presentation from a lesson.</p>
            </div>
          ) : (
            <div className="workspace-card shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-ink-200">
                {jobs.map((job) => (
                  <li key={job.jobId} className="hover:bg-parchment-100">
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-3">
                            <p className="text-sm font-medium text-ink-600 truncate">
                              Job ID: {job.jobId}
                            </p>
                            {getStatusBadge(job.status)}
                            {getPriorityBadge(job.priority)}
                          </div>
                          <div className="mt-2 flex items-center text-sm text-ink-500">
                            <p>Lesson ID: {job.lessonId}</p>
                            <span className="mx-2">•</span>
                            <p>Created: {formatDate(job.createdAt)}</p>
                            {job.startedAt && (
                              <>
                                <span className="mx-2">•</span>
                                <p>Started: {formatDate(job.startedAt)}</p>
                              </>
                            )}
                            {job.processingTimeSeconds && (
                              <>
                                <span className="mx-2">•</span>
                                <p>Duration: {formatDuration(job.processingTimeSeconds)}</p>
                              </>
                            )}
                          </div>
                          <p className="mt-1 text-sm text-ink-500">{job.message}</p>

                          {/* Progress Bar */}
                          {(job.status === 'running' || job.status === 'pending') && (
                            <div className="mt-2">
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-xs text-ink-500">Progress</span>
                                <span className="text-xs text-ink-500">{job.progress}%</span>
                              </div>
                              <div className="w-full bg-parchment-300 rounded-full h-1.5">
                                <div
                                  className="bg-ink-600 h-1.5 rounded-full transition-all duration-300"
                                  style={{ width: `${job.progress}%` }}
                                ></div>
                              </div>
                            </div>
                          )}

                          {/* Error Details */}
                          {job.errorMessage && (
                            <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                              {job.errorMessage}
                            </div>
                          )}
                        </div>

                        <div className="flex items-center space-x-2 ml-4">
                          {job.status === 'pending' || job.status === 'running' ? (
                            <button
                              onClick={() => cancelJob(job.jobId)}
                              className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                              title="Cancel job"
                            >
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            </button>
                          ) : job.status === 'failed' ? (
                            <button
                              onClick={() => retryJob(job.jobId)}
                              className="p-2 text-ink-500 hover:text-ink-700 hover:bg-parchment-200 rounded"
                              title="Retry job"
                            >
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                              </svg>
                            </button>
                          ) : null}

                          {job.presentationId && (
                            <button
                              onClick={() => {
                                if (onViewPresentation) {
                                  onViewPresentation(job.presentationId!);
                                } else {
                                  window.location.href = `/presentations/${job.presentationId}`;
                                }
                              }}
                              className="p-2 text-green-700 hover:text-green-800 hover:bg-green-50 rounded"
                              title="View presentation"
                            >
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                            </button>
                          )}

                          {/* Delete button - only show for finished jobs */}
                          {(job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') && (
                            <button
                              onClick={() => deleteJob(job.jobId)}
                              className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                              title="Delete job"
                            >
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Presentations Tab */}
      {activeTab === 'presentations' && (
        <div>
          {presentations.length === 0 ? (
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-ink-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              <h3 className="mt-4 text-lg font-medium text-ink-800">No presentations yet</h3>
              <p className="mt-2 text-ink-600">Generate presentations from your lessons to see them here.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {presentations.map((presentation) => (
                <div key={presentation.id} className="workspace-card shadow rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-ink-800 truncate">
                          {presentation.title || 'Untitled Presentation'}
                        </h3>
                        <p className="text-sm text-ink-600 mt-1">
                          {presentation.slideCount} slides • {presentation.totalDurationMinutes || 0} min
                        </p>
                      </div>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        presentation.status === 'complete' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {presentation.status}
                      </span>
                    </div>
                    
                    {presentation.description && (
                      <p className="text-sm text-ink-600 mb-4 line-clamp-2">{presentation.description}</p>
                    )}
                    
                    <div className="flex items-center justify-between text-xs text-ink-500 mb-4">
                      <span>Lesson: {presentation.lessonId.substring(0, 8)}...</span>
                      <span>v{presentation.version}</span>
                    </div>
                    
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          if (onViewPresentation) {
                            onViewPresentation(presentation.id);
                          } else {
                            window.location.href = `/presentations/${presentation.id}`;
                          }
                        }}
                        className="flex-1 px-4 py-2 bg-ink-600 text-parchment-100 rounded hover:bg-ink-700 transition-colors text-sm font-medium"
                      >
                        View
                      </button>
                      {presentation.hasExports && (
                        <button
                          onClick={() => window.open(`/api/presentations/${presentation.id}/export?format=pptx`, '_blank')}
                          className="px-4 py-2 border border-ink-300 text-ink-700 rounded hover:bg-ink-50 transition-colors text-sm font-medium"
                          title="Download PPTX"
                        >
                          ⬇️
                        </button>
                      )}
                      <button
                        onClick={() => deletePresentation(presentation.id)}
                        className="px-4 py-2 border border-red-300 text-red-700 rounded hover:bg-red-50 transition-colors text-sm font-medium"
                        title="Delete presentation"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                    
                    <div className="mt-4 pt-4 border-t border-ink-200 text-xs text-ink-500">
                      Created {new Date(presentation.createdAt).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Health Tab */}
      {activeTab === 'health' && (
        <div>
          {healthMetrics ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Overall Stats */}
              <div className="workspace-card p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-ink-800 mb-4">System Overview</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-ink-500">Total Jobs</span>
                    <span className="text-sm font-medium text-ink-700">{healthMetrics.total_jobs}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-ink-500">Success Rate</span>
                    <span className="text-sm font-medium text-green-700">{healthMetrics.success_rate.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-ink-500">Avg Processing Time</span>
                    <span className="text-sm font-medium text-ink-700">{formatDuration(healthMetrics.avg_processing_time)}</span>
                  </div>
                </div>
              </div>

              {/* Job Status Breakdown */}
              <div className="workspace-card p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-ink-800 mb-4">Job Status</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-ink-500">Pending</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-ink-700">{healthMetrics.pending_jobs}</span>
                      {getStatusBadge('pending')}
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-ink-500">Running</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-ink-700">{healthMetrics.running_jobs}</span>
                      {getStatusBadge('running')}
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-ink-500">Completed</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-ink-700">{healthMetrics.completed_jobs}</span>
                      {getStatusBadge('completed')}
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-ink-500">Failed</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-ink-700">{healthMetrics.failed_jobs}</span>
                      {getStatusBadge('failed')}
                    </div>
                  </div>
                </div>
              </div>

              {/* User Stats */}
              <div className="workspace-card p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-ink-800 mb-4">Your Jobs</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-ink-500">Your Total Jobs</span>
                    <span className="text-sm font-medium text-ink-700">{healthMetrics.total_user_jobs}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-ink-500">Your Success Rate</span>
                    <span className="text-sm font-medium text-green-700">{healthMetrics.user_success_rate.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-ink-500">Your Active Jobs</span>
                    <span className="text-sm font-medium text-ink-700">{healthMetrics.user_pending_jobs + healthMetrics.user_running_jobs}</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <svg className="animate-spin h-8 w-8 text-ink-600 mx-auto" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p className="mt-2 text-ink-600">Loading health metrics...</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PresentationManagement;