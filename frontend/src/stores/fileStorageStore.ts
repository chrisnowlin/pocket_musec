import { create } from 'zustand';
import type { FileMetadata, FileStats } from '../types/fileStorage';

interface FileStorageState {
  files: FileMetadata[];
  fileStats: FileStats | null;
  loading: boolean;
  error: string;
  currentPage: number;
  totalCount: number;
  selectedStatus: string;
  setFiles: (files: FileMetadata[], totalCount?: number) => void;
  setFileStats: (stats: FileStats | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string) => void;
  setCurrentPage: (page: number) => void;
  setSelectedStatus: (status: string) => void;
}

export const useFileStorageStore = create<FileStorageState>((set) => ({
  files: [],
  fileStats: null,
  loading: false,
  error: '',
  currentPage: 0,
  totalCount: 0,
  selectedStatus: 'all',
  setFiles: (files, totalCount) => set((state) => ({
    files,
    totalCount: totalCount ?? state.totalCount,
  })),
  setFileStats: (fileStats) => set({ fileStats }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setCurrentPage: (currentPage) => set({ currentPage }),
  setSelectedStatus: (selectedStatus) => set({ selectedStatus }),
}));
