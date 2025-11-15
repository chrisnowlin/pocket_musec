import { render, screen, waitFor } from '@testing-library/react'
import { useState } from 'react'
import userEvent from '@testing-library/user-event'
import ChatMessage from '../ChatMessage'
import LessonEditor from '../LessonEditor'
import ExportModal from '../ExportModal'
import type { ChatMessage as ChatMessageType, DraftItem } from '../../../types/unified'

const mockDownloadFile = vi.hoisted(() => vi.fn())
const mockUseCitations = vi.hoisted(() => vi.fn(() => ({
  citations: [],
  loading: false,
  downloadFile: mockDownloadFile,
})))

vi.mock('../../hooks/useCitations', () => ({
  useCitations: () => mockUseCitations(),
}))

const lessonEditorStorageMock = vi.hoisted(() => ({
  saveContent: vi.fn().mockResolvedValue(undefined),
  loadContent: vi.fn().mockResolvedValue(null),
  deleteContent: vi.fn(),
  clearAllContent: vi.fn(),
  formatTimestamp: vi.fn((timestamp: string) => timestamp),
}))

vi.mock('../../../utils/lessonEditorStorage', () => ({
  lessonEditorStorage: lessonEditorStorageMock,
}))

function ChatMessageHarness({
  initialContent,
  mockOnUpdate,
}: {
  initialContent: string
  mockOnUpdate: (id: string, newText: string) => Promise<void>
}) {
  const [message, setMessage] = useState<ChatMessageType>({
    id: 'msg-1',
    sender: 'ai',
    text: initialContent,
    timestamp: '2024-01-01T00:00:00Z',
    lessonId: 'lesson-1',
  })

  const handleUpdate = async (id: string, newText: string) => {
    await mockOnUpdate(id, newText)
    setMessage((prev) => ({ ...prev, text: newText, isModified: true }))
  }

  return (
    <ChatMessage
      message={message}
      onUpdateMessage={handleUpdate}
    />
  )
}

describe('Lesson editing integration flows', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    lessonEditorStorageMock.saveContent.mockResolvedValue(undefined)
    lessonEditorStorageMock.loadContent.mockResolvedValue(null)
  })

  it('performs an inline edit and save through ChatMessage and LessonEditor', async () => {
    const user = userEvent.setup()
    const mockOnUpdateMessage = vi.fn().mockResolvedValue(undefined)

    const initialContent = `# Lesson Plan\n\n## Objectives\n- Explore rhythmic patterns` as const
    const updatedContent = `# Lesson Plan\n\n## Objectives\n- Explore rhythmic patterns\n- Compose a short ostinato`

    render(
      <ChatMessageHarness
        initialContent={initialContent}
        mockOnUpdate={mockOnUpdateMessage}
      />
    )

    const bubble = screen.getByTestId('chat-message-bubble-msg-1')
    await user.hover(bubble)
    await user.click(screen.getByLabelText('Edit this lesson'))

    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
    await user.clear(textarea)
    await user.type(textarea, updatedContent)

    await user.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => {
      expect(mockOnUpdateMessage).toHaveBeenCalledWith('msg-1', updatedContent)
    })

    await waitFor(() => {
      expect(screen.queryByRole('dialog', { name: /Lesson Editor/i })).not.toBeInTheDocument()
    })

    expect(
      screen.getByText((content) => content.includes('Compose a short ostinato'))
    ).toBeInTheDocument()
  })

  it('invokes export handler with the selected format', async () => {
    const user = userEvent.setup()
    const mockOnExport = vi.fn()

    const draft: DraftItem = {
      id: 'draft-1',
      title: 'Percussion Warmup',
      content: 'Clap and echo basic rhythms.',
      grade: 'Grade 3',
      strand: 'Rhythm',
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-02T00:00:00Z',
    }

    render(
      <ExportModal
        isOpen={true}
        onClose={vi.fn()}
        draft={draft}
        onExport={mockOnExport}
        isLoading={false}
      />
    )

    await user.click(screen.getByRole('radio', { name: /PDF/ }))
    await user.click(screen.getByRole('button', { name: /Export as PDF/i }))

    expect(mockOnExport).toHaveBeenCalledWith('pdf')
  })

  it('recovers auto-saved content when lessonEditorStorage has unsaved data', async () => {
    const recoveredContent = '# Autosaved Lesson\n\nRecovered from storage.'
    lessonEditorStorageMock.loadContent.mockResolvedValue(recoveredContent)
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(
      <LessonEditor
        content="# Original Lesson"
        onSave={vi.fn().mockResolvedValue(undefined)}
        onCancel={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(screen.getByRole('textbox')).toHaveValue(recoveredContent)
    })

    expect(confirmSpy).toHaveBeenCalled()
    confirmSpy.mockRestore()
  })
})
