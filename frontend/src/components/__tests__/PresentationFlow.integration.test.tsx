import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useState } from 'react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { usePresentations } from '../../hooks/usePresentations';
import { PresentationCTA } from '../unified/PresentationCTA';
import { PresentationViewer } from '../unified/PresentationViewer';
import type { 
  PresentationDocument, 
  PresentationSummary, 
  PresentationStatus,
  SlideType 
} from '../../types/presentations';

// Mock the API client using vi.hoisted to properly handle the mock
const { mockApiClient } = vi.hoisted(() => {
  const mockApiClient = {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  };
  return { mockApiClient };
});

vi.mock('../../lib/api', () => ({
  apiClient: mockApiClient,
}));

// Mock the usePresentations hook
const mockUsePresentations = {
  generatePresentation: vi.fn(),
  getPresentation: vi.fn(),
  exportPresentation: vi.fn(),
  downloadExport: vi.fn(),
  loadPresentations: vi.fn(),
  isGenerating: false,
  isExporting: false,
  error: null,
  clearError: vi.fn(),
};

vi.mock('../../hooks/usePresentations', () => ({
  usePresentations: () => mockUsePresentations,
}));

// Mock URL.createObjectURL and revokeObjectURL for download tests
global.URL.createObjectURL = vi.fn(() => 'mock-url');
global.URL.revokeObjectURL = vi.fn();

// Mock document.createElement for download
const mockAnchor = { click: vi.fn() };
const originalCreateElement = document.createElement.bind(document);
vi.spyOn(document, 'createElement').mockImplementation((tagName: string, options?: ElementCreationOptions) => {
  if (tagName.toLowerCase() === 'a') {
    return mockAnchor as any;
  }
  return originalCreateElement(tagName, options);
});
const originalAppendChild = document.body.appendChild.bind(document.body);
const originalRemoveChild = document.body.removeChild.bind(document.body);
vi.spyOn(document.body, 'appendChild').mockImplementation((node: Node) => {
  if (node === (mockAnchor as unknown as Node)) {
    return node;
  }
  return originalAppendChild(node);
});
vi.spyOn(document.body, 'removeChild').mockImplementation((node: Node) => {
  if (node === (mockAnchor as unknown as Node)) {
    return node;
  }
  return originalRemoveChild(node);
});

// Mock data
const mockPresentationSummary: PresentationSummary = {
  id: 'test-presentation-1',
  lesson_id: 'test-lesson-1',
  title: 'Test Presentation',
  status: 'completed' as PresentationStatus,
  total_slides: 3,
  total_duration_minutes: 15,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  is_stale: false,
};

const mockPresentationDocument: PresentationDocument = {
  id: 'test-presentation-1',
  lesson_id: 'test-lesson-1',
  title: 'Test Presentation',
  description: 'A test presentation for integration testing',
  total_slides: 3,
  total_duration_minutes: 15,
  status: 'completed' as PresentationStatus,
  slides: [
    {
      id: 'slide-1',
      slide_number: 1,
      slide_type: 'title' as SlideType,
      title: 'Introduction to Music',
      content: 'Welcome to our music lesson!\n\nToday we will learn about rhythm and melody.',
      teacher_script: 'Welcome students to the music class. Introduce yourself and the lesson objectives.',
      duration_minutes: 5,
      materials_needed: ['Whiteboard', 'Markers'],
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    },
    {
      id: 'slide-2',
      slide_number: 2,
      slide_type: 'content' as SlideType,
      title: 'Understanding Rhythm',
      content: 'Rhythm is the pattern of sounds in music.\n\nKey concepts:\n• Beat\n• Tempo\n• Time signature',
      teacher_script: 'Explain what rhythm means. Use examples of familiar songs to demonstrate beat patterns.',
      duration_minutes: 5,
      materials_needed: ['Drum', 'Metronome'],
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    },
    {
      id: 'slide-3',
      slide_number: 3,
      slide_type: 'activity' as SlideType,
      title: 'Clapping Exercise',
      content: 'Let\'s practice rhythm together!\n\n1. Follow the leader\n2. Clap the beat\n3. Create your own pattern',
      teacher_script: 'Guide students through the clapping exercise. Encourage participation and creativity.',
      duration_minutes: 5,
      materials_needed: [],
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    },
  ],
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  is_stale: false,
};

