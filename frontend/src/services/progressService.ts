/* Service for real-time presentation generation progress tracking */

import { getAuth, getAuthToken, getAuthUserId } from './auth';

export interface StepProgress {
  step: string;
  name: string;
  description: string;
  weight: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  progress: number;
  started_at?: string;
  completed_at?: string;
  estimated_duration?: number;
  actual_duration?: number;
  error_message?: string;
  details: Record<string, any>;
}

export interface DetailedProgress {
  job_id: string;
  current_step?: string;
  current_step_info?: {
    step: string;
    name: string;
    description: string;
    progress: number;
    status: string;
    started_at?: string;
    message: string;
  };
  overall_progress: number;
  estimated_time_remaining_seconds?: number;
  estimated_completion_time?: string;
  current_message: string;
  last_updated: string;
  steps: StepProgress[];
}

export interface ProgressUpdate {
  job_id: string;
  update_type: 'progress' | 'step_complete' | 'step_error' | 'job_complete' | 'job_error' | 'job_status';
  timestamp: string;
  progress?: DetailedProgress;
  result?: any;
  error?: any;
  job_status?: any;
}

export interface ProgressSubscription {
  jobId: string;
  onProgress: (update: ProgressUpdate) => void;
  onError: (error: Error) => void;
  onComplete?: (result: any) => void;
  onConnectionChange?: (connected: boolean) => void;
}

class ProgressService {
  private ws: WebSocket | null = null;
  private subscriptions: Map<string, ProgressSubscription> = new Map();
  private reconnectAttempts: Map<string, number> = new Map();
  private reconnectTimers: Map<string, NodeJS.Timeout> = new Map();
  private heartbeatTimers: Map<string, NodeJS.Timeout> = new Map();
  private fallbackPollingIntervals: Map<string, NodeJS.Timeout> = new Map();
  private readonly maxReconnectAttempts = 5;
  private readonly reconnectDelay = 2000;
  private readonly pollingInterval = 2000;
  private readonly heartbeatInterval = 30000;

  async subscribe(subscription: ProgressSubscription): Promise<void> {
    const { jobId } = subscription;

    // Store subscription
    this.subscriptions.set(jobId, subscription);
    this.reconnectAttempts.set(jobId, 0);

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.sendSubscribe(jobId);
      if (subscription.onConnectionChange) {
        subscription.onConnectionChange(true);
      }
      return;
    }

