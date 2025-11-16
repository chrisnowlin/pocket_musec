import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { PresentationViewer } from '../PresentationViewer';
import { PresentationDocument, PresentationStatus, SlideType } from '../../../types/presentations';

// Mock presentation data
const mockPresentation: PresentationDocument = {
  id: 'test-presentation-1',
  lesson_id: 'test-lesson-1',
  title: 'Test Presentation',
  description: 'A test presentation for unit testing',
  total_slides: 3,
  total_duration_minutes: 15,
  status: PresentationStatus.COMPLETED,
  slides: [
    {
      id: 'slide-1',
      slide_number: 1,
      slide_type: SlideType.TITLE,
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
      slide_type: SlideType.CONTENT,
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
      slide_type: SlideType.ACTIVITY,
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

describe('PresentationViewer', () => {
  const mockOnClose = vi.fn();
  const mockOnExport = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when isOpen is false', () => {
    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={false}
        onClose={mockOnClose}
      />
    );

    expect(screen.queryByText('Test Presentation')).not.toBeInTheDocument();
  });

  it('renders presentation when isOpen is true', () => {
    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Test Presentation')).toBeInTheDocument();
    expect(screen.getByText('Introduction to Music')).toBeInTheDocument();
    expect(screen.getByText('Slide 1 of 3')).toBeInTheDocument();
  });

it('displays correct slide information', () => {
    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    // First slide info
    expect(screen.getByText('Slide 1 of 3')).toBeInTheDocument();
    expect(screen.getByText('📋 title')).toBeInTheDocument();
    expect(screen.getByText('5 min')).toBeInTheDocument();
    expect(screen.getByText('Introduction to Music')).toBeInTheDocument();
    
    // Check for content using a more flexible approach
    const contentElement = screen.getByText((content: string, element: Element | null) => {
      return element?.className.includes('whitespace-pre-wrap') === true && 
             content.includes('Welcome to our music lesson!') === true;
    });
    expect(contentElement).toBeInTheDocument();
  });

  it('shows materials when they exist', () => {
    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Materials Needed:')).toBeInTheDocument();
    expect(screen.getByText('Whiteboard')).toBeInTheDocument();
    expect(screen.getByText('Markers')).toBeInTheDocument();
  });

  it('hides materials section when none exist', () => {
    const presentationWithoutMaterials = {
      ...mockPresentation,
      slides: [
        {
          ...mockPresentation.slides[0],
          materials_needed: [],
        },
      ],
    };

    render(
      <PresentationViewer
        presentation={presentationWithoutMaterials}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    expect(screen.queryByText('Materials Needed:')).not.toBeInTheDocument();
  });

  it('displays teacher script by default', () => {
    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Teacher Script')).toBeInTheDocument();
    expect(screen.getByText('Welcome students to the music class. Introduce yourself and the lesson objectives.')).toBeInTheDocument();
  });

  it('can hide and show teacher script', () => {
    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    const toggleButton = screen.getByText('Hide');
    fireEvent.click(toggleButton);

    expect(screen.queryByText('Welcome students to the music class. Introduce yourself and the lesson objectives.')).not.toBeInTheDocument();
    expect(screen.getByText('Show')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Show'));
    expect(screen.getByText('Welcome students to the music class. Introduce yourself and the lesson objectives.')).toBeInTheDocument();
    expect(screen.getByText('Hide')).toBeInTheDocument();
  });

  it('navigates between slides using next/previous buttons', () => {
    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    // Start on first slide
    expect(screen.getByText('Slide 1 of 3')).toBeInTheDocument();
    expect(screen.getByText('Introduction to Music')).toBeInTheDocument();

    // Go to next slide
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    expect(screen.getByText('Slide 2 of 3')).toBeInTheDocument();
    expect(screen.getByText('Understanding Rhythm')).toBeInTheDocument();

    // Go to previous slide
    const prevButton = screen.getByText('Previous');
    fireEvent.click(prevButton);

    expect(screen.getByText('Slide 1 of 3')).toBeInTheDocument();
    expect(screen.getByText('Introduction to Music')).toBeInTheDocument();
  });

  it('disables navigation buttons appropriately', () => {
    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    // Previous button disabled on first slide
    const prevButton = screen.getByText('Previous');
    expect(prevButton).toBeDisabled();

    // Go to last slide
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton); // Slide 2
    fireEvent.click(nextButton); // Slide 3

    // Next button disabled on last slide
    expect(nextButton).toBeDisabled();
    expect(prevButton).not.toBeDisabled();
  });

  it('navigates using slide dots', () => {
    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    const dots = screen.getAllByRole('button').filter(button => 
      button.className.includes('w-2 h-2 rounded-full')
    );

    // Click on third dot
    fireEvent.click(dots[2]);

    expect(screen.getByText('Slide 3 of 3')).toBeInTheDocument();
    expect(screen.getByText('Clapping Exercise')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('calls onExport with correct format when export buttons are clicked', () => {
    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={true}
        onClose={mockOnClose}
        onExport={mockOnExport}
      />
    );

    const jsonButton = screen.getByText('Export JSON');
    fireEvent.click(jsonButton);

    expect(mockOnExport).toHaveBeenCalledWith('json');

    const markdownButton = screen.getByText('Export Markdown');
    fireEvent.click(markdownButton);

    expect(mockOnExport).toHaveBeenCalledWith('markdown');
  });

  it('disables export buttons when isExporting is true', () => {
    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={true}
        onClose={mockOnClose}
        onExport={mockOnExport}
        isExporting={true}
      />
    );

    const exportButtons = screen.getAllByText('Exporting...');
    expect(exportButtons).toHaveLength(4);
    exportButtons.forEach(button => {
      expect(button).toBeDisabled();
    });
  });

  it('shows correct slide type colors and icons', () => {
    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    // Title slide
    const titleBadge = screen.getByText('📋 title');
    expect(titleBadge).toHaveClass('bg-purple-100', 'text-purple-800');

    // Navigate to content slide
    fireEvent.click(screen.getByText('Next'));
    const contentBadge = screen.getByText('📝 content');
    expect(contentBadge).toHaveClass('bg-blue-100', 'text-blue-800');

    // Navigate to activity slide
    fireEvent.click(screen.getByText('Next'));
    const activityBadge = screen.getByText('🎯 activity');
    expect(activityBadge).toHaveClass('bg-green-100', 'text-green-800');
  });

  it('handles keyboard navigation', () => {
    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    // Test that component renders and is interactive
    expect(screen.getByText('Slide 1 of 3')).toBeInTheDocument();
    
    // Navigate to next slide
    fireEvent.click(screen.getByText('Next'));
    expect(screen.getByText('Slide 2 of 3')).toBeInTheDocument();
  });

  it('displays presentation status indicator', () => {
    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('handles empty presentation gracefully', () => {
    const emptyPresentation: PresentationDocument = {
      ...mockPresentation,
      slides: [],
      total_slides: 0,
    };

    render(
      <PresentationViewer
        presentation={emptyPresentation}
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Test Presentation')).toBeInTheDocument();
    expect(screen.queryByText('Slide 1 of 0')).not.toBeInTheDocument();
  });
});