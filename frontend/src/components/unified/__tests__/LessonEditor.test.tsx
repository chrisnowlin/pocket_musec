import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LessonEditor from '../LessonEditor'

// Mock the lessonEditorStorage
vi.mock('../../utils/lessonEditorStorage', () => ({
  lessonEditorStorage: {
    saveContent: vi.fn(),
    loadContent: vi.fn(),
  },
}))

// Mock the useAutoSave hook
vi.mock('../../hooks/useAutoSave', () => ({
  useAutoSave: vi.fn(() => ({
    triggerSave: vi.fn(),
    saveImmediately: vi.fn(),
  })),
}))

// Mock the MarkdownRenderer
vi.mock('../../components/MarkdownRenderer', () => ({
  default: ({ content, className }: { content: string; className?: string }) => (
    <div className={className} data-testid="markdown-renderer">
      {content}
    </div>
  ),
}))

describe('LessonEditor', () => {
  const mockOnSave = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders editor with initial content', () => {
    render(
      <LessonEditor
        content="Initial content"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    )

    expect(screen.getByDisplayValue('Initial content')).toBeInTheDocument()
    expect(screen.getByText('Lesson Editor')).toBeInTheDocument()
  })

  it('switches between edit, split, and preview modes', async () => {
    const user = userEvent.setup()
    render(
      <LessonEditor
        content="Test content"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    )

    // Initially in edit mode - Edit button should be active
    expect(screen.getByDisplayValue('Test content')).toBeInTheDocument()
    expect(screen.getByText('Edit')).toHaveClass('bg-white text-ink-800 shadow-sm')

    // Switch to split mode
    await user.click(screen.getByText('Split'))
    expect(screen.getByDisplayValue('Test content')).toBeInTheDocument()
    expect(screen.getByText('Split')).toHaveClass('bg-white text-ink-800 shadow-sm')

    // Switch to preview mode
    await user.click(screen.getByText('Preview'))
    expect(screen.getByText('Preview')).toHaveClass('bg-white text-ink-800 shadow-sm')

    // Switch back to edit mode
    await user.click(screen.getByText('Edit'))
    expect(screen.getByDisplayValue('Test content')).toBeInTheDocument()
    expect(screen.getByText('Edit')).toHaveClass('bg-white text-ink-800 shadow-sm')
  })

  it('displays word and character count', () => {
    render(
      <LessonEditor
        content="Hello world test"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    )

    expect(screen.getByText('3 words • 16 chars')).toBeInTheDocument()
  })

  it('calls onSave when save button is clicked', async () => {
    const user = userEvent.setup()
    mockOnSave.mockResolvedValue(undefined)
    
    render(
      <LessonEditor
        content="Test content"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    )

    await user.click(screen.getByText('Save'))
    expect(mockOnSave).toHaveBeenCalledWith('Test content')
  })

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup()
    
    render(
      <LessonEditor
        content="Test content"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    )

    await user.click(screen.getByText('Cancel'))
    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('handles keyboard shortcuts', async () => {
    const user = userEvent.setup()
    mockOnSave.mockResolvedValue(undefined)
    
    render(
      <LessonEditor
        content="Test content"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    )

    const textarea = screen.getByDisplayValue('Test content')
    
    // Ctrl+S saves
    await user.click(textarea)
    await user.keyboard('{Control>}s{/Control}')
    expect(mockOnSave).toHaveBeenCalledWith('Test content')

    // Esc cancels
    await user.keyboard('{Escape}')
    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('toggles fullscreen mode', async () => {
    const user = userEvent.setup()
    
    render(
      <LessonEditor
        content="Test content"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    )

    const fullscreenButton = screen.getByTitle('Enter fullscreen')
    await user.click(fullscreenButton)
    
    expect(screen.getByTitle('Exit fullscreen')).toBeInTheDocument()
  })

  it('shows save status', () => {
    render(
      <LessonEditor
        content="Test content"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        autoSave={false}
      />
    )

    expect(screen.getByText('Saved')).toBeInTheDocument()
  })

  it('updates content when typing', async () => {
    const user = userEvent.setup()
    
    render(
      <LessonEditor
        content="Initial"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        autoSave={false}
      />
    )

    const textarea = screen.getByDisplayValue('Initial')
    await user.clear(textarea)
    await user.type(textarea, 'New content')
    
    expect(screen.getByDisplayValue('New content')).toBeInTheDocument()
  })

  it('shows auto-save status when enabled', () => {
    render(
      <LessonEditor
        content="Test content"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        autoSave={true}
      />
    )

    expect(screen.getByText('Auto-save enabled (2s after typing • every 30s)')).toBeInTheDocument()
  })

  it('hides auto-save status when disabled', () => {
    render(
      <LessonEditor
        content="Test content"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        autoSave={false}
      />
    )

    expect(screen.queryByText('Auto-save enabled')).not.toBeInTheDocument()
  })
})