    try {
      // Try WebSocket connection first
      await this.connectWebSocket(jobId);
    } catch (error) {
      console.warn(`WebSocket connection failed for job ${jobId}, falling back to polling:`, error);
      this.startPolling(jobId);
    }
  }

  unsubscribe(jobId: string): void {
    // Remove subscription
    this.subscriptions.delete(jobId);

    // Notify server we no longer need this job
    this.sendUnsubscribe(jobId);

    // Clean up polling
    this.stopPolling(jobId);

    // Clean up timers
    this.cleanupTimers(jobId);

    if (this.subscriptions.size === 0) {
      this.disconnectWebSocket();
    }
  }

  private async connectWebSocket(jobId: string): Promise<void> {
    const auth = getAuth();
    const userId = getAuthUserId();
    if (!auth || !auth.token || !userId) {
      throw new Error('Authentication required for progress tracking');
    }

    // Build WebSocket URL with authentication
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    const wsUrl = `${wsProtocol}//${wsHost}/api/presentations/progress/ws?user_id=${userId}`;

    return new Promise((resolve, reject) => {
      let timeout: NodeJS.Timeout | undefined;
      
      try {
        this.ws = new WebSocket(wsUrl);

        timeout = setTimeout(() => {
          reject(new Error('WebSocket connection timeout'));
        }, 10000);

        this.ws.onopen = () => {
          if (timeout) clearTimeout(timeout);
          console.log(`WebSocket connected for job ${jobId}`);

          // Subscribe to job updates
          this.sendSubscribe(jobId);

          // Start heartbeat
          this.startHeartbeat(jobId);

          // Notify connection change
          const subscription = this.subscriptions.get(jobId);
          if (subscription?.onConnectionChange) {
            subscription.onConnectionChange(true);
          }

          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(jobId, data);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          if (timeout) clearTimeout(timeout);
          console.log(`WebSocket closed for job ${jobId}:`, event.code, event.reason);

          // Notify connection change
          const subscription = this.subscriptions.get(jobId);
          if (subscription?.onConnectionChange) {
            subscription.onConnectionChange(false);
          }

          // Try to reconnect if not a normal closure
          if (event.code !== 1000) {
            this.handleReconnect(jobId);
          }
        };

        this.ws.onerror = (event) => {
          if (timeout) clearTimeout(timeout);
          console.error('WebSocket error:', event);
          reject(new Error('WebSocket connection failed'));
        };

      } catch (error) {
        if (timeout) clearTimeout(timeout);
        reject(error);
      }
    });
  }

  private disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close(1000, 'Normal closure');
      this.ws = null;
    }
  }

  private sendSubscribe(jobId: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe_job',
        job_id: jobId
      }));
    }
  }

  private sendUnsubscribe(jobId: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe_job',
        job_id: jobId
      }));
    }
  }

  private handleWebSocketMessage(jobId: string, data: any): void {
    const subscription = this.subscriptions.get(jobId);
    if (!subscription) return;

    switch (data.type) {
      case 'connected':
        console.log(`WebSocket connection confirmed for user ${data.user_id}`);
        break;

      case 'progress':
      case 'step_complete':
      case 'step_error':
      case 'job_complete':
      case 'job_error':
      case 'job_status':
        subscription.onProgress(data as ProgressUpdate);

        // Handle specific completion
        if (data.type === 'job_complete' && subscription.onComplete) {
          subscription.onComplete(data.result);
        }
        break;

      case 'subscription_result':
        console.log(`Subscription result for job ${data.job_id}: ${data.success}`);
        break;

      case 'pong':
        // Heartbeat response
        break;

      case 'error':
        subscription.onError(new Error(data.message));
        break;

      default:
        console.log(`Unhandled WebSocket message type: ${data.type}`);
    }
  }

  private startHeartbeat(jobId: string): void {
    const timer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      } else {
        this.stopHeartbeat(jobId);
      }
    }, this.heartbeatInterval);

    this.heartbeatTimers.set(jobId, timer);
  }

  private stopHeartbeat(jobId: string): void {
    const timer = this.heartbeatTimers.get(jobId);
    if (timer) {
      clearInterval(timer);
      this.heartbeatTimers.delete(jobId);
    }
  }

  private handleReconnect(jobId: string): void {
    const attempts = this.reconnectAttempts.get(jobId) || 0;

    if (attempts >= this.maxReconnectAttempts) {
      console.error(`Max reconnection attempts reached for job ${jobId}`);
      this.startPolling(jobId);
      return;
    }

    this.reconnectAttempts.set(jobId, attempts + 1);

    const timer = setTimeout(async () => {
      try {
        console.log(`Attempting to reconnect WebSocket for job ${jobId} (attempt ${attempts + 1})`);
        await this.connectWebSocket(jobId);
      } catch (error) {
        console.log(`Reconnection attempt ${attempts + 1} failed for job ${jobId}`);
        this.handleReconnect(jobId);
      }
    }, this.reconnectDelay * (attempts + 1)); // Exponential backoff

    this.reconnectTimers.set(jobId, timer);
  }

  private startPolling(jobId: string): void {
    console.log(`Starting polling fallback for job ${jobId}`);

    // Initial poll
    this.pollJobStatus(jobId);

    // Set up interval polling
    const timer = setInterval(() => {
      this.pollJobStatus(jobId);
    }, this.pollingInterval);

    this.fallbackPollingIntervals.set(jobId, timer);

    // Notify connection change
    const subscription = this.subscriptions.get(jobId);
    if (subscription?.onConnectionChange) {
      subscription.onConnectionChange(false); // Using polling
    }
  }

  private stopPolling(jobId: string): void {
    const timer = this.fallbackPollingIntervals.get(jobId);
    if (timer) {
      clearInterval(timer);
      this.fallbackPollingIntervals.delete(jobId);
    }
  }

  private async pollJobStatus(jobId: string): Promise<void> {
    const subscription = this.subscriptions.get(jobId);
    if (!subscription) return;

    try {
      const response = await fetch(`/api/presentations/jobs/${jobId}`, {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to poll job status: ${response.status}`);
      }

      const jobStatus = await response.json();

      // Convert job status to progress update
      const progressUpdate: ProgressUpdate = {
        job_id: jobId,
        update_type: 'job_status',
        timestamp: new Date().toISOString(),
        job_status: jobStatus
      };

      subscription.onProgress(progressUpdate);

      // Stop polling if job is complete
      if (jobStatus.status === 'completed') {
        this.stopPolling(jobId);
        if (subscription.onComplete) {
          subscription.onComplete(jobStatus);
        }
      } else if (jobStatus.status === 'failed' || jobStatus.status === 'cancelled') {
        this.stopPolling(jobId);
        subscription.onError(new Error(jobStatus.error_message || 'Job failed'));
      }

    } catch (error) {
      console.error(`Failed to poll job status for ${jobId}:`, error);
      // Don't call subscription.onError to avoid too many error notifications
    }
  }

  private cleanupTimers(jobId: string): void {
    // Cleanup reconnect timer
    const reconnectTimer = this.reconnectTimers.get(jobId);
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      this.reconnectTimers.delete(jobId);
    }

    // Cleanup heartbeat timer
    this.stopHeartbeat(jobId);

    // Reset reconnect attempts
    this.reconnectAttempts.delete(jobId);
  }

  // Utility methods
  formatTimeRemaining(seconds?: number): string {
    if (!seconds || seconds < 0) return '';

    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  }

  getStepIcon(step: string): string {
    const iconMap: Record<string, string> = {
      'initializing': '⚙️',
      'fetching_lesson': '📚',
      'validating_access': '🔐',
      'marking_stale': '🗑️',
      'building_scaffold': '🏗️',
      'creating_presentation': '📝',
      'llm_polish_request': '🤖',
      'llm_polish_processing': '✨',
      'updating_slides': '💾',
      'generating_exports': '📤',
      'finalizing': '✅',
      'completed': '🎉'
    };

    return iconMap[step] || '📌';
  }

  getStepStatusIcon(status: string): string {
    const iconMap: Record<string, string> = {
      'pending': '⏸️',
      'running': '⏳',
      'completed': '✅',
      'failed': '❌',
      'skipped': '⏭️'
    };

    return iconMap[status] || '❓';
  }

  isStepActive(currentStep: string, step: string): boolean {
    return currentStep === step;
  }

  isStepCompleted(status: string): boolean {
    return status === 'completed' || status === 'skipped';
  }

  isStepFailed(status: string): boolean {
    return status === 'failed';
  }

  getProgressColor(progress: number): string {
    if (progress >= 80) return 'bg-green-500';
    if (progress >= 50) return 'bg-blue-500';
    if (progress >= 25) return 'bg-yellow-500';
    return 'bg-red-500';
  }

  getStepProgressStatus(overallProgress: number): {
    color: string;
    text: string;
    icon: string;
  } {
    if (overallProgress >= 100) {
      return {
        color: 'text-green-600',
        text: 'Completed',
        icon: '🎉'
      };
    } else if (overallProgress >= 75) {
      return {
        color: 'text-blue-600',
        text: 'Finalizing',
        icon: '🔄'
      };
    } else if (overallProgress >= 50) {
      return {
        color: 'text-purple-600',
        text: 'Processing',
        icon: '⚙️'
      };
    } else if (overallProgress >= 25) {
      return {
        color: 'text-yellow-600',
        text: 'Building',
        icon: '🏗️'
      };
    } else {
      return {
        color: 'text-gray-600',
        text: 'Starting',
        icon: '🚀'
      };
    }
  }
}

// Singleton instance
export const progressService = new ProgressService();

export default progressService;
