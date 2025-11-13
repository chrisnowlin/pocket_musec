import { useState, useEffect, useCallback } from 'react';
import type { FileMetadata, FileStats } from '../types/fileStorage';
import { ingestionService } from '../services/ingestionService';
import { FILE_STORAGE_CONSTANTS, FILE_STORAGE_MESSAGES } from '../constants/unified';

interface UseFileStorageOptions {
  autoLoad?: boolean;
  defaultStatus?: string;
  pageSize?: number;
}

interface UseFileStorageReturn {
  files: FileMetadata[];
  fileStats: FileStats | null;
  loading: boolean;
  error: string;
  currentPage: number;
  totalPages: number;
  totalCount: number;
  selectedStatus: string;
  
  // Actions
  loadFiles: (status?: string, page?: number) => Promise<void>;
  loadFileStats: () => Promise<void>;
  downloadFile: (fileId: string, filename: string) => Promise<void>;
  getFileMetadata: (fileId: string) => Promise<FileMetadata | null>;
  setStatusFilter: (status: string) => void;
  setCurrentPage: (page: number) => void;
  refresh: () => Promise<void>;
  
  // Computed values
  hasFiles: boolean;
  hasErrors: boolean;
  recentlyUploaded: FileMetadata[];
}

export function useFileStorage(options: UseFileStorageOptions = {}): UseFileStorageReturn {
  const {
    autoLoad = true,
    defaultStatus = 'all',
    pageSize = FILE_STORAGE_CONSTANTS.DEFAULT_PAGE_SIZE,
  } = options;

  const [files, setFiles] = useState<FileMetadata[]>([]);
  const [fileStats, setFileStats] = useState<FileStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedStatus, setSelectedStatus] = useState(defaultStatus);

  const loadFiles = useCallback(async (status?: string, page: number = 0) => {
    try {
      setLoading(true);
      setError('');
      
      const statusFilter = status || selectedStatus;
      const response = await ingestionService.getUploadedFiles(
        statusFilter === 'all' ? undefined : statusFilter,
        pageSize,
        page * pageSize
      );
      
      if (response.success && response.files) {
        setFiles(response.files);
        if (response.pagination) {
          setTotalCount(response.pagination.total);
        }
      } else {
        setError(response.error || FILE_STORAGE_MESSAGES.UPLOAD_FAILED);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : FILE_STORAGE_MESSAGES.UPLOAD_FAILED;
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [selectedStatus, pageSize]);

  const loadFileStats = useCallback(async () => {
    try {
      const response = await ingestionService.getFileStatistics();
      if (response.success && response.database_stats) {
        setFileStats(response.database_stats);
      }
    } catch (err) {
      console.error('Failed to load file stats:', err);
    }
  }, []);

  const downloadFile = useCallback(async (fileId: string, filename: string) => {
    try {
      const blob = await ingestionService.downloadFile(fileId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : FILE_STORAGE_MESSAGES.DOWNLOAD_FAILED;
      setError(errorMessage);
      throw err;
    }
  }, []);

  const getFileMetadata = useCallback(async (fileId: string): Promise<FileMetadata | null> => {
    try {
      const response = await ingestionService.getFileMetadata(fileId);
      if (response.success && response.file) {
        return response.file;
      }
      return null;
    } catch (err) {
      console.error('Failed to get file metadata:', err);
      return null;
    }
  }, []);

  const setStatusFilter = useCallback((status: string) => {
    setSelectedStatus(status);
    setCurrentPage(0);
  }, []);

  const refresh = useCallback(async () => {
    await Promise.all([
      loadFiles(selectedStatus, currentPage),
      loadFileStats()
    ]);
  }, [loadFiles, loadFileStats, selectedStatus, currentPage]);

  // Auto-load data on mount
  useEffect(() => {
    if (autoLoad) {
      loadFiles();
      loadFileStats();
    }
  }, [autoLoad]);

  // Load files when status or page changes
  useEffect(() => {
    if (autoLoad) {
      loadFiles(selectedStatus, currentPage);
    }
  }, [selectedStatus, currentPage, autoLoad, loadFiles]);

  // Computed values
  const hasFiles = files.length > 0;
  const hasErrors = error.length > 0;
  const totalPages = Math.ceil(totalCount / pageSize);
  const recentlyUploaded = files
    .filter(file => file.ingestion_status === 'completed')
    .slice(0, 3);

  return {
    files,
    fileStats,
    loading,
    error,
    currentPage,
    totalPages,
    totalCount,
    selectedStatus,
    
    loadFiles,
    loadFileStats,
    downloadFile,
    getFileMetadata,
    setStatusFilter,
    setCurrentPage,
    refresh,
    
    hasFiles,
    hasErrors,
    recentlyUploaded,
  };
}

// Utility hook for file upload validation
export function useFileValidation() {
  const validateFile = useCallback((file: File): string | null => {
    // Check file size
    if (file.size > FILE_STORAGE_CONSTANTS.MAX_FILE_SIZE) {
      return FILE_STORAGE_MESSAGES.FILE_TOO_LARGE;
    }

    // Check file extension
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!FILE_STORAGE_CONSTANTS.ALLOWED_EXTENSIONS.includes(extension)) {
      return FILE_STORAGE_MESSAGES.INVALID_FILE_TYPE;
    }

    // Check MIME type
    if (!FILE_STORAGE_CONSTANTS.SUPPORTED_MIME_TYPES.includes(file.type)) {
      return FILE_STORAGE_MESSAGES.INVALID_FILE_TYPE;
    }

    return null;
  }, []);

  const validateMultipleFiles = useCallback((files: File[]): { valid: File[], invalid: Array<{ file: File, error: string }> } => {
    const valid: File[] = [];
    const invalid: Array<{ file: File, error: string }> = [];

    files.forEach(file => {
      const error = validateFile(file);
      if (error) {
        invalid.push({ file, error });
      } else {
        valid.push(file);
      }
    });

    return { valid, invalid };
  }, [validateFile]);

  return {
    validateFile,
    validateMultipleFiles,
    MAX_FILE_SIZE: FILE_STORAGE_CONSTANTS.MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS: FILE_STORAGE_CONSTANTS.ALLOWED_EXTENSIONS,
    SUPPORTED_MIME_TYPES: FILE_STORAGE_CONSTANTS.SUPPORTED_MIME_TYPES,
  };
}