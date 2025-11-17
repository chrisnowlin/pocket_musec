import type { FileMetadata, FileStorageResponse } from '../types/fileStorage';

// Standardized ingestion types for harmonized responses
export interface StandardizedIngestionResponse {
  status: 'success' | 'error' | 'partial' | 'pending';
  message: string;
  data?: any;
  errors?: Array<{
    message: string;
    code?: string;
    file_path?: string;
    [key: string]: any;
  }>;
  meta?: {
    error_type?: string;
    operation_type?: string;
    user_id?: string;
    [key: string]: any;
  };
  timestamp: string;
}

export interface IngestionRequest {
  file: File;
  advancedOption?: string;
}

export interface DocumentClassification {
  fileName: string;
  documentType: {
    value: string;
    label: string;
    description: string;
    icon: string;
  };
  confidence: number;
  recommendedParser: string;
}

export interface IngestionResults {
  standards_count?: number;
  objectives_count?: number;
  sections_count?: number;
  strategies_count?: number;
  guidance_count?: number;
  relationships_count?: number;
  mappings_count?: number;
  glossary_count?: number;
  faq_count?: number;
  resource_count?: number;
  statistics?: Record<string, any>;
}

export interface IngestionResponse {
  success: boolean;
  classification?: DocumentClassification;
  results?: IngestionResults;
  fileMetadata?: FileMetadata;
  duplicate?: boolean;
  message?: string;
  existing_file?: {
    id: string;
    filename: string;
    upload_date: string;
    status: string;
  };
  error?: string;
}

class IngestionService {
  private baseUrl = (import.meta.env?.VITE_API_BASE_URL as string) || '/api';

  /**
   * Parse a standardized ingestion response
   */
  static parseStandardizedResponse(data: any): StandardizedIngestionResponse {
    if (this.isStandardizedResponse(data)) {
      return data as StandardizedIngestionResponse;
    }

    // Legacy response - normalize to standard format
    return this.normalizeLegacyResponse(data);
  }

  /**
   * Check if response follows the standardized ingestion envelope
   */
  private static isStandardizedResponse(data: any): boolean {
    return (
      data &&
      typeof data === 'object' &&
      ['success', 'error', 'partial', 'pending'].includes(data.status)
    );
  }

