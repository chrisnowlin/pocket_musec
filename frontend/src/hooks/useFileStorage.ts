import { useCallback, useEffect } from 'react';
import { keepPreviousData, useQuery, useQueryClient } from '@tanstack/react-query';
import type { FileMetadata, FileStats } from '../types/fileStorage';
import { ingestionService } from '../services/ingestionService';
import { FILE_STORAGE_CONSTANTS, FILE_STORAGE_MESSAGES } from '../constants/unified';
import { useFileStorageStore } from '../stores/fileStorageStore';

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
  loadFiles: (status?: string, page?: number) => Promise<void>;
  loadFileStats: () => Promise<void>;
  downloadFile: (fileId: string, filename: string) => Promise<void>;
  getFileMetadata: (fileId: string) => Promise<FileMetadata | null>;
  setStatusFilter: (status: string) => void;
  setCurrentPage: (page: number) => void;
  refresh: () => Promise<void>;
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

  const files = useFileStorageStore((state) => state.files);
  const fileStats = useFileStorageStore((state) => state.fileStats);
  const loading = useFileStorageStore((state) => state.loading);
  const error = useFileStorageStore((state) => state.error);
  const currentPage = useFileStorageStore((state) => state.currentPage);
  const totalCount = useFileStorageStore((state) => state.totalCount);
  const selectedStatus = useFileStorageStore((state) => state.selectedStatus);
  const setFiles = useFileStorageStore((state) => state.setFiles);
  const setFileStats = useFileStorageStore((state) => state.setFileStats);
  const setLoading = useFileStorageStore((state) => state.setLoading);
  const setError = useFileStorageStore((state) => state.setError);
  const setCurrentPage = useFileStorageStore((state) => state.setCurrentPage);
  const setSelectedStatus = useFileStorageStore((state) => state.setSelectedStatus);

  const queryClient = useQueryClient();

  interface FilesResponse {
    files: FileMetadata[];
    total: number;
  }

  const fetchFiles = useCallback(async (statusValue: string, pageValue: number): Promise<FilesResponse> => {
    const statusFilter = statusValue === 'all' ? undefined : statusValue;
    const response = await ingestionService.getUploadedFiles(
      statusFilter,
      pageSize,
      pageValue * pageSize
    );

    if (response.success && response.files) {
      return {
        files: response.files,
        total: response.pagination?.total ?? response.files.length,
      };
    }

    throw new Error(response.error || FILE_STORAGE_MESSAGES.UPLOAD_FAILED);
  }, [pageSize]);

  const fetchStats = useCallback(async (): Promise<FileStats> => {
    const response = await ingestionService.getFileStatistics();
    if (response.success && response.database_stats) {
      return response.database_stats;
    }
    throw new Error(FILE_STORAGE_MESSAGES.UPLOAD_FAILED);
  }, []);

  const filesQuery = useQuery<FilesResponse, Error>({
    queryKey: ['files', selectedStatus, currentPage, pageSize],
    queryFn: () => fetchFiles(selectedStatus, currentPage),
    placeholderData: keepPreviousData,
    enabled: autoLoad,
  });

  const statsQuery = useQuery<FileStats, Error>({
    queryKey: ['fileStats'],
    queryFn: fetchStats,
    enabled: autoLoad,
  });

  useEffect(() => {
    if (filesQuery.data) {
      setFiles(filesQuery.data.files, filesQuery.data.total);
      setError('');
    }
  }, [filesQuery.data, setFiles, setError]);

  useEffect(() => {
    if (filesQuery.error) {
      setError(filesQuery.error.message || FILE_STORAGE_MESSAGES.UPLOAD_FAILED);
    }
  }, [filesQuery.error, setError]);

  useEffect(() => {
    if (statsQuery.data) {
      setFileStats(statsQuery.data);
    }
  }, [statsQuery.data, setFileStats]);

  useEffect(() => {
    if (statsQuery.error) {
      console.error('Failed to load file stats:', statsQuery.error);
    }
  }, [statsQuery.error]);

  const loadFiles = useCallback(async (status?: string, page?: number) => {
    const statusValue = status ?? selectedStatus;
    const pageValue = page ?? currentPage;
    setSelectedStatus(statusValue);
    setCurrentPage(pageValue);
    const data = await queryClient.fetchQuery<FilesResponse>({
      queryKey: ['files', statusValue, pageValue, pageSize],
      queryFn: () => fetchFiles(statusValue, pageValue),
    });
    setFiles(data.files, data.total);
  }, [selectedStatus, currentPage, setSelectedStatus, setCurrentPage, queryClient, pageSize, fetchFiles, setFiles]);

  const loadFileStats = useCallback(async () => {
    const stats = await queryClient.fetchQuery<FileStats>({
      queryKey: ['fileStats'],
      queryFn: fetchStats,
    });
    setFileStats(stats);
  }, [queryClient, fetchStats, setFileStats]);

  const downloadFile = useCallback(async (fileId: string, filename: string) => {
    try {
      const blob = await ingestionService.downloadFile(fileId);
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(anchor);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : FILE_STORAGE_MESSAGES.DOWNLOAD_FAILED;
      setError(errorMessage);
      throw err;
    }
  }, [setError]);

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
  }, [setSelectedStatus, setCurrentPage]);

  const refresh = useCallback(async () => {
    await Promise.all([
      loadFiles(selectedStatus, currentPage),
      loadFileStats(),
    ]);
  }, [loadFiles, loadFileStats, selectedStatus, currentPage]);

  useEffect(() => {
    setLoading(filesQuery.isFetching);
  }, [filesQuery.isFetching, setLoading]);

  useEffect(() => {
    if (defaultStatus && selectedStatus !== defaultStatus) {
      setSelectedStatus(defaultStatus);
    }
  }, [defaultStatus, selectedStatus, setSelectedStatus]);

  const hasFiles = files.length > 0;
  const hasErrors = error.length > 0;
  const totalPages = Math.ceil(totalCount / pageSize);
  const recentlyUploaded = files
    .filter(file => file.ingestionStatus === 'completed')
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

export function useFileValidation() {
  const validateFile = useCallback((file: File): string | null => {
    if (file.size > FILE_STORAGE_CONSTANTS.MAX_FILE_SIZE) {
      return FILE_STORAGE_MESSAGES.FILE_TOO_LARGE;
    }

    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!FILE_STORAGE_CONSTANTS.ALLOWED_EXTENSIONS.includes(extension)) {
      return FILE_STORAGE_MESSAGES.INVALID_FILE_TYPE;
    }

    if (!FILE_STORAGE_CONSTANTS.SUPPORTED_MIME_TYPES.includes(file.type)) {
      return FILE_STORAGE_MESSAGES.INVALID_FILE_TYPE;
    }

    return null;
  }, []);

  const validateMultipleFiles = useCallback((files: File[]) => {
    const valid: File[] = [];
    const invalid: Array<{ file: File; error: string }> = [];

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
