import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { PresentationCTA } from '../PresentationCTA';
import { PresentationStatus } from '../../../types/presentations';

describe('PresentationCTA', () => {
  const mockOnGenerate = vi.fn();
  const mockOnView = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows generate button when no presentation exists', () => {
    render(
      <PresentationCTA
        lessonId="test-lesson-1"
        onGenerate={mockOnGenerate}
      />
    );

    const generateButton = screen.getByRole('button', { name: 'Generate Presentation' });
    expect(generateButton).toBeInTheDocument();
    expect(generateButton).toHaveClass('bg-green-600');
  });

  it('shows status indicator and view button when presentation is completed', () => {
    render(
      <PresentationCTA
        lessonId="test-lesson-1"
        presentationStatus={PresentationStatus.COMPLETED}
        presentationId="test-presentation-1"
        onView={mockOnView}
      />
    );

    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'View Presentation' })).toBeInTheDocument();
  });

  it('shows generating status when presentation is generating', () => {
    render(
      <PresentationCTA
        lessonId="test-lesson-1"
        presentationStatus={PresentationStatus.GENERATING}
      />
    );

    expect(screen.getByText('Generating...')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'View Presentation' })).not.toBeInTheDocument();
  });

  it('calls onGenerate when generate button is clicked', () => {
    render(
      <PresentationCTA
        lessonId="test-lesson-1"
        onGenerate={mockOnGenerate}
      />
    );

    const generateButton = screen.getByRole('button', { name: 'Generate Presentation' });
    fireEvent.click(generateButton);
    expect(mockOnGenerate).toHaveBeenCalledTimes(1);
  });

  it('calls onView when view button is clicked', () => {
    render(
      <PresentationCTA
        lessonId="test-lesson-1"
        presentationStatus={PresentationStatus.COMPLETED}
        presentationId="test-presentation-1"
        onView={mockOnView}
      />
    );

    const viewButton = screen.getByRole('button', { name: 'View Presentation' });
    fireEvent.click(viewButton);
    expect(mockOnView).toHaveBeenCalledWith('test-presentation-1');
  });

  it('shows regenerate button when presentation is completed and onGenerate is provided', () => {
    render(
      <PresentationCTA
        lessonId="test-lesson-1"
        presentationStatus={PresentationStatus.COMPLETED}
        presentationId="test-presentation-1"
        onGenerate={mockOnGenerate}
        onView={mockOnView}
      />
    );

    expect(screen.getByRole('button', { name: 'Regenerate' })).toBeInTheDocument();
  });

  it('disables buttons when disabled prop is true', () => {
    render(
      <PresentationCTA
        lessonId="test-lesson-1"
        onGenerate={mockOnGenerate}
        disabled={true}
      />
    );

    const generateButton = screen.getByRole('button', { name: 'Generate Presentation' });
    expect(generateButton).toBeDisabled();
    expect(generateButton).toHaveClass('disabled:bg-green-300');
  });
});