  /**
   * Normalize legacy responses to standardized format
   */
  private static normalizeLegacyResponse(data: any): StandardizedIngestionResponse {
    // Handle legacy image upload responses
    if (data.id && data.filename && data.fileSize) {
      return {
        status: 'success',
        message: data.message || 'Image uploaded successfully',
        data: data,
        meta: {
          error_type: 'file_processing',
          operation_type: 'single_upload'
        },
        timestamp: new Date().toISOString()
      };
    }

    // Handle legacy ingestion responses
    if (data.success !== undefined) {
      return {
        status: data.success ? 'success' : 'error',
        message: data.message || (data.success ? 'Operation completed' : 'Operation failed'),
        data: data.success ? data : undefined,
        errors: data.error ? [{ message: data.error }] : undefined,
        meta: {
          operation_type: 'document_ingestion'
        },
        timestamp: new Date().toISOString()
      };
    }

    // Fallback: treat as success
    return {
      status: 'success',
      message: 'Operation completed',
      data: data,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Normalize error responses to standardized format
   */
  private static normalizeErrorResponse(error: any): StandardizedIngestionResponse {
    let errorMessage = 'Unknown error occurred';
    let errors: any[] = [];
    let meta: any = { error_type: 'unknown' };

    if (error.response?.data) {
      const errorData = error.response.data;

      // If it's already a standardized error, return it
      if (this.isStandardizedResponse(errorData)) {
        return errorData;
      }

      // Handle FastAPI error responses
      if (errorData.detail) {
        errorMessage = typeof errorData.detail === 'string'
          ? errorData.detail
          : errorData.detail.message || 'Request failed';

        if (errorData.detail.error) {
          errors = [errorData.detail.error];
          meta.error_type = errorData.detail.error.code || 'api_error';
        }
      } else {
        errorMessage = errorData.message || errorData.detail || 'Request failed';
      }
    } else if (error.message) {
      errorMessage = error.message;
      meta.error_type = 'network_error';
    }

    return {
      status: 'error',
      message: errorMessage,
      errors: errors.length > 0 ? errors : undefined,
      meta,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Check if ingestion was successful
   */
  static isSuccessful(response: StandardizedIngestionResponse): boolean {
    return response.status === 'success';
  }

  /**
   * Check if ingestion partially succeeded
   */
  static isPartial(response: StandardizedIngestionResponse): boolean {
    return response.status === 'partial';
  }

  /**
   * Check if ingestion failed
   */
  static isFailed(response: StandardizedIngestionResponse): boolean {
    return response.status === 'error';
  }

  /**
   * Check if ingestion is pending/processing
   */
  static isPending(response: StandardizedIngestionResponse): boolean {
    return response.status === 'pending';
  }

  /**
   * Get user-friendly error message
   */
  static getUserMessage(response: StandardizedIngestionResponse): string {
    if (this.isFailed(response)) {
      return response.message || 'Processing failed';
    }

    if (this.isPartial(response)) {
      return response.message || 'Processing partially completed';
    }

    if (this.isPending(response)) {
      return response.message || 'Processing in progress';
    }

    return response.message || 'Processing completed';
  }

  private handleFeatureUnavailable(feature: string): never {
    throw new Error(`${feature} is temporarily unavailable. The document ingestion feature has been disabled.`);
  }

  async classifyDocument(file: File): Promise<DocumentClassification> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/ingestion/classify`, {
      method: 'POST',
      body: formData,
    });

    if (response.status === 404) {
      this.handleFeatureUnavailable('Document classification');
    }

    if (!response.ok) {
      throw new Error(`Classification failed: ${response.statusText}`);
    }

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error || 'Classification failed');
    }

    return result.classification;
  }

  async ingestDocument(request: IngestionRequest): Promise<IngestionResponse> {
    const formData = new FormData();
    formData.append('file', request.file);
    
    if (request.advancedOption) {
      formData.append('advanced_option', request.advancedOption);
    }

    const response = await fetch(`${this.baseUrl}/ingestion/ingest`, {
      method: 'POST',
      body: formData,
    });

    if (response.status === 404) {
      this.handleFeatureUnavailable('Document ingestion');
    }

    if (!response.ok) {
      throw new Error(`Ingestion failed: ${response.statusText}`);
    }

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error || 'Ingestion failed');
    }

    return {
      success: result.success,
      results: result.results || {},
      fileMetadata: result.fileMetadata,
      duplicate: result.duplicate,
      message: result.message,
      existing_file: result.existing_file,
      error: result.error
    };
  }

  async getDocumentTypes(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/ingestion/document-types`);
    
    if (response.status === 404) {
      this.handleFeatureUnavailable('Document type information');
    }
    
    if (!response.ok) {
      throw new Error(`Failed to get document types: ${response.statusText}`);
    }

    const result = await response.json();
    return result.documentTypes || [];
  }

  async getAdvancedOptions(documentType: string): Promise<string[]> {
    const response = await fetch(`${this.baseUrl}/ingestion/advanced-options/${documentType}`);
    
    if (response.status === 404) {
      this.handleFeatureUnavailable('Advanced options');
    }
    
    if (!response.ok) {
      throw new Error(`Failed to get advanced options: ${response.statusText}`);
    }

    const result = await response.json();
    return result.options || [];
  }

  async getUploadedFiles(status?: string, limit: number = 50, offset: number = 0): Promise<FileStorageResponse> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    const response = await fetch(`${this.baseUrl}/ingestion/files?${params}`);
    
    if (response.status === 404) {
      this.handleFeatureUnavailable('File management');
    }
    
    if (!response.ok) {
      throw new Error(`Failed to get uploaded files: ${response.statusText}`);
    }

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error || 'Failed to get uploaded files');
    }

    return result;
  }

  async getFileMetadata(fileId: string): Promise<FileStorageResponse> {
    const response = await fetch(`${this.baseUrl}/ingestion/files/${fileId}`);
    
    if (response.status === 404) {
      this.handleFeatureUnavailable('File metadata');
    }
    
    if (!response.ok) {
      throw new Error(`Failed to get file metadata: ${response.statusText}`);
    }

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error || 'Failed to get file metadata');
    }

    return result;
  }

  async downloadFile(fileId: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/ingestion/files/${fileId}/download`);
    
    if (response.status === 404) {
      this.handleFeatureUnavailable('File download');
    }
    
    if (!response.ok) {
      throw new Error(`Failed to download file: ${response.statusText}`);
    }

    return response.blob();
  }

  async getFileStatistics(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/ingestion/files/stats`);
    
    if (response.status === 404) {
      this.handleFeatureUnavailable('File statistics');
    }
    
    if (!response.ok) {
      throw new Error(`Failed to get file statistics: ${response.statusText}`);
    }

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error || 'Failed to get file statistics');
    }

    return result;
  }

  async uploadAndClassify(file: File): Promise<IngestionResponse> {
    try {
      const classification = await this.classifyDocument(file);
      return {
        success: true,
        classification
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Classification failed'
      };
    }
  }

  async uploadAndIngest(file: File, advancedOption?: string): Promise<IngestionResponse> {
    try {
      const ingestionResponse = await this.ingestDocument({ file, advancedOption });
      
      if (ingestionResponse.duplicate) {
        // Handle duplicate file case
        return {
          success: true,
          duplicate: true,
          message: ingestionResponse.message || 'File already exists',
          existing_file: ingestionResponse.existing_file,
          error: ingestionResponse.error
        };
      }
      
      const classification = await this.classifyDocument(file);
      
      return {
        success: true,
        classification,
        results: ingestionResponse.results,
        fileMetadata: ingestionResponse.fileMetadata,
        duplicate: ingestionResponse.duplicate,
        message: ingestionResponse.message,
        existing_file: ingestionResponse.existing_file,
        error: ingestionResponse.error
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Ingestion failed'
      };
    }
  }
}

export const ingestionService = new IngestionService();