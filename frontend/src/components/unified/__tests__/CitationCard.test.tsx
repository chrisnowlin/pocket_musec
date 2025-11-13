import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { CitationCard } from '../CitationCard';
import { FileStorageService } from '../../services/fileStorageService';
import { Citation, FileCitation } from '../../types/fileStorage';

// Mock the file storage service
jest.mock('../../services/fileStorageService');

const mockFileStorageService = FileStorageService as jest.Mocked<typeof FileStorageService>;

// Mock citation with file information
const mockCitation: Citation = {
  id: 'test-citation-1',
  source_document: 'Test Document',
  page_number: 1,
  text: 'This is a test citation with file information',
  file_id: 'test-file-1',
  snippet_start: 0,
  snippet_end: 50,
  content_preview: 'This is a test citation...',
  relevance_score: 0.95,
  metadata: {
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
};

// Mock file citation
const mockFileCitation: FileCitation = {
  citation: mockCitation,
  file: {
    id: 'test-file-1',
    filename: 'test-document.pdf',
    original_filename: 'Test Document.pdf',
    file_path: '/test/path/test-document.pdf',
    file_type: 'pdf',
    file_size: 1024000,
    upload_date: '2024-01-01T00:00:00Z',
    processing_status: 'completed',
    metadata: {
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    }
  },
  isAvailable: true
};

// Mock legacy citation (string only)
const mockLegacyCitation = 'Test Document - Page 1';

describe('CitationCard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock downloadFile method
    mockFileStorageService.downloadFile.mockResolvedValue(undefined);
    
    // Mock file URL generation
    URL.createObjectURL = jest.fn(() => 'blob:mock-url');
    URL.revokeObjectURL = jest.fn();
  });

  it('renders enhanced citation with file information', () => {
    render(
      <CitationCard
        citation={mockLegacyCitation}
        enhancedCitation={mockFileCitation}
        isExpanded={false}
        onToggle={() => {}}
        onViewInContext={() => {}}
      />
    );

    // Check basic citation info
    expect(screen.getByText('Test Document')).toBeInTheDocument();
    expect(screen.getByText('Page 1')).toBeInTheDocument();
    
    // Check file information
    expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
    expect(screen.getByText('PDF')).toBeInTheDocument();
    expect(screen.getByText('1.0 MB')).toBeInTheDocument();
  });

  it('shows download button and triggers download', async () => {
    const onDownload = jest.fn();
    
    render(
      <CitationCard
        citation={mockLegacyCitation}
        enhancedCitation={mockFileCitation}
        isExpanded={false}
        onToggle={() => {}}
        onViewInContext={() => {}}
        onDownload={onDownload}
      />
    );

    const downloadButton = screen.getByLabelText('Download source document');
    expect(downloadButton).toBeInTheDocument();

    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(mockFileStorageService.downloadFile).toHaveBeenCalledWith('test-file-1');
      expect(onDownload).toHaveBeenCalledWith(mockFileCitation);
    });
  });

  it('shows unavailable state for missing files', () => {
    const unavailableCitation: FileCitation = {
      ...mockFileCitation,
      isAvailable: false,
      file: undefined
    };

    render(
      <CitationCard
        citation={mockLegacyCitation}
        enhancedCitation={unavailableCitation}
        isExpanded={false}
        onToggle={() => {}}
        onViewInContext={() => {}}
      />
    );

    expect(screen.getByText('Source document unavailable')).toBeInTheDocument();
    expect(screen.getByText(/File may have been deleted/)).toBeInTheDocument();
  });

  it('expands to show full details when clicked', () => {
    const onToggle = jest.fn();
    
    render(
      <CitationCard
        citation={mockLegacyCitation}
        enhancedCitation={mockFileCitation}
        isExpanded={false}
        onToggle={onToggle}
        onViewInContext={() => {}}
      />
    );

    const expandButton = screen.getByLabelText('Expand citation details');
    fireEvent.click(expandButton);

    expect(onToggle).toHaveBeenCalledWith(mockLegacyCitation);
  });

  it('shows full text when expanded', () => {
    render(
      <CitationCard
        citation={mockLegacyCitation}
        enhancedCitation={mockFileCitation}
        isExpanded={true}
        onToggle={() => {}}
        onViewInContext={() => {}}
      />
    );

    expect(screen.getByText('This is a test citation with file information')).toBeInTheDocument();
  });

  it('displays file icon based on file type', () => {
    render(
      <CitationCard
        citation={mockLegacyCitation}
        enhancedCitation={mockFileCitation}
        isExpanded={false}
        onToggle={() => {}}
        onViewInContext={() => {}}
      />
    );

    // Check for PDF icon
    expect(screen.getByTestId('file-icon')).toBeInTheDocument();
  });

  it('handles download errors gracefully', async () => {
    const onDownloadError = jest.fn();
    
    mockFileStorageService.downloadFile.mockRejectedValue(new Error('Download failed'));

    render(
      <CitationCard
        citation={mockLegacyCitation}
        enhancedCitation={mockFileCitation}
        isExpanded={false}
        onToggle={() => {}}
        onViewInContext={() => {}}
        onDownloadError={onDownloadError}
      />
    );

    const downloadButton = screen.getByLabelText('Download source document');
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(onDownloadError).toHaveBeenCalled();
    });
  });

  it('formats file size correctly', () => {
    const smallFileCitation: FileCitation = {
      ...mockFileCitation,
      file: {
        ...mockFileCitation.file!,
        file_size: 1024 // 1 KB
      }
    };

    render(
      <CitationCard
        citation={mockLegacyCitation}
        enhancedCitation={smallFileCitation}
        isExpanded={false}
        onToggle={() => {}}
        onViewInContext={() => {}}
      />
    );

    expect(screen.getByText('1.0 KB')).toBeInTheDocument();
  });

  it('displays view in context button when lesson ID is provided', () => {
    render(
      <CitationCard
        citation={mockLegacyCitation}
        enhancedCitation={mockFileCitation}
        isExpanded={false}
        lessonId="test-lesson-1"
        onToggle={() => {}}
        onViewInContext={() => {}}
      />
    );

    expect(screen.getByLabelText('View citation in lesson context')).toBeInTheDocument();
  });
});