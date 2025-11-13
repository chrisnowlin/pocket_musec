import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ingestionService } from '../../services/ingestionService';
import { useFileStorage, useFileValidation } from '../../hooks/useFileStorage';
import FileStoragePanel from '../unified/FileStoragePanel';
import FileManager from '../unified/FileManager';
import DocumentIngestion from '../DocumentIngestion';

// Mock the ingestion service
jest.mock('../../services/ingestionService', () => ({
  ingestionService: {
    getUploadedFiles: jest.fn(),
    getFileMetadata: jest.fn(),
    downloadFile: jest.fn(),
    getFileStatistics: jest.fn(),
    classifyDocument: jest.fn(),
    ingestDocument: jest.fn(),
  },
}));

// Mock file storage types
const mockFileMetadata = {
  id: 'test-file-id',
  file_id: 'test-uuid',
  original_filename: 'test-document.pdf',
  file_hash: 'abc123',
  file_size: 1024 * 1024, // 1MB
  mime_type: 'application/pdf',
  document_type: 'standards',
  confidence: 0.95,
  ingestion_status: 'completed' as const,
  created_at: '2024-01-15T10:30:00Z',
  updated_at: '2024-01-15T10:35:00Z',
  metadata: {
    advanced_option: 'Use vision AI processing',
  },
};

const mockFileStats = {
  total_files: 5,
  total_bytes: 5 * 1024 * 1024, // 5MB
  total_mb: 5,
  completed_files: 4,
  processing_files: 1,
  error_files: 0,
  uploaded_files: 0,
  files_by_type: {
    'application/pdf': 5,
  },
};

