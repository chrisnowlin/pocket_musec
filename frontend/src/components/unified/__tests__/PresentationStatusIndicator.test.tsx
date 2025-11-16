import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { PresentationStatusIndicator } from '../PresentationStatusIndicator';
import { PresentationStatus } from '../../../types/presentations';

describe('PresentationStatusIndicator', () => {
  it('renders pending status correctly', () => {
    render(<PresentationStatusIndicator status={PresentationStatus.PENDING} />);
    
    const indicator = screen.getByText('Pending');
    expect(indicator).toBeInTheDocument();
    expect(screen.getByText('⏳')).toBeInTheDocument();
    expect(indicator.closest('div')).toHaveClass('bg-gray-100 text-gray-800 border-gray-200');
  });

  it('renders generating status correctly', () => {
    render(<PresentationStatusIndicator status={PresentationStatus.GENERATING} />);
    
    const indicator = screen.getByText('Generating...');
    expect(indicator).toBeInTheDocument();
    expect(screen.getByText('🔄')).toBeInTheDocument();
    expect(indicator.closest('div')).toHaveClass('bg-blue-100 text-blue-800 border-blue-200');
  });

  it('renders completed status correctly', () => {
    render(<PresentationStatusIndicator status={PresentationStatus.COMPLETED} />);
    
    const indicator = screen.getByText('Completed');
    expect(indicator).toBeInTheDocument();
    expect(screen.getByText('✅')).toBeInTheDocument();
    expect(indicator.closest('div')).toHaveClass('bg-green-100 text-green-800 border-green-200');
  });

  it('renders failed status correctly', () => {
    render(<PresentationStatusIndicator status={PresentationStatus.FAILED} />);
    
    const indicator = screen.getByText('Failed');
    expect(indicator).toBeInTheDocument();
    expect(screen.getByText('❌')).toBeInTheDocument();
    expect(indicator.closest('div')).toHaveClass('bg-red-100 text-red-800 border-red-200');
  });

  it('applies custom className', () => {
    render(
      <PresentationStatusIndicator 
        status={PresentationStatus.COMPLETED} 
        className="custom-class" 
      />
    );
    
    const indicator = screen.getByText('Completed').closest('div');
    expect(indicator).toHaveClass('custom-class');
  });

  it('has correct structure and styling', () => {
    render(<PresentationStatusIndicator status={PresentationStatus.PENDING} />);
    
    const container = screen.getByText('Pending').closest('div');
    expect(container).toHaveClass(
      'inline-flex',
      'items-center',
      'gap-1',
      'px-2',
      'py-1',
      'rounded-full',
      'text-xs',
      'font-medium',
      'border'
    );
  });

  it('handles unknown status gracefully', () => {
    render(<PresentationStatusIndicator status={'unknown' as PresentationStatus} />);
    
    const indicator = screen.getByText('Unknown');
    expect(indicator).toBeInTheDocument();
    expect(screen.getByText('❓')).toBeInTheDocument();
    expect(indicator.closest('div')).toHaveClass('bg-gray-100 text-gray-800 border-gray-200');
  });

  it('icon has correct animation for generating status', () => {
    render(<PresentationStatusIndicator status={PresentationStatus.GENERATING} />);
    
    const icon = screen.getByText('🔄');
    expect(icon).toHaveStyle('animation-duration: 2s');
  });

  it('icon has no animation for non-generating status', () => {
    render(<PresentationStatusIndicator status={PresentationStatus.COMPLETED} />);
    
    const icon = screen.getByText('✅');
    expect(icon).toHaveStyle('animation-duration: 0s');
  });
});