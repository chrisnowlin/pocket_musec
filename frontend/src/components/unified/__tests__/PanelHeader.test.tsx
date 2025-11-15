import { describe, expect, it } from 'vitest';
import { render } from '@testing-library/react';
import PanelHeader from '../PanelHeader';

describe('PanelHeader', () => {
  it('renders title', () => {
    const { getByText } = render(<PanelHeader title="Test Title" />);
    expect(getByText('Test Title')).toHaveClass('text-2xl', 'font-bold', 'text-ink-800');
  });

  it('renders subtitle when provided', () => {
    const { getByText } = render(
      <PanelHeader title="Test Title" subtitle="Test Subtitle" />,
    );
    expect(getByText('Test Subtitle')).toHaveClass('text-ink-600', 'mt-2');
  });

  it('does not render subtitle when not provided', () => {
    const { queryByText } = render(<PanelHeader title="Test Title" />);
    expect(queryByText('Test Subtitle')).not.toBeInTheDocument();
  });

  it('renders children when provided', () => {
    const { getByText } = render(
      <PanelHeader title="Test Title">
        <div>Child content</div>
      </PanelHeader>,
    );
    expect(getByText('Child content')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <PanelHeader title="Test Title" className="mb-6" />,
    );
    const headerDiv = container.firstElementChild as HTMLElement;
    expect(headerDiv).toHaveClass('mb-6');
  });
});

