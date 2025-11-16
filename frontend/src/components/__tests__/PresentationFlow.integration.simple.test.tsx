import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, describe, it, expect } from 'vitest';
import { PresentationCTA } from '../unified/PresentationCTA';

// Simple test to verify DOM setup
describe('Presentation Flow Simple Integration', () => {
  it('should render basic component', () => {
    const mockOnGenerate = vi.fn();
    
    render(
      <PresentationCTA
        lessonId="test-lesson-1"
        onGenerate={mockOnGenerate}
      />
    );

    expect(screen.getByText('Generate Presentation')).toBeInTheDocument();
  });
});