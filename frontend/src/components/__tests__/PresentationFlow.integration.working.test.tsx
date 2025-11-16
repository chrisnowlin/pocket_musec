import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useState } from 'react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { PresentationCTA } from '../unified/PresentationCTA';
import { PresentationViewer } from '../unified/PresentationViewer';
import type { 
  PresentationDocument, 
  PresentationSummary, 
  PresentationStatus,
  SlideType 
} from '../../types/presentations';

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
  ],
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  is_stale: false,
};

// Test component with simplified state management
function PresentationFlowTest({ lessonId }: { lessonId: string }) {
  const [presentation, setPresentation] = useState<PresentationDocument | null>(null);
  const [presentationStatus, setPresentationStatus] = useState<PresentationStatus>();
  const [presentationId, setPresentationId] = useState<string>();
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    
    // Simulate generation delay
    await new Promise(resolve => setTimeout(resolve, 100));
    
    setPresentationStatus(mockPresentationSummary.status);
    setPresentationId(mockPresentationSummary.id);
    setIsGenerating(false);
  };

  const handleView = async (id: string) => {
    // Simulate loading delay
    await new Promise(resolve => setTimeout(resolve, 50));
    
    setPresentation(mockPresentationDocument);
    setIsViewerOpen(true);
  };

  const handleExport = async (format: 'json' | 'markdown') => {
    if (!presentation) return;
    
    setIsExporting(true);
    setError(null);
    
    // Simulate export delay
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Simulate download
    const blob = new Blob(['{}'], { type: format === 'json' ? 'application/json' : 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `presentation.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    setIsExporting(false);
  };

  const clearError = () => setError(null);

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
  });

  it('should render PresentationCTA with different states', () => {
    const mockOnGenerate = vi.fn();
    const mockOnView = vi.fn();

    // Test initial state
    render(
      <PresentationCTA
        lessonId="test-lesson-1"
        onGenerate={mockOnGenerate}
        onView={mockOnView}
      />
    );
    expect(screen.getByText('Generate Presentation')).toBeInTheDocument();

    // Test completed state
    render(
      <PresentationCTA
        lessonId="test-lesson-1"
        presentationStatus={'completed' as PresentationStatus}
        presentationId="test-presentation-1"
        onGenerate={mockOnGenerate}
        onView={mockOnView}
      />
    );
    expect(screen.getByText('View Presentation')).toBeInTheDocument();
  });

  it('should render PresentationViewer with presentation data', () => {
    const mockOnExport = vi.fn();
    const mockOnClose = vi.fn();

    render(
      <PresentationViewer
        presentation={mockPresentationDocument}
        isOpen={true}
        onClose={mockOnClose}
        onExport={mockOnExport}
        isExporting={false}
      />
    );

    expect(screen.getByText('Test Presentation')).toBeInTheDocument();
    expect(screen.getByText('Introduction to Music')).toBeInTheDocument();
    expect(screen.getByText('Slide 1 of 2')).toBeInTheDocument();
    expect(screen.getByText('Materials Needed:')).toBeInTheDocument();
    expect(screen.getByText('Whiteboard')).toBeInTheDocument();
    expect(screen.getByText('Teacher Script')).toBeInTheDocument();
  });

  it('should handle slide navigation in PresentationViewer', () => {
    const mockOnExport = vi.fn();
    const mockOnClose = vi.fn();

    render(
      <PresentationViewer
        presentation={mockPresentationDocument}
        isOpen={true}
        onClose={mockOnClose}
        onExport={mockOnExport}
        isExporting={false}
      />
    );

    // Test initial slide
    expect(screen.getByText('Slide 1 of 2')).toBeInTheDocument();
    expect(screen.getByText('Introduction to Music')).toBeInTheDocument();

    // Navigate to next slide
    fireEvent.click(screen.getByText('Next'));
    expect(screen.getByText('Slide 2 of 2')).toBeInTheDocument();
    expect(screen.getByText('Understanding Rhythm')).toBeInTheDocument();

    // Navigate back to previous slide
    fireEvent.click(screen.getByText('Previous'));
    expect(screen.getByText('Slide 1 of 2')).toBeInTheDocument();
    expect(screen.getByText('Introduction to Music')).toBeInTheDocument();
  });

  it('should handle teacher script toggle', () => {
    const mockOnExport = vi.fn();
    const mockOnClose = vi.fn();

    render(
      <PresentationViewer
        presentation={mockPresentationDocument}
        isOpen={true}
        onClose={mockOnClose}
        onExport={mockOnExport}
        isExporting={false}
      />
    );

    // Script should be visible initially
    expect(screen.getByText('Welcome students to the music class. Introduce yourself and the lesson objectives.')).toBeInTheDocument();

    // Hide script
    fireEvent.click(screen.getByText('Hide'));
    expect(screen.queryByText('Welcome students to the music class.')).not.toBeInTheDocument();

    // Show script again
    fireEvent.click(screen.getByText('Show'));
    expect(screen.getByText('Welcome students to the music class. Introduce yourself and the lesson objectives.')).toBeInTheDocument();
  });
});
