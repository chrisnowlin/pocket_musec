export interface DatabaseStats {
  standards_count: number;
  objectives_count: number;
  sections_count: number;
  strategies_count: number;
  guidance_count: number;
  relationships_count: number;
  mappings_count: number;
  glossary_count: number;
  faq_count: number;
  resource_count: number;
  total_documents: number;
  last_updated: string;
}

class StatsService {
  private baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  async getIngestionStats(): Promise<DatabaseStats> {
    const response = await fetch(`${this.baseUrl}/ingestion/stats`, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get stats: ${response.statusText}`);
    }

    const result = await response.json();
    return result.stats || this.getDefaultStats();
  }

  private getDefaultStats(): DatabaseStats {
    return {
      standards_count: 0,
      objectives_count: 0,
      sections_count: 0,
      strategies_count: 0,
      guidance_count: 0,
      relationships_count: 0,
      mappings_count: 0,
      glossary_count: 0,
      faq_count: 0,
      resource_count: 0,
      total_documents: 0,
      last_updated: new Date().toISOString(),
    };
  }

  async getContentItems(contentType: string, limit: number = 100): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/ingestion/items/${contentType}?limit=${limit}`, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get ${contentType} items: ${response.statusText}`);
    }

    const result = await response.json();
    return result.items || [];
  }
}

export const statsService = new StatsService();