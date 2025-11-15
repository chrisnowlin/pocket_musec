import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ChatMessage from '../ChatMessage'
import type { ChatMessage as ChatMessageType } from '../../../types/unified'
import type { EnhancedCitation } from '../../../types/fileStorage'

const mockDownloadFile = vi.fn()
const mockUseCitations = vi.fn()

// Mock the LessonEditor
vi.mock('../LessonEditor', () => ({
  default: ({ 
    content, 
    onSave, 
    onCancel 
  }: { 
    content: string; 
    onSave: (content: string) => Promise<void>; 
    onCancel: () => void;
  }) => (
    <div data-testid="lesson-editor">
      <textarea data-testid="editor-textarea" defaultValue={content} />
      <button onClick={() => onSave(content)} data-testid="editor-save">Save</button>
      <button onClick={onCancel} data-testid="editor-cancel">Cancel</button>
    </div>
  ),
}))

// Mock the MarkdownRenderer
vi.mock('../../components/MarkdownRenderer', () => ({
  default: ({ content }: { content: string }) => (
    <div data-testid="markdown-renderer">{content}</div>
  ),
}))

// Mock the citation hooks
vi.mock('../../hooks/useCitations', () => ({
  useCitations: (...args: unknown[]) => mockUseCitations(...args),
}))

// Mock the CitationList and CitationErrorBoundary
vi.mock('../CitationList', () => ({
  default: () => <div data-testid="citation-list" />,
}))