// Test component that uses the presentation hook
function PresentationFlowTest({ lessonId }: { lessonId: string }) {
  const {
    generatePresentation,
    getPresentation,
    exportPresentation,
    downloadExport,
    isGenerating,
    isExporting,
    error,
    clearError,
  } = usePresentations();

  const [presentation, setPresentation] = useState<PresentationDocument | null>(null);
  const [presentationStatus, setPresentationStatus] = useState<PresentationStatus>();
  const [presentationId, setPresentationId] = useState<string>();
  const [isViewerOpen, setIsViewerOpen] = useState(false);

  const handleGenerate = async () => {
    setPresentationStatus('generating');
    setPresentationId(undefined);
    const result = await generatePresentation(lessonId, {
      include_teacher_scripts: true,
      include_materials: true,
      slide_duration_minutes: 5,
    });
    if (result) {
      setPresentationStatus(result.status);
      setPresentationId(result.id);
    }
  };

  const handleView = async (id: string) => {
    const fullPresentation = await getPresentation(id);
    if (fullPresentation) {
      setPresentation(fullPresentation);
      setIsViewerOpen(true);
    }
  };

  const handleExport = async (format: 'json' | 'markdown') => {
    if (!presentation) return;
    
    const exportData = await exportPresentation(presentation.id, format);
    if (exportData) {
      await downloadExport(exportData.file_url, `presentation.${format}`);
    }
  };

  return (
    <div>
      <h1>Presentation Flow Test</h1>
      
      {error && (
        <div data-testid="error-message">
          {error}
          <button onClick={clearError}>Clear Error</button>
        </div>
      )}

      <PresentationCTA
        lessonId={lessonId}
        presentationStatus={presentationStatus}
        presentationId={presentationId}
        onGenerate={handleGenerate}
        onView={handleView}
        disabled={isGenerating}
      />

      {presentation && (
        <PresentationViewer
          presentation={presentation}
          isOpen={isViewerOpen}
          onClose={() => setIsViewerOpen(false)}
          onExport={handleExport}
          isExporting={isExporting}
        />
      )}
    </div>
  );
}

