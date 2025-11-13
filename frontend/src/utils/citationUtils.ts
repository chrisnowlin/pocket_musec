import type { EnhancedCitation, Citation } from '../types/fileStorage';

/**
 * Fallback citation data when files are unavailable
 */
export function createFallbackCitation(citation: Citation): EnhancedCitation {
  return {
    id: citation.id,
    citation_number: citation.citation_number,
    source_title: citation.source_title,
    source_type: citation.source_type,
    citation_text: citation.citation_text,
    page_number: citation.page_number,
    excerpt: citation.excerpt,
    is_file_available: false,
    can_download: false,
  };
}

/**
 * Handle mixed old/new citation formats
 */
export function normalizeCitations(citations: any[]): (Citation | string)[] {
  return citations.map(citation => {
    if (typeof citation === 'string') {
      return citation; // Legacy string format
    }
    
    // Check if it's a proper Citation object
    if (citation && typeof citation === 'object' && 'id' in citation) {
      return citation as Citation;
    }
    
    // Fallback to string
    return citation.source_title || JSON.stringify(citation);
  });
}

/**
 * Filter citations by availability
 */
export function filterCitationsByAvailability(
  citations: EnhancedCitation[]
): {
  available: EnhancedCitation[];
  unavailable: EnhancedCitation[];
  downloadable: EnhancedCitation[];
} {
  const available = citations.filter(c => c.is_file_available);
  const unavailable = citations.filter(c => !c.is_file_available);
  const downloadable = citations.filter(c => c.is_file_available && c.can_download);

  return { available, unavailable, downloadable };
}

/**
 * Sort citations by relevance and availability
 */
export function sortCitations(citations: EnhancedCitation[]): EnhancedCitation[] {
  return [...citations].sort((a, b) => {
    // First sort by availability (available first)
    if (a.is_file_available && !b.is_file_available) return -1;
    if (!a.is_file_available && b.is_file_available) return 1;
    
    // Then by downloadability (downloadable first)
    if (a.can_download && !b.can_download) return -1;
    if (!a.can_download && b.can_download) return 1;
    
    // Finally by citation number
    return a.citation_number - b.citation_number;
  });
}

/**
 * Generate citation summary text
 */
export function generateCitationSummary(citations: EnhancedCitation[]): string {
  const { available, unavailable, downloadable } = filterCitationsByAvailability(citations);
  
  const parts = [];
  
  if (citations.length === 0) {
    return 'No citations';
  }
  
  parts.push(`${citations.length} source${citations.length !== 1 ? 's' : ''}`);
  
  if (available.length > 0) {
    parts.push(`${available.length} available`);
  }
  
  if (downloadable.length > 0) {
    parts.push(`${downloadable.length} downloadable`);
  }
  
  if (unavailable.length > 0) {
    parts.push(`${unavailable.length} unavailable`);
  }
  
  return parts.join(', ');
}

/**
 * Validate citation data
 */
export function validateCitation(citation: any): boolean {
  if (!citation || typeof citation !== 'object') {
    return false;
  }
  
  const requiredFields = ['id', 'source_title', 'source_type'];
  return requiredFields.every(field => field in citation);
}

/**
 * Sanitize citation text
 */
export function sanitizeCitationText(text: string): string {
  if (!text || typeof text !== 'string') {
    return '';
  }
  
  // Remove potentially harmful content
  return text
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<[^>]*>/g, '')
    .trim();
}

/**
 * Get citation type display information
 */
export function getCitationTypeInfo(sourceType: string) {
  const typeMap = {
    standard: {
      icon: '📋',
      label: 'Music Standard',
      color: 'text-blue-700',
      bgColor: 'bg-blue-100',
    },
    objective: {
      icon: '🎯',
      label: 'Learning Objective',
      color: 'text-green-700',
      bgColor: 'bg-green-100',
    },
    document: {
      icon: '📄',
      label: 'Document',
      color: 'text-ink-700',
      bgColor: 'bg-ink-100',
    },
    image: {
      icon: '🖼️',
      label: 'Image',
      color: 'text-purple-700',
      bgColor: 'bg-purple-100',
    },
  };
  
  return typeMap[sourceType as keyof typeof typeMap] || {
    icon: '📝',
    label: 'Source',
    color: 'text-ink-700',
    bgColor: 'bg-ink-100',
  };
}

/**
 * Handle citation errors gracefully
 */
export function handleCitationError(error: Error, context: string): {
  message: string;
  shouldRetry: boolean;
  fallbackData?: EnhancedCitation[];
} {
  console.error(`Citation error in ${context}:`, error);
  
  // Check for specific error types
  if (error.message.includes('NetworkError') || error.message.includes('fetch')) {
    return {
      message: 'Network error while loading citations. Please check your connection.',
      shouldRetry: true,
    };
  }
  
  if (error.message.includes('Unauthorized') || error.message.includes('401')) {
    return {
      message: 'You may not have permission to access these citations.',
      shouldRetry: false,
    };
  }
  
  if (error.message.includes('Not Found') || error.message.includes('404')) {
    return {
      message: 'Citation data not found. The source may have been deleted.',
      shouldRetry: false,
    };
  }
  
  // Generic error
  return {
    message: 'Unable to load citation information. Please try again later.',
    shouldRetry: true,
  };
}

/**
 * Debounce citation loading
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Check if citation is recent (within last 30 days)
 */
export function isRecentCitation(citation: EnhancedCitation): boolean {
  if (!citation.file_metadata?.created_at) {
    return false;
  }
  
  const createdDate = new Date(citation.file_metadata.created_at);
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
  
  return createdDate > thirtyDaysAgo;
}