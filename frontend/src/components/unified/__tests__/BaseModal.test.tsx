import { render, screen, fireEvent } from '@testing-library/react'
import BaseModal from '../BaseModal'

describe('BaseModal', () => {
  it('does not render when isOpen is false', () => {
    const { container } = render(
      <BaseModal isOpen={false} onClose={() => {}}>
        <div>Content</div>
      </BaseModal>
    )

    expect(container.firstChild).toBeNull()
  })

  it('renders children when open', () => {
    render(
      <BaseModal isOpen onClose={() => {}}>
        <div>Modal Content</div>
      </BaseModal>
    )

    expect(screen.getByText('Modal Content')).toBeInTheDocument()
  })

  it('calls onClose when clicking overlay background', () => {
    const onClose = vi.fn()

    render(
      <BaseModal isOpen onClose={onClose}>
        <div>Inside</div>
      </BaseModal>
    )

    const overlay = screen.getByRole('dialog')
    fireEvent.click(overlay)

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('does not call onClose when clicking inside content', () => {
    const onClose = vi.fn()

    render(
      <BaseModal isOpen onClose={onClose}>
        <button>Click me</button>
      </BaseModal>
    )

    const button = screen.getByText('Click me')
    fireEvent.click(button)

    expect(onClose).not.toHaveBeenCalled()
  })

  it('applies size classes correctly', () => {
    const { rerender } = render(
      <BaseModal isOpen size="sm" onClose={() => {}}>
        <div>Small</div>
      </BaseModal>
    )

    expect(screen.getByText('Small').parentElement).toHaveClass('max-w-md')

    rerender(
      <BaseModal isOpen size="lg" onClose={() => {}}>
        <div>Large</div>
      </BaseModal>
    )

    expect(screen.getByText('Large').parentElement).toHaveClass('max-w-3xl')
  })
})

