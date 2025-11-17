/* Enhanced export progress service with comprehensive tracking and error handling */

import { progressService } from './progressService';

// Export progress types
export interface ExportStepProgress {
  step: string;
  name: string;
  description: string;
  format: 'json' | 'markdown' | 'pptx' | 'pdf';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'cancelled';
  progress: number;
  weight: number;
  started_at?: string;
  completed_at?: string;
  estimated_duration?: number;
  actual_duration?: number;
  error_message?: string;
  error_code?: string;
  details: Record<string, any>;
}

export interface ExportFormatProgress {
  export_id: string;
  format: 'json' | 'markdown' | 'pptx' | 'pdf';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'retrying';
  overall_progress: number;
  file_size_bytes?: number;
  filename?: string;
  quality_score?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_code?: string;
  error_message?: string;
  retry_count: number;
  max_retries: number;
  last_updated: string;
  current_step?: {
    step: string;
    name: string;
    description: string;
    progress: number;
    status: string;
    started_at?: string;
    message: string;
    estimated_duration?: number;
    actual_duration?: number;
  };
  estimated_time_remaining?: number;
  steps: ExportStepProgress[];
}

export interface BulkExportProgress {
  bulk_export_id: string;
  presentation_id: string;
  user_id: string;
  formats: string[];
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'retrying';
  overall_progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  successful_exports: string[];
  failed_exports: string[];
  cancelled_exports: string[];
  error_message?: string;
  concurrent_exports: number;
  download_zip_path?: string;
  export_progress: Record<string, ExportFormatProgress>;
  progress_summary: {
    bulk_export_id: string;
    presentation_id: string;
    status: string;
    overall_progress: number;
    total_formats: number;
    successful_exports: number;
    failed_exports: number;
    cancelled_exports: number;
    running_exports: number;
    pending_exports: number;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    estimated_completion_time?: string;
    download_zip_path?: string;
    formats: Record<string, {
      status: string;
      progress: number;
      file_size_bytes?: number;
      filename?: string;
      error_message?: string;
      current_step?: any;
    }>;
  };
}

export interface ExportProgressUpdate {
  export_id: string;
  bulk_export_id?: string;
  format?: string;
  update_type: 'export_progress' | 'format_complete' | 'format_failed' | 'export_complete' | 'export_failed' | 'bulk_export_progress';
  timestamp: string;
  message: string;
  format_progress?: ExportFormatProgress;
  bulk_progress?: BulkExportProgress;
}

export interface ExportSubscription {
  exportId?: string;
  bulkExportId?: string;
  onProgress: (update: ExportProgressUpdate) => void;
  onError: (error: Error) => void;
  onComplete?: (result: any) => void;
  onConnectionChange?: (connected: boolean) => void;
}

export interface ExportOptions {
  include_metadata?: boolean;
  include_teacher_script?: boolean;
  quality_settings?: Record<string, any>;
  pdf_options?: Record<string, any>;
  pptx_options?: Record<string, any>;
  batch_size?: number;
  max_retries?: number;
  timeout_seconds?: number;
}

export interface ExportRequest { presentationId: string;
  format: 'json' | 'markdown' | 'pptx' | 'pdf';
  options?: ExportOptions;
  track_progress?: boolean;
}

export interface BulkExportRequest { presentationId: string;
  formats: string[];
  options?: ExportOptions;
  create_zip?: boolean;
  track_progress?: boolean;
}

export interface ExportAnalytics {
  user_id: string;
  time_window_hours: number;
  total_exports: number;
  successful_exports: number;
  failed_exports: number;
  success_rate: number;
  formats_used: Record<string, number>;
  average_processing_time_seconds: number;
  average_file_size_bytes: number;
  most_popular_format?: string;
  performance_summary: Record<string, any>;
}

export class ExportProgressService {
  private subscriptions: Map<string, ExportSubscription> = new Map();
  private pollIntervals: Map<string, NodeJS.Timeout> = new Map();
  private apiClient: any; // Will be initialized later

