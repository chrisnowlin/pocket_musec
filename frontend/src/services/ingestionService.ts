import type { FileMetadata, FileStorageResponse } from '../types/fileStorage';

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
  file_metadata?: FileMetadata;
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

  async classifyDocument(file: File): Promise<DocumentClassification> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/ingestion/classify`, {
      method: 'POST',
      body: formData,
    });

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
      file_metadata: result.file_metadata,
      duplicate: result.duplicate,
      message: result.message,
      existing_file: result.existing_file,
      error: result.error
    };
  }

  async getDocumentTypes(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/ingestion/document-types`);
    
    if (!response.ok) {
      throw new Error(`Failed to get document types: ${response.statusText}`);
    }

    const result = await response.json();
    return result.documentTypes || [];
  }

  async getAdvancedOptions(documentType: string): Promise<string[]> {
    const response = await fetch(`${this.baseUrl}/ingestion/advanced-options/${documentType}`);
    
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
    
    if (!response.ok) {
      throw new Error(`Failed to download file: ${response.statusText}`);
    }

    return response.blob();
  }

  async getFileStatistics(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/ingestion/files/stats`);
    
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
        file_metadata: ingestionResponse.file_metadata,
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