vi.mock('../CitationErrorBoundary', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

describe('ChatMessage', () => {
  const mockOnUpdateMessage = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockDownloadFile.mockReset()
    mockUseCitations.mockReset()
    mockUseCitations.mockReturnValue({
      citations: [],
      loading: false,
      downloadFile: mockDownloadFile,
    })
  })

  const createMockMessage = (overrides: Partial<ChatMessageType> = {}): ChatMessageType => ({
    id: '1',
    sender: 'ai',
    text: 'Test message',
    timestamp: '2024-01-01T00:00:00Z',
    ...overrides,
  })

  const buildMockCitations = (count: number): EnhancedCitation[] =>
    Array.from({ length: count }, (_, index) => ({
      id: `citation-${index}`,
      citation_number: index + 1,
      source_title: `Source ${index + 1}`,
      source_type: 'document',
      citation_text: `Citation text ${index + 1}`,
      is_file_available: false,
      can_download: false,
    }))

  it('renders user message correctly', () => {
    const message = createMockMessage({ sender: 'user', text: 'User input' })
    
    render(
      <ChatMessage
        message={message}
        onUpdateMessage={mockOnUpdateMessage}
      />
    )

    expect(screen.getByText('You')).toBeInTheDocument()
    expect(screen.getByText('User input')).toBeInTheDocument()
    expect(screen.queryByText('PocketMusec AI')).not.toBeInTheDocument()
  })

  it('renders AI message correctly', () => {
    const message = createMockMessage({ sender: 'ai', text: 'AI response' })
    
    render(
      <ChatMessage
        message={message}
        onUpdateMessage={mockOnUpdateMessage}
      />
    )

    expect(screen.getByText('PocketMusec AI')).toBeInTheDocument()
    expect(screen.getByText('AI response')).toBeInTheDocument()
    expect(screen.queryByText('You')).not.toBeInTheDocument()
  })

  it('shows edit button for lesson content when hovered', async () => {
    const message = createMockMessage({ 
      text: 'Lesson plan\n\n## Objectives\nStudents will learn...' 
    })
    
    render(
      <ChatMessage
        message={message}
        onUpdateMessage={mockOnUpdateMessage}
      />
    )

    const overlay = screen.getByLabelText('Edit this lesson').parentElement!
    expect(overlay).toHaveAttribute('aria-hidden', 'true')

    const user = userEvent.setup()
    const bubble = screen.getByTestId('chat-message-bubble-1')
    await user.hover(bubble)

    await waitFor(() => {
      expect(overlay).toHaveAttribute('aria-hidden', 'false')
    })
  })

  it('does not render edit controls for non-lesson content', async () => {
    const message = createMockMessage({ 
      text: 'This is just a regular message without lesson structure' 
    })
    
    render(
      <ChatMessage
        message={message}
        onUpdateMessage={mockOnUpdateMessage}
      />
    )

    expect(screen.queryByLabelText('Edit this lesson')).not.toBeInTheDocument()
  })

  it('enters edit mode when edit button is clicked', async () => {
    const message = createMockMessage({ 
      text: '## Lesson Plan\n\n### Objectives\n\nStudents will learn music.' 
    })
    
    render(
      <ChatMessage
        message={message}
        onUpdateMessage={mockOnUpdateMessage}
      />
    )

    // Hover and click edit button
    const user = userEvent.setup()
    const bubble = screen.getByTestId('chat-message-bubble-1')
    await user.hover(bubble)
    await user.click(screen.getByLabelText('Edit this lesson'))

    // Should be in edit mode (LessonEditor loads lazily)
    expect(await screen.findByTestId('lesson-editor')).toBeInTheDocument()
    expect(screen.getByDisplayValue('## Lesson Plan\n\n### Objectives\n\nStudents will learn music.')).toBeInTheDocument()
  })

  it('saves edited content and exits edit mode', async () => {
    const message = createMockMessage({ 
      text: '## Lesson Plan\n\n### Objectives' 
    })
    mockOnUpdateMessage.mockResolvedValue(undefined)
    
    render(
      <ChatMessage
        message={message}
        onUpdateMessage={mockOnUpdateMessage}
      />
    )

    // Enter edit mode
    const user = userEvent.setup()
    const bubble = screen.getByTestId('chat-message-bubble-1')
    await user.hover(bubble)
    await user.click(screen.getByLabelText('Edit this lesson'))

    // Save the edit
    await user.click(screen.getByTestId('editor-save'))

    // Should call update and exit edit mode
    await waitFor(() => {
      expect(mockOnUpdateMessage).toHaveBeenCalledWith('1', '## Lesson Plan\n\n### Objectives')
    })
    expect(screen.queryByTestId('lesson-editor')).not.toBeInTheDocument()
    expect(screen.getByTestId('markdown-renderer')).toBeInTheDocument()
  })

  it('cancels edit and returns to view mode', async () => {
    const message = createMockMessage({ 
      text: '## Lesson Plan\n\n### Objectives' 
    })
    
    render(
      <ChatMessage
        message={message}
        onUpdateMessage={mockOnUpdateMessage}
      />
    )

    // Enter edit mode
    const user = userEvent.setup()
    const bubble = screen.getByTestId('chat-message-bubble-1')
    await user.hover(bubble)
    await user.click(screen.getByLabelText('Edit this lesson'))

    // Cancel the edit
    await user.click(screen.getByTestId('editor-cancel'))

    // Should exit edit mode without saving
    expect(mockOnUpdateMessage).not.toHaveBeenCalled()
    expect(screen.queryByTestId('lesson-editor')).not.toBeInTheDocument()
    expect(screen.getByTestId('markdown-renderer')).toBeInTheDocument()
  })

  it('shows modified indicator for modified messages', () => {
    const message = createMockMessage({ 
      isModified: true 
    })
    
    render(
      <ChatMessage
        message={message}
        onUpdateMessage={mockOnUpdateMessage}
      />
    )

    expect(screen.getByText('Modified')).toBeInTheDocument()
  })

  it('does not show modified indicator for unmodified messages', () => {
    const message = createMockMessage({ 
      isModified: false 
    })
    
    render(
      <ChatMessage
        message={message}
        onUpdateMessage={mockOnUpdateMessage}
      />
    )

    expect(screen.queryByText('Modified')).not.toBeInTheDocument()
  })

  it('displays citations when provided from the enhanced citations hook', () => {
    mockUseCitations.mockReturnValue({
      citations: buildMockCitations(2),
      loading: false,
      downloadFile: mockDownloadFile,
    })

    const message = createMockMessage({ lessonId: 'lesson-123' })
    
    render(
      <ChatMessage
        message={message}
        onUpdateMessage={mockOnUpdateMessage}
        lessonId="lesson-123"
      />
    )

    expect(screen.getByRole('button', { name: /Sources & Citations \(2\)/ })).toBeInTheDocument()
  })

  it('toggles citations visibility', async () => {
    mockUseCitations.mockReturnValue({
      citations: buildMockCitations(1),
      loading: false,
      downloadFile: mockDownloadFile,
    })

    const message = createMockMessage({ lessonId: 'lesson-456' })
    
    render(
      <ChatMessage
        message={message}
        onUpdateMessage={mockOnUpdateMessage}
        lessonId="lesson-456"
      />
    )

    const user = userEvent.setup()
    const toggleButton = screen.getByRole('button', { name: /Sources & Citations \(1\)/ })

    expect(screen.queryByTestId('citation-list')).not.toBeInTheDocument()

    await user.click(toggleButton)
    expect(screen.getByTestId('citation-list')).toBeInTheDocument()

    await user.click(toggleButton)
    expect(screen.queryByTestId('citation-list')).not.toBeInTheDocument()
  })
})