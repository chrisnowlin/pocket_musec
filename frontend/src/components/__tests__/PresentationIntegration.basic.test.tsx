import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { PresentationCTA } from '../unified/PresentationCTA';
import { PresentationViewer } from '../unified/PresentationViewer';
import { PresentationStatus, SlideType } from '../../types/presentations';

describe('Presentation Integration Basic', () => {
  const mockOnGenerate = vi.fn();
  const mockOnView = vi.fn();
  const mockOnExport = vi.fn();
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render PresentationCTA component', () => {
    render(
      <PresentationCTA
        lessonId="test-lesson-1"
        onGenerate={mockOnGenerate}
      />
    );

    expect(screen.getByText('Generate Presentation')).toBeInTheDocument();
  });

  it('should render PresentationViewer component', () => {
    const mockPresentation = {
      id: 'test-presentation-1',
      lesson_id: 'test-lesson-1',
      title: 'Test Presentation',
      description: 'A test presentation',
      total_slides: 1,
      total_duration_minutes: 5,
      status: 'completed' as PresentationStatus,
      slides: [{
        id: 'slide-1',
        slide_number: 1,
        slide_type: 'title' as SlideType,
        title: 'Test Slide',
        content: 'Test content',
        teacher_script: 'Test script',
        duration_minutes: 5,
        materials_needed: [],
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }],
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
      is_stale: false,
    };

    render(
      <PresentationViewer
        presentation={mockPresentation}
        isOpen={true}
        onClose={mockOnClose}
        onExport={mockOnExport}
        isExporting={false}
      />
    );

    expect(screen.getByText('Test Presentation')).toBeInTheDocument();
    expect(screen.getByText('Test Slide')).toBeInTheDocument();
  });
});