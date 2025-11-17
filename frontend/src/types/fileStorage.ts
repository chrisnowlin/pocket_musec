export interface FileMetadata {
  id: string;
  fileId: string;
  originalFilename: string;
  fileHash: string;
  fileSize: number;
  mimeType: string;
  documentType?: string;
  confidence?: number;
  ingestionStatus: 'uploaded' | 'processing' | 'completed' | 'error';
  createdAt: string;
  updatedAt: string;
  errorMessage?: string;
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
  existingFile?: {
    id: string;
    filename: string;
    uploadDate: string;
    status: string;
  };
  error?: string;
}

export interface FileStats {
  totalFiles: number;
  totalBytes: number;
  totalMb: number;
  completedFiles: number;
  processingFiles: number;
  errorFiles: number;
  uploadedFiles: number;
  filesByType: Record<string, number>;
}

export interface StorageStats {
  totalFiles: number;
  totalBytes: number;
  totalBytesMb: number;
  fileCountsByExtension: Record<string, number>;
  storageRoot: string;
  error?: string;
}

export interface DuplicateFileWarning {
  duplicate: boolean;
  message: string;
  existingFile: {
    id: string;
    filename: string;
    uploadDate: string;
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
  lessonId: string;
  sourceType: 'standard' | 'objective' | 'document' | 'image';
  sourceId: string;
  sourceTitle: string;
  pageNumber?: number;
  excerpt?: string;
  citationText: string;
  citationNumber: number;
  fileId?: string;
  createdAt?: string;
}

export interface FileCitation {
  citation: Citation;
  fileMetadata?: FileMetadata;
  isFileAvailable: boolean;
  downloadUrl?: string;
}

export interface EnhancedCitation {
  id: string;
  citationNumber: number;
  sourceTitle: string;
  sourceType: string;
  fileMetadata?: {
    id: string;
    fileId: string;
    originalFilename: string;
    fileSize: number;
    mimeType: string;
    createdAt: string;
    documentType?: string;
  };
  pageNumber?: number;
  excerpt?: string;
  citationText: string;
  isFileAvailable: boolean;
  canDownload: boolean;
  formattedDate?: string;
  relativeTime?: string;
}

export interface CitationServiceResponse {
  success: boolean;
  citations?: Citation[];
  enhancedCitations?: EnhancedCitation[];
  error?: string;
}

// Utility functions for citation file information
export function formatCitationFileInfo(citation: Citation, fileMetadata?: FileMetadata): Partial<EnhancedCitation> {
  if (!fileMetadata) {
    return {
      isFileAvailable: false,
      canDownload: false,
    };
  }

  return {
    fileMetadata: {
      id: fileMetadata.id,
      fileId: fileMetadata.fileId,
      originalFilename: fileMetadata.originalFilename,
      fileSize: fileMetadata.fileSize,
      mimeType: fileMetadata.mimeType,
      createdAt: fileMetadata.createdAt,
      documentType: fileMetadata.documentType,
    },
    isFileAvailable: true,
    canDownload: fileMetadata.ingestionStatus === 'completed',
    formattedDate: formatDate(fileMetadata.createdAt),
    relativeTime: getRelativeTime(fileMetadata.createdAt),
  };
}

export function getCitationDisplayText(citation: EnhancedCitation): string {
  const parts = [];
  
  if (citation.citationText) {
    parts.push(citation.citationText);
  }
  
  if (citation.fileMetadata) {
    parts.push(`Source: ${citation.fileMetadata.originalFilename}`);
  }
  
  if (citation.pageNumber) {
    parts.push(`Page ${citation.pageNumber}`);
  }
  
  return parts.join(' • ');
}

export function getCitationIcon(citation: EnhancedCitation): string {
  if (citation.fileMetadata?.documentType) {
    return DOCUMENT_TYPE_ICONS[citation.fileMetadata.documentType as keyof typeof DOCUMENT_TYPE_ICONS] || '📄';
  }
  
  switch (citation.sourceType) {
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
  if (citation.fileMetadata?.documentType) {
    return DOCUMENT_TYPE_LABELS[citation.fileMetadata.documentType as keyof typeof DOCUMENT_TYPE_LABELS] || 'Document';
  }
  
  switch (citation.sourceType) {
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