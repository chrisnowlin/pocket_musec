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
  error?: string;
}

class IngestionService {
  private baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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

  async ingestDocument(request: IngestionRequest): Promise<IngestionResults> {
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

    return result.results || {};
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
      const results = await this.ingestDocument({ file, advancedOption });
      const classification = await this.classifyDocument(file);
      
      return {
        success: true,
        classification,
        results
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