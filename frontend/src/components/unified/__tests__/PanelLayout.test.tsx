import { describe, expect, it } from 'vitest';
import { render } from '@testing-library/react';
import PanelLayout from '../PanelLayout';

describe('PanelLayout', () => {
  it('renders children with workspace-card class', () => {
    const { container } = render(
      <PanelLayout>
        <div>Test content</div>
      </PanelLayout>,
    );

    const panelDiv = container.firstElementChild as HTMLElement;
    expect(panelDiv).toHaveClass('workspace-card');
    expect(panelDiv.textContent).toBe('Test content');
  });

  it('applies additional className', () => {
    const { container } = render(
      <PanelLayout className="p-6 mb-6">
        <div>Test content</div>
      </PanelLayout>,
    );

    const panelDiv = container.firstElementChild as HTMLElement;
    expect(panelDiv).toHaveClass('workspace-card', 'p-6', 'mb-6');
  });
});