describe('FileStorage Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('useFileValidation Hook', () => {
    it('should validate PDF files correctly', () => {
      const { validateFile } = useFileValidation();
      
      const validPdf = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const result = validateFile(validPdf);
      
      expect(result).toBeNull();
    });

    it('should reject oversized files', () => {
      const { validateFile } = useFileValidation();
      
      const oversizeFile = new File(['x'.repeat(11 * 1024 * 1024)], 'large.pdf', { type: 'application/pdf' });
      const result = validateFile(oversizeFile);
      
      expect(result).toContain('File size exceeds');
    });

    it('should reject invalid file types', () => {
      const { validateFile } = useFileValidation();
      
      const invalidFile = new File(['test'], 'test.exe', { type: 'application/executable' });
      const result = validateFile(invalidFile);
      
      expect(result).toContain('File type not supported');
    });

    it('should validate multiple files', () => {
      const { validateMultipleFiles } = useFileValidation();
      
      const validFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const invalidFile = new File(['test'], 'test.exe', { type: 'application/executable' });
      
      const result = validateMultipleFiles([validFile, invalidFile]);
      
      expect(result.valid).toHaveLength(1);
      expect(result.invalid).toHaveLength(1);
      expect(result.invalid[0].error).toContain('File type not supported');
    });
  });

  describe('FileStoragePanel Component', () => {
    it('should display file statistics when provided', () => {
      render(
        <FileStoragePanel
          recentFiles={[mockFileMetadata]}
          fileStats={mockFileStats}
        />
      );

      expect(screen.getByText('File Storage')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument(); // Total files
      expect(screen.getByText('5 MB')).toBeInTheDocument(); // Storage used
      expect(screen.getByText('4')).toBeInTheDocument(); // Completed files
      expect(screen.getByText('1')).toBeInTheDocument(); // Processing files
    });

    it('should display recent files with download option', () => {
      const onDownloadFile = jest.fn();
      
      render(
        <FileStoragePanel
          recentFiles={[mockFileMetadata]}
          fileStats={mockFileStats}
          onDownloadFile={onDownloadFile}
        />
      );

      expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
      expect(screen.getByText('Completed')).toBeInTheDocument();
      expect(screen.getByText('Download')).toBeInTheDocument();
      
      fireEvent.click(screen.getByText('Download'));
      expect(onDownloadFile).toHaveBeenCalledWith('test-uuid', 'test-document.pdf');
    });

    it('should show empty state when no files', () => {
      render(<FileStoragePanel />);
      
      expect(screen.queryByText('File Storage')).not.toBeInTheDocument();
    });
  });

  describe('FileManager Component', () => {
    it('should load and display files', async () => {
      (ingestionService.getUploadedFiles as jest.Mock).mockResolvedValue({
        success: true,
        files: [mockFileMetadata],
        pagination: { total: 1, count: 1, limit: 10, offset: 0 },
      });

      (ingestionService.getFileStatistics as jest.Mock).mockResolvedValue({
        success: true,
        database_stats: mockFileStats,
      });

      render(<FileManager />);

      await waitFor(() => {
        expect(screen.getByText('File Manager')).toBeInTheDocument();
      });

      expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
      expect(screen.getByText('All Files (5)')).toBeInTheDocument();
    });

    it('should handle file download', async () => {
      const mockBlob = new Blob(['test content'], { type: 'application/pdf' });
      (ingestionService.downloadFile as jest.Mock).mockResolvedValue(mockBlob);

      // Mock URL.createObjectURL and revokeObjectURL
      global.URL.createObjectURL = jest.fn(() => 'mock-url');
      global.URL.revokeObjectURL = jest.fn();
      
      // Mock document.createElement for download
      const mockAnchor = { click: jest.fn() };
      jest.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any);
      jest.spyOn(document.body, 'appendChild').mockImplementation();
      jest.spyOn(document.body, 'removeChild').mockImplementation();

      (ingestionService.getUploadedFiles as jest.Mock).mockResolvedValue({
        success: true,
        files: [mockFileMetadata],
        pagination: { total: 1, count: 1, limit: 10, offset: 0 },
      });

      (ingestionService.getFileStatistics as jest.Mock).mockResolvedValue({
        success: true,
        database_stats: mockFileStats,
      });

      render(<FileManager />);

      await waitFor(() => {
        expect(screen.getByText('Download')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Download'));

      await waitFor(() => {
        expect(ingestionService.downloadFile).toHaveBeenCalledWith('test-uuid', 'test-document.pdf');
        expect(mockAnchor.click).toHaveBeenCalled();
      });
    });

    it('should handle errors gracefully', async () => {
      (ingestionService.getUploadedFiles as jest.Mock).mockRejectedValue(
        new Error('Network error')
      );

      render(<FileManager />);

      await waitFor(() => {
        expect(screen.getByText(/Network error/)).toBeInTheDocument();
      });
    });
  });

  describe('DocumentIngestion Component', () => {
    it('should handle successful ingestion with file metadata', async () => {
      const mockClassification = {
        fileName: 'test-document.pdf',
        documentType: {
          value: 'standards',
          label: 'NC Music Standards',
          description: 'Formal standards documents',
          icon: '📋',
        },
        confidence: 0.95,
        recommendedParser: 'pdf-parser',
      };

      (ingestionService.classifyDocument as jest.Mock).mockResolvedValue(mockClassification);
      (ingestionService.ingestDocument as jest.Mock).mockResolvedValue({
        success: true,
        results: { standards_count: 10 },
        file_metadata: mockFileMetadata,
      });

      const onIngestionComplete = jest.fn();
      render(<DocumentIngestion onIngestionComplete={onIngestionComplete} />);

      // Upload file
      const fileInput = screen.getByLabelText(/Select File/i);
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      
      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('Proceed with Ingestion')).toBeInTheDocument();
      });

      // Proceed with ingestion
      fireEvent.click(screen.getByText('Proceed with Ingestion'));

      await waitFor(() => {
        expect(screen.getByText('File Successfully Stored!')).toBeInTheDocument();
      });

      expect(onIngestionComplete).toHaveBeenCalledWith({
        success: true,
        results: { standards_count: 10 },
        file_metadata: mockFileMetadata,
      });
    });

    it('should handle duplicate file detection', async () => {
      const mockClassification = {
        fileName: 'test-document.pdf',
        documentType: {
          value: 'standards',
          label: 'NC Music Standards',
          description: 'Formal standards documents',
          icon: '📋',
        },
        confidence: 0.95,
        recommendedParser: 'pdf-parser',
      };

      (ingestionService.classifyDocument as jest.Mock).mockResolvedValue(mockClassification);
      (ingestionService.ingestDocument as jest.Mock).mockResolvedValue({
        success: true,
        duplicate: true,
        message: 'File already exists',
        existing_file: {
          id: 'existing-id',
          filename: 'test-document.pdf',
          upload_date: '2024-01-10T10:00:00Z',
          status: 'completed',
        },
      });

      render(<DocumentIngestion />);

      // Upload file
      const fileInput = screen.getByLabelText(/Select File/i);
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      
      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('Proceed with Ingestion')).toBeInTheDocument();
      });

      // Proceed with ingestion
      fireEvent.click(screen.getByText('Proceed with Ingestion'));

      await waitFor(() => {
        expect(screen.getByText('Duplicate File Detected')).toBeInTheDocument();
      });

      expect(screen.getByText('This file has already been uploaded and processed.')).toBeInTheDocument();
    });

    it('should validate file upload', async () => {
      render(<DocumentIngestion />);

      // Try to upload oversized file
      const fileInput = screen.getByLabelText(/Select File/i);
      const largeFile = new File(['x'.repeat(11 * 1024 * 1024)], 'large.pdf', { type: 'application/pdf' });
      
      fireEvent.change(fileInput, { target: { files: [largeFile] } });

      await waitFor(() => {
        expect(screen.getByText(/File size exceeds/)).toBeInTheDocument();
      });
    });
  });

  describe('Integration End-to-End', () => {
    it('should complete full file upload and management flow', async () => {
      // Mock all service calls
      (ingestionService.classifyDocument as jest.Mock).mockResolvedValue({
        fileName: 'test.pdf',
        documentType: {
          value: 'standards',
          label: 'NC Music Standards',
          description: 'Formal standards documents',
          icon: '📋',
        },
        confidence: 0.95,
        recommendedParser: 'pdf-parser',
      });

      (ingestionService.ingestDocument as jest.Mock).mockResolvedValue({
        success: true,
        results: { standards_count: 10 },
        file_metadata: mockFileMetadata,
      });

      (ingestionService.getUploadedFiles as jest.Mock).mockResolvedValue({
        success: true,
        files: [mockFileMetadata],
        pagination: { total: 1, count: 1, limit: 10, offset: 0 },
      });

      (ingestionService.getFileStatistics as jest.Mock).mockResolvedValue({
        success: true,
        database_stats: mockFileStats,
      });

      (ingestionService.downloadFile as jest.Mock).mockResolvedValue(new Blob(['test']));

      // Test ingestion
      const onIngestionComplete = jest.fn();
      const { unmount } = render(<DocumentIngestion onIngestionComplete={onIngestionComplete} />);

      const fileInput = screen.getByLabelText(/Select File/i);
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      
      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('Proceed with Ingestion')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Proceed with Ingestion'));

      await waitFor(() => {
        expect(onIngestionComplete).toHaveBeenCalled();
      });

      unmount();

      // Test file management
      render(<FileManager />);

      await waitFor(() => {
        expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
      });

      // Test download
      global.URL.createObjectURL = jest.fn(() => 'mock-url');
      global.URL.revokeObjectURL = jest.fn();
      const mockAnchor = { click: jest.fn() };
      jest.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any);
      jest.spyOn(document.body, 'appendChild').mockImplementation();
      jest.spyOn(document.body, 'removeChild').mockImplementation();

      fireEvent.click(screen.getByText('Download'));

      await waitFor(() => {
        expect(ingestionService.downloadFile).toHaveBeenCalled();
      });
    });
  });
});