  constructor() {
    // Initialize API client
    this.initApiClient();
  }

  private initApiClient() {
    // This would be your API client implementation
    // For now, we'll use fetch directly
  }

  // Export management methods
  async startExport(request: ExportRequest): Promise<{
    export_id?: string;
    presentation_id: string;
    format: string;
    status: string;
    track_progress: boolean;
    websocket_url?: string;
    created_at: string;
  }> {
    try {
      const response = await fetch('/api/exports/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`,
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || 'Failed to start export');
      }

      return await response.json();
    } catch (error: any) {
      console.error('Failed to start export:', error);
      throw error;
    }
  }

  async startBulkExport(request: BulkExportRequest): Promise<{
    bulk_export_id: string;
    presentation_id: string;
    formats: string[];
    status: string;
    create_zip: boolean;
    concurrent_exports: number;
    websocket_url: string;
    created_at: string;
  }> {
    try {
      const response = await fetch('/api/exports/bulk-export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`,
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || 'Failed to start bulk export');
      }

      return await response.json();
    } catch (error: any) {
      console.error('Failed to start bulk export:', error);
      throw error;
    }
  }

  // Progress tracking methods
  subscribeToExportProgress(subscription: ExportSubscription): Promise<void> {
    return new Promise((resolve, reject) => {
      const key = subscription.exportId || subscription.bulkExportId;
      if (!key) {
        reject(new Error('Either exportId or bulkExportId must be provided'));
        return;
      }

      // Store subscription
      this.subscriptions.set(key, subscription);

      // Try WebSocket first
      this.connectWebSocket(subscription)
        .then(() => {
          console.log('Connected to WebSocket for export progress');
          resolve();
        })
        .catch((error) => {
          console.warn('WebSocket failed, falling back to polling:', error);
          this.startPolling(subscription);
          resolve();
        });
    });
  }

  unsubscribeFromProgress(exportId?: string, bulkExportId?: string): void {
    const key = exportId || bulkExportId;
    if (!key) return;

    // Remove subscription
    this.subscriptions.delete(key);

    // Clean up polling
    const interval = this.pollIntervals.get(key);
    if (interval) {
      clearInterval(interval);
      this.pollIntervals.delete(key);
    }

    // Clean up WebSocket subscription
    if (exportId) {
      progressService.unsubscribe(exportId);
    }
  }

  private async connectWebSocket(subscription: ExportSubscription): Promise<void> {
    if (!subscription.exportId && !subscription.bulkExportId) {
      throw new Error('Cannot connect to WebSocket without export ID');
    }

    // Use the existing progress service WebSocket
    // We'll map export progress updates to export-specific progress
    const jobId = subscription.exportId || subscription.bulkExportId!;
    const progressSubscription = {
      jobId,
      onProgress: (update: any) => {
        // Convert generic progress update to export progress update
        const exportUpdate: ExportProgressUpdate = this.convertProgressUpdate(update, subscription);
        subscription.onProgress(exportUpdate);

        if (update.update_type === 'job_complete' && subscription.onComplete) {
          subscription.onComplete(update.result);
        }
      },
      onError: (error: Error) => {
        subscription.onError(error);
      },
      onComplete: subscription.onComplete,
      onConnectionChange: subscription.onConnectionChange,
    };

    await progressService.subscribe(progressSubscription);
  }

  private startPolling(subscription: ExportSubscription): void {
    const key = subscription.exportId || subscription.bulkExportId;
    if (!key) return;

    const interval = setInterval(async () => {
      try {
        const progress = subscription.exportId
          ? await this.getExportProgress(subscription.exportId)
          : await this.getBulkExportProgress(subscription.bulkExportId!);

        if (progress) {
          const update: ExportProgressUpdate = {
            export_id: subscription.exportId || subscription.bulkExportId!,
            bulk_export_id: subscription.bulkExportId,
            format: 'format' in progress ? progress.format : undefined,
            update_type: subscription.bulkExportId ? 'bulk_export_progress' : 'export_progress',
            timestamp: new Date().toISOString(),
            message: `Progress: ${progress.overall_progress.toFixed(1)}%`,
            format_progress: (progress as any).format_progress,
            bulk_progress: (progress as any).bulk_progress,
          };

          subscription.onProgress(update);

          // Stop polling if complete
          if (progress.status === 'completed' || progress.status === 'failed') {
            this.unsubscribeFromProgress(subscription.exportId, subscription.bulkExportId);
            if (progress.status === 'completed' && subscription.onComplete) {
              subscription.onComplete(progress);
            } else if (progress.status === 'failed') {
              subscription.onError(new Error(progress.error_message || 'Export failed'));
            }
          }
        }
      } catch (error: any) {
        console.error('Polling error:', error);
        // Don't call onError to avoid spamming errors
      }
    }, 2000);

    this.pollIntervals.set(key, interval);
  }

  private convertProgressUpdate(update: any, subscription: ExportSubscription): ExportProgressUpdate {
    // Convert generic progress update to export-specific update
    return {
      export_id: update.job_id || subscription.exportId || subscription.bulkExportId!,
      bulk_export_id: subscription.bulkExportId,
      update_type: update.update_type,
      timestamp: update.timestamp,
      message: update.message || '',
      format_progress: update.progress,
      bulk_progress: update.progress,
    };
  }

  // API methods
  async getExportProgress(exportId: string): Promise<ExportFormatProgress | null> {
    try {
      const response = await fetch(`/api/exports/progress/${exportId}`, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
        },
      });

      if (!response.ok) {
        if (response.status === 404) return null;
        throw new Error('Failed to get export progress');
      }

      return await response.json();
    } catch (error: any) {
      console.error('Failed to get export progress:', error);
      return null;
    }
  }

  async getBulkExportProgress(bulkExportId: string): Promise<BulkExportProgress | null> {
    try {
      const response = await fetch(`/api/exports/bulk-progress/${bulkExportId}`, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
        },
      });

      if (!response.ok) {
        if (response.status === 404) return null;
        throw new Error('Failed to get bulk export progress');
      }

      return await response.json();
    } catch (error: any) {
      console.error('Failed to get bulk export progress:', error);
      return null;
    }
  }

  async cancelExport(exportId: string): Promise<void> {
    try {
      const response = await fetch(`/api/exports/exports/${exportId}/cancel`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to cancel export');
      }
    } catch (error: any) {
      console.error('Failed to cancel export:', error);
      throw error;
    }
  }

  async cancelBulkExport(bulkExportId: string): Promise<void> {
    try {
      const response = await fetch(`/api/exports/bulk-exports/${bulkExportId}/cancel`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to cancel bulk export');
      }
    } catch (error: any) {
      console.error('Failed to cancel bulk export:', error);
      throw error;
    }
  }

  async retryExport(exportId: string): Promise<void> {
    try {
      const response = await fetch(`/api/exports/exports/${exportId}/retry`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to retry export');
      }
    } catch (error: any) {
      console.error('Failed to retry export:', error);
      throw error;
    }
  }

  async downloadExportedFile(exportId: string): Promise<void> {
    try {
      const response = await fetch(`/api/exports/exports/download/${exportId}`, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to download export file');
      }

      // Get filename from headers or use default
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `export_${exportId}`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Create download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (error: any) {
      console.error('Failed to download export file:', error);
      throw error;
    }
  }

  async downloadBulkExportZip(bulkExportId: string): Promise<void> {
    try {
      const response = await fetch(`/api/exports/bulk-exports/download/${bulkExportId}`, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to download bulk export ZIP');
      }

      // Get filename from headers or use default
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `bulk_export_${bulkExportId}.zip`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Create download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (error: any) {
      console.error('Failed to download bulk export ZIP:', error);
      throw error;
    }
  }

  async listActiveExports(status?: string, limit = 50): Promise<ExportFormatProgress[]> {
    try {
      const params = new URLSearchParams();
      if (status) params.append('status', status);
      params.append('limit', limit.toString());

      const response = await fetch(`/api/exports/exports?${params}`, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to list active exports');
      }

      return await response.json();
    } catch (error: any) {
      console.error('Failed to list active exports:', error);
      return [];
    }
  }

  async getExportAnalytics(hours = 24): Promise<ExportAnalytics | null> {
    try {
      const response = await fetch(`/api/exports/analytics?hours=${hours}`, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get export analytics');
      }

      return await response.json();
    } catch (error: any) {
      console.error('Failed to get export analytics:', error);
      return null;
    }
  }

  // Utility methods
  getExportFormatIcon(format: string): string {
    const iconMap: Record<string, string> = {
      'json': '📄',
      'markdown': '📝',
      'pptx': '📊',
      'pdf': '📋',
    };
    return iconMap[format] || '📁';
  }

  getFormatColor(format: string): string {
    const colorMap: Record<string, string> = {
      'json': 'bg-blue-500',
      'markdown': 'bg-green-500',
      'pptx': 'bg-orange-500',
      'pdf': 'bg-red-500',
    };
    return colorMap[format] || 'bg-gray-500';
  }

  getStatusColor(status: string): string {
    const colorMap: Record<string, string> = {
      'pending': 'bg-gray-500',
      'running': 'bg-blue-500',
      'completed': 'bg-green-500',
      'failed': 'bg-red-500',
      'cancelled': 'bg-yellow-500',
      'retrying': 'bg-purple-500',
    };
    return colorMap[status] || 'bg-gray-500';
  }

  formatFileSize(bytes?: number): string {
    if (!bytes || bytes === 0) return 'Unknown size';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  }

  formatTimeRemaining(seconds?: number): string {
    if (!seconds || seconds < 0) return 'Unknown';
    if (seconds < 60) return `~${Math.round(seconds)}s`;
    if (seconds < 3600) return `~${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
    return `~${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  }

  getStepIcon(step: string): string {
    const iconMap: Record<string, string> = {
      'initializing': '⚙️',
      'validating_presentation': '🔐',
      'preparing_content': '📚',
      'json_serializing': '💾',
      'json_validating': '✅',
      'markdown_formatting': '📝',
      'markdown_styling': '🎨',
      'pptx_creating_presentation': '📊',
      'pptx_adding_slides': '📑',
      'pptx_applying_styles': '🎨',
      'pptx_saving': '💾',
      'pdf_creating_document': '📋',
      'pdf_adding_content': '📄',
      'pdf_formatting': '🎨',
      'pdf_rendering': '🖨️',
      'pdf_saving': '💾',
      'validating_output': '✅',
      'calculating_size': '📏',
      'generating_filename': '📝',
      'completed': '🎉',
    };
    return iconMap[step] || '📌';
  }

  getErrorMessage(error: any): { message: string; retryable: boolean; actions?: string[] } {
    if (!error) {
      return { message: 'Unknown error occurred', retryable: false };
    }

    // Check for structured error from API
    if (error.error) {
      return {
        message: error.error.message || 'Export failed',
        retryable: error.error.recovery?.retry_recommended || false,
        actions: error.error.recovery?.actions?.map((a: any) => a.label) || [],
      };
    }

    // Fallback error handling
    const message = error.message || 'Export failed';
    const retryable = !message.includes('permission') && !message.includes('not found');

    return { message, retryable };
  }

  private getAuthToken(): string {
    // This should match your auth implementation
    const auth = this.getAuth();
    return auth?.token || '';
  }

  private getAuth(): any {
    // This should match your auth implementation
    return localStorage.getItem('auth') ? JSON.parse(localStorage.getItem('auth')!) : null;
  }
}

// Singleton instance
export const exportProgressService = new ExportProgressService();

export default exportProgressService;