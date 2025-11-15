export interface FileMetadata {
  id: string;
  file_id: string;
  original_filename: string;
  file_hash: string;
  file_size: number;
  mime_type: string;
  document_type?: string;
  confidence?: number;
  ingestion_status: 'uploaded' | 'processing' | 'completed' | 'error';
  created_at: string;
  updated_at: string;
  error_message?: string;
  metadata?: Record<string, any>;
}

export interface FileStorageResponse {
  success: boolean;
  file?: FileMetadata;
  files?: FileMetadata[];
  pagination?: {
    limit: number;
    offset: number;
    total: number;
    count: number;
  };
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

export interface FileStats {
  total_files: number;
  total_bytes: number;
  total_mb: number;
  completed_files: number;
  processing_files: number;
  error_files: number;
  uploaded_files: number;
  files_by_type: Record<string, number>;
}

export interface StorageStats {
  total_files: number;
  total_bytes: number;
  total_bytes_mb: number;
  file_counts_by_extension: Record<string, number>;
  storage_root: string;
  error?: string;
}

export interface DuplicateFileWarning {
  duplicate: boolean;
  message: string;
  existing_file: {
    id: string;
    filename: string;
    upload_date: string;
    status: string;
  };
}

export const FILE_STATUS_COLORS = {
  uploaded: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  processing: 'bg-blue-100 text-blue-800 border-blue-200',
  completed: 'bg-green-100 text-green-800 border-green-200',
  error: 'bg-red-100 text-red-800 border-red-200',
} as const;

export const FILE_STATUS_LABELS = {
  uploaded: 'Uploaded',
  processing: 'Processing',
  completed: 'Completed',
  error: 'Error',
} as const;

export const DOCUMENT_TYPE_ICONS = {
  standards: '📋',
  unpacking: '📚',
  alignment: '🔗',
  glossary: '📝',
  guide: '📖',
  unknown: '❓',
} as const;

export const DOCUMENT_TYPE_LABELS = {
  standards: 'NC Music Standards',
  unpacking: 'Grade-Level Unpacking',
  alignment: 'Alignment Matrices',
  glossary: 'Glossary & Reference',
  guide: 'Implementation Guides',
  unknown: 'Unknown Document',
} as const;

export const SUPPORTED_FILE_TYPES = {
  'application/pdf': { icon: '📄', label: 'PDF Document' },
  'text/plain': { icon: '📝', label: 'Text File' },
  'application/msword': { icon: '📄', label: 'Word Document' },
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': { icon: '📄', label: 'Word Document' },
} as const;

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB in bytes
export const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.doc', '.docx'];

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Deprecated: Use formatDateTime from '../../lib/dateUtils' instead
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// Citation-related types
export interface Citation {
  id: string;
  lesson_id: string;
  source_type: 'standard' | 'objective' | 'document' | 'image';
  source_id: string;
  source_title: string;
  page_number?: number;
  excerpt?: string;
  citation_text: string;
  citation_number: number;
  file_id?: string;
  created_at?: string;
}

export interface FileCitation {
  citation: Citation;
  file_metadata?: FileMetadata;
  is_file_available: boolean;
  download_url?: string;
}

export interface EnhancedCitation {
  id: string;
  citation_number: number;
  source_title: string;
  source_type: string;
  file_metadata?: {
    id: string;
    file_id: string;
    original_filename: string;
    file_size: number;
    mime_type: string;
    created_at: string;
    document_type?: string;
  };
  page_number?: number;
  excerpt?: string;
  citation_text: string;
  is_file_available: boolean;
  can_download: boolean;
  formatted_date?: string;
  relative_time?: string;
}

export interface CitationServiceResponse {
  success: boolean;
  citations?: Citation[];
  enhanced_citations?: EnhancedCitation[];
  error?: string;
}

// Utility functions for citation file information
export function formatCitationFileInfo(citation: Citation, fileMetadata?: FileMetadata): Partial<EnhancedCitation> {
  if (!fileMetadata) {
    return {
      is_file_available: false,
      can_download: false,
    };
  }

  return {
    file_metadata: {
      id: fileMetadata.id,
      file_id: fileMetadata.file_id,
      original_filename: fileMetadata.original_filename,
      file_size: fileMetadata.file_size,
      mime_type: fileMetadata.mime_type,
      created_at: fileMetadata.created_at,
      document_type: fileMetadata.document_type,
    },
    is_file_available: true,
    can_download: fileMetadata.ingestion_status === 'completed',
    formatted_date: formatDate(fileMetadata.created_at),
    relative_time: getRelativeTime(fileMetadata.created_at),
  };
}

export function getCitationDisplayText(citation: EnhancedCitation): string {
  const parts = [];
  
  if (citation.citation_text) {
    parts.push(citation.citation_text);
  }
  
  if (citation.file_metadata) {
    parts.push(`Source: ${citation.file_metadata.original_filename}`);
  }
  
  if (citation.page_number) {
    parts.push(`Page ${citation.page_number}`);
  }
  
  return parts.join(' • ');
}

export function getCitationIcon(citation: EnhancedCitation): string {
  if (citation.file_metadata?.document_type) {
    return DOCUMENT_TYPE_ICONS[citation.file_metadata.document_type as keyof typeof DOCUMENT_TYPE_ICONS] || '📄';
  }
  
  switch (citation.source_type) {
    case 'standard':
      return '📋';
    case 'objective':
      return '🎯';
    case 'document':
      return '📄';
    case 'image':
      return '🖼️';
    default:
      return '📝';
  }
}

export function getCitationTypeLabel(citation: EnhancedCitation): string {
  if (citation.file_metadata?.document_type) {
    return DOCUMENT_TYPE_LABELS[citation.file_metadata.document_type as keyof typeof DOCUMENT_TYPE_LABELS] || 'Document';
  }
  
  switch (citation.source_type) {
    case 'standard':
      return 'Music Standard';
    case 'objective':
      return 'Learning Objective';
    case 'document':
      return 'Document';
    case 'image':
      return 'Image';
    default:
      return 'Source';
  }
}

export function getRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`;
  
  return formatDate(dateString);
}