describe('Presentation Flow Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Reset mock implementations
    mockUsePresentations.generatePresentation.mockResolvedValue(mockPresentationSummary);
    mockUsePresentations.getPresentation.mockResolvedValue(mockPresentationDocument);
    mockUsePresentations.exportPresentation.mockResolvedValue({
      id: 'export-1',
      presentation_id: 'test-presentation-1',
      export_format: 'json',
      file_url: 'http://example.com/export.json',
      file_size_bytes: 1024,
      created_at: '2025-01-01T00:00:00Z',
      expires_at: '2025-01-02T00:00:00Z',
    });
    mockUsePresentations.downloadExport.mockImplementation(async () => {
      const anchor = document.createElement('a');
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      return undefined;
    });
    mockUsePresentations.clearError.mockImplementation(() => {});
    mockUsePresentations.isGenerating = false;
    mockUsePresentations.isExporting = false;
    mockUsePresentations.error = null;
  });

  describe('Complete Presentation Generation Flow', () => {
    it('should generate, view, and export a presentation successfully', async () => {
      // Mock hook responses
      mockUsePresentations.generatePresentation.mockResolvedValueOnce(mockPresentationSummary);
      mockUsePresentations.getPresentation.mockResolvedValueOnce(mockPresentationDocument);
      mockUsePresentations.exportPresentation.mockResolvedValueOnce({
        id: 'export-1',
        presentation_id: 'test-presentation-1',
        export_format: 'json',
        file_url: 'http://example.com/export.json',
        file_size_bytes: 1024,
        created_at: '2025-01-01T00:00:00Z',
        expires_at: '2025-01-02T00:00:00Z',
      });

      // Mock fetch for download
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        blob: vi.fn().mockResolvedValueOnce(new Blob(['{}'], { type: 'application/json' })),
      } as any);

      render(<PresentationFlowTest lessonId="test-lesson-1" />);

      // Initial state - should show generate button
      expect(screen.getByText('Generate Presentation')).toBeInTheDocument();
      expect(screen.queryByText('View Presentation')).not.toBeInTheDocument();

      // Generate presentation
      fireEvent.click(screen.getByText('Generate Presentation'));

      // Should show generating status
      await waitFor(() => {
        expect(screen.getByText('Generating...')).toBeInTheDocument();
      });

      // Should complete generation and show view button
      await waitFor(() => {
        expect(screen.getByText('View Presentation')).toBeInTheDocument();
      });

      // View presentation
      fireEvent.click(screen.getByText('View Presentation'));

      // Should open presentation viewer
      await waitFor(() => {
        expect(screen.getByText('Introduction to Music')).toBeInTheDocument();
        expect(screen.getByText('Slide 1 of 3')).toBeInTheDocument();
        expect(screen.getByText('Materials Needed:')).toBeInTheDocument();
        expect(screen.getByText('Whiteboard')).toBeInTheDocument();
        expect(screen.getByText('Teacher Script')).toBeInTheDocument();
      });

      // Navigate slides
      fireEvent.click(screen.getByText('Next'));
      expect(screen.getByText('Slide 2 of 3')).toBeInTheDocument();
      expect(screen.getByText('Understanding Rhythm')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Next'));
      expect(screen.getByText('Slide 3 of 3')).toBeInTheDocument();
      expect(screen.getByText('Clapping Exercise')).toBeInTheDocument();

      // Export presentation
      fireEvent.click(screen.getByText('Export JSON'));

      await waitFor(() => {
        expect(mockUsePresentations.exportPresentation).toHaveBeenCalledWith('test-presentation-1', 'json');
      });

      // Should trigger download
      await waitFor(() => {
        expect(mockAnchor.click).toHaveBeenCalled();
      });

      // Close viewer
      fireEvent.click(screen.getByText('Close'));
      expect(screen.queryByText('Introduction to Music')).not.toBeInTheDocument();
    });

    it('should handle generation failure gracefully', async () => {
      // Mock API failure
      mockApiClient.post.mockResolvedValueOnce({
        ok: false,
        message: 'Generation failed',
      });

      render(<PresentationFlowTest lessonId="test-lesson-1" />);

      fireEvent.click(screen.getByText('Generate Presentation'));

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument();
        expect(screen.getByText('Generation failed')).toBeInTheDocument();
      });

      // Should be able to clear error and try again
      fireEvent.click(screen.getByText('Clear Error'));
      expect(screen.queryByText('Generation failed')).not.toBeInTheDocument();
      expect(screen.getByText('Generate Presentation')).toBeInTheDocument();
    });

    it('should handle presentation loading failure', async () => {
      // Mock generation success
      mockApiClient.post.mockResolvedValueOnce({
        ok: true,
        data: mockPresentationSummary,
      });

      // Mock loading failure
      mockApiClient.get.mockResolvedValueOnce({
        ok: false,
        message: 'Failed to load presentation',
      });

      render(<PresentationFlowTest lessonId="test-lesson-1" />);

      // Generate presentation
      fireEvent.click(screen.getByText('Generate Presentation'));

      await waitFor(() => {
        expect(screen.getByText('View Presentation')).toBeInTheDocument();
      });

      // Try to view presentation
      fireEvent.click(screen.getByText('View Presentation'));

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument();
        expect(screen.getByText('Failed to load presentation')).toBeInTheDocument();
      });

      // Viewer should not open
      expect(screen.queryByText('Introduction to Music')).not.toBeInTheDocument();
    });
  });

  describe('Presentation Status Flow', () => {
    it('should handle different presentation statuses correctly', async () => {
      const pendingPresentation: PresentationSummary = {
        ...mockPresentationSummary,
        status: 'pending' as PresentationStatus,
      };

      const generatingPresentation: PresentationSummary = {
        ...mockPresentationSummary,
        status: 'generating' as PresentationStatus,
      };

      const failedPresentation: PresentationSummary = {
        ...mockPresentationSummary,
        status: 'failed' as PresentationStatus,
      };

      // Test pending status
      mockApiClient.post.mockResolvedValueOnce({
        ok: true,
        data: pendingPresentation,
      });

      render(<PresentationFlowTest lessonId="test-lesson-1" />);

      fireEvent.click(screen.getByText('Generate Presentation'));

      await waitFor(() => {
        expect(screen.getByText('Pending')).toBeInTheDocument();
        expect(screen.queryByText('View Presentation')).not.toBeInTheDocument();
      });

      // Test generating status
      mockApiClient.post.mockResolvedValueOnce({
        ok: true,
        data: generatingPresentation,
      });

      fireEvent.click(screen.getByText('Generate Presentation'));

      await waitFor(() => {
        expect(screen.getByText('Generating...')).toBeInTheDocument();
        expect(screen.queryByText('View Presentation')).not.toBeInTheDocument();
      });

      // Test failed status
      mockApiClient.post.mockResolvedValueOnce({
        ok: true,
        data: failedPresentation,
      });

      fireEvent.click(screen.getByText('Generate Presentation'));

      await waitFor(() => {
        expect(screen.getByText('Failed')).toBeInTheDocument();
        expect(screen.getByText('Regenerate')).toBeInTheDocument();
      });
    });
  });

  describe('Export Functionality', () => {
    it('should export to both JSON and Markdown formats', async () => {
      // Mock successful generation and loading
      mockApiClient.post.mockResolvedValueOnce({
        ok: true,
        data: mockPresentationSummary,
      });

      mockApiClient.get.mockResolvedValueOnce({
        ok: true,
        data: mockPresentationDocument,
      });

      // Mock export responses
      mockApiClient.post
        .mockResolvedValueOnce({
          ok: true,
          data: {
            id: 'export-1',
            presentation_id: 'test-presentation-1',
            export_format: 'json',
            file_url: 'http://example.com/export.json',
            file_size_bytes: 1024,
            created_at: '2025-01-01T00:00:00Z',
            expires_at: '2025-01-02T00:00:00Z',
          },
        })
        .mockResolvedValueOnce({
          ok: true,
          data: {
            id: 'export-2',
            presentation_id: 'test-presentation-1',
            export_format: 'markdown',
            file_url: 'http://example.com/export.md',
            file_size_bytes: 2048,
            created_at: '2025-01-01T00:00:00Z',
            expires_at: '2025-01-02T00:00:00Z',
          },
        });

      // Mock fetch for downloads
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          blob: vi.fn().mockResolvedValueOnce(new Blob(['{}'], { type: 'application/json' })),
        } as any)
        .mockResolvedValueOnce({
          ok: true,
          blob: vi.fn().mockResolvedValueOnce(new Blob(['# Markdown'], { type: 'text/markdown' })),
        } as any);

      render(<PresentationFlowTest lessonId="test-lesson-1" />);

      // Generate and view presentation
      fireEvent.click(screen.getByText('Generate Presentation'));
      await waitFor(() => {
        expect(screen.getByText('View Presentation')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('View Presentation'));
      await waitFor(() => {
        expect(screen.getByText('Introduction to Music')).toBeInTheDocument();
      });

      // Export JSON
      fireEvent.click(screen.getByText('Export JSON'));
      await waitFor(() => {
        expect(mockApiClient.post).toHaveBeenCalledWith('/presentations/test-presentation-1/export', {
          format: 'json',
        });
      });

      // Export Markdown
      fireEvent.click(screen.getByText('Export Markdown'));
      await waitFor(() => {
        expect(mockApiClient.post).toHaveBeenCalledWith('/presentations/test-presentation-1/export', {
          format: 'markdown',
        });
      });

      // Both downloads should be triggered
      expect(mockAnchor.click).toHaveBeenCalledTimes(2);
    });

    it('should handle export failure gracefully', async () => {
      // Mock successful generation and loading
      mockApiClient.post.mockResolvedValueOnce({
        ok: true,
        data: mockPresentationSummary,
      });

      mockApiClient.get.mockResolvedValueOnce({
        ok: true,
        data: mockPresentationDocument,
      });

      // Mock export failure
      mockApiClient.post.mockResolvedValueOnce({
        ok: false,
        message: 'Export failed',
      });

      render(<PresentationFlowTest lessonId="test-lesson-1" />);

      // Generate and view presentation
      fireEvent.click(screen.getByText('Generate Presentation'));
      await waitFor(() => {
        expect(screen.getByText('View Presentation')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('View Presentation'));
      await waitFor(() => {
        expect(screen.getByText('Introduction to Music')).toBeInTheDocument();
      });

      // Try to export
      fireEvent.click(screen.getByText('Export JSON'));

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument();
        expect(screen.getByText('Export failed')).toBeInTheDocument();
      });

      // Should not trigger download
      expect(mockAnchor.click).not.toHaveBeenCalled();
    });
  });

  describe('Component Integration', () => {
    it('should properly integrate all presentation components', async () => {
      // Mock successful API calls
      mockApiClient.post.mockResolvedValueOnce({
        ok: true,
        data: mockPresentationSummary,
      });

      mockApiClient.get.mockResolvedValueOnce({
        ok: true,
        data: mockPresentationDocument,
      });

      render(<PresentationFlowTest lessonId="test-lesson-1" />);

      // Test PresentationCTA component
      expect(screen.getByText('Generate Presentation')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Generate Presentation'));
      await waitFor(() => {
        expect(screen.getByText('View Presentation')).toBeInTheDocument();
      });

      // Test PresentationStatusIndicator integration
      expect(screen.getByText('Completed')).toBeInTheDocument();

      // Test PresentationViewer integration
      fireEvent.click(screen.getByText('View Presentation'));
      await waitFor(() => {
        expect(screen.getByText('Introduction to Music')).toBeInTheDocument();
      });

      // Test all viewer components work together
      expect(screen.getByText('Slide 1 of 3')).toBeInTheDocument();
      expect(screen.getByText('📋 title')).toBeInTheDocument();
      expect(screen.getByText('5 min')).toBeInTheDocument();
      expect(screen.getByText('Materials Needed:')).toBeInTheDocument();
      expect(screen.getByText('Teacher Script')).toBeInTheDocument();
      expect(screen.getByText('Export JSON')).toBeInTheDocument();
      expect(screen.getByText('Export Markdown')).toBeInTheDocument();

      // Test navigation
      fireEvent.click(screen.getByText('Next'));
      expect(screen.getByText('📝 content')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Previous'));
      expect(screen.getByText('📋 title')).toBeInTheDocument();

      // Test teacher script toggle
      fireEvent.click(screen.getByText('Hide'));
      expect(screen.queryByText('Welcome students to the music class.')).not.toBeInTheDocument();

      fireEvent.click(screen.getByText('Show'));
      expect(screen.getByText('Welcome students to the music class. Introduce yourself and the lesson objectives.')).toBeInTheDocument();
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle network errors gracefully', async () => {
      // Mock network error
      mockApiClient.post.mockRejectedValueOnce(new Error('Network error'));

      render(<PresentationFlowTest lessonId="test-lesson-1" />);

      fireEvent.click(screen.getByText('Generate Presentation'));

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument();
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });

    it('should handle empty presentation gracefully', async () => {
      const emptyPresentation: PresentationDocument = {
        ...mockPresentationDocument,
        slides: [],
        total_slides: 0,
      };

      mockApiClient.post.mockResolvedValueOnce({
        ok: true,
        data: mockPresentationSummary,
      });

      mockApiClient.get.mockResolvedValueOnce({
        ok: true,
        data: emptyPresentation,
      });

      render(<PresentationFlowTest lessonId="test-lesson-1" />);

      fireEvent.click(screen.getByText('Generate Presentation'));
      await waitFor(() => {
        expect(screen.getByText('View Presentation')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('View Presentation'));
      await waitFor(() => {
        expect(screen.getByText('Test Presentation')).toBeInTheDocument();
        expect(screen.queryByText('Slide 1 of 0')).not.toBeInTheDocument();
      });
    });
  });
});
