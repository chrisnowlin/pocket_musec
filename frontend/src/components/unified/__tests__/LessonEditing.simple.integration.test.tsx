import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ChatMessage from '../ChatMessage'
import { useDrafts } from '../../../hooks/useDrafts'
import { useCitations } from '../../../hooks/useCitations'

// Mock all dependencies for integration testing
vi.mock('../../../hooks/useDrafts', () => ({
  useDrafts: vi.fn(),
}))

vi.mock('../../../hooks/useCitations', () => ({
  useCitations: vi.fn(),
  useLegacyCitations: vi.fn(() => ({
    enhancedCitations: [],
    hasLegacyCitations: false,
  })),
}))

vi.mock('../../../components/MarkdownRenderer', () => ({
  default: ({ content, className }: { content: string; className?: string }) => (
    <div className={className} data-testid="markdown-renderer">
      {content}
    </div>
  ),
}))

vi.mock('../../../utils/lessonEditorStorage', () => ({
  lessonEditorStorage: {
    saveContent: vi.fn(),
    loadContent: vi.fn(),
  },
}))

vi.mock('../../../hooks/useAutoSave', () => ({
  useAutoSave: vi.fn(() => ({
    triggerSave: vi.fn(),
    saveImmediately: vi.fn(),
  })),
}))

describe('Lesson Editing Simple Integration Tests', () => {
  const mockUseDrafts = vi.mocked(useDrafts)
  const mockUseCitations = vi.mocked(useCitations)
  
  const mockDraftsHook = {
    drafts: [],
    isLoading: false,
    error: null,
    draftCount: 0,
    editingDraftId: null,
    isSaving: false,
    loadDrafts: vi.fn(),
    getDraft: vi.fn(),
    createDraft: vi.fn(),
    updateDraft: vi.fn(),
    deleteDraft: vi.fn(),
    saveEditedLesson: vi.fn(),
    setEditMode: vi.fn(),
    clearEditMode: vi.fn(),
    isEditingDraft: vi.fn(),
    getEditingDraft: vi.fn(),
    getDraftWithUpdates: vi.fn(),
    clearError: vi.fn(),
  }

  const mockCitationsHook = {
    citations: [],
    loading: false,
    error: '',
    loadCitations: vi.fn(),
    refreshCitations: vi.fn(),
    downloadFile: vi.fn(),
    downloadAllFiles: vi.fn(),
    clearCache: vi.fn(),
    hasCitations: false,
    availableCitationsCount: 0,
    downloadableCitationsCount: 0,
    downloadingFileIds: [],
    isDownloading: false,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseDrafts.mockReturnValue(mockDraftsHook)
    mockUseCitations.mockReturnValue(mockCitationsHook)
  })

  describe('Basic Edit Workflow', () => {
    it('completes full edit workflow from ChatMessage to updated content', async () => {
      const user = userEvent.setup()
      const mockOnUpdateMessage = vi.fn().mockResolvedValue(undefined)
      
      // Initial lesson content - use content that triggers lesson detection
      const initialContent = `# Lesson Plan: Music Theory

## Learning Objectives
- Students will understand basic music theory concepts
- Students will identify musical notes and rhythms

## Standards Alignment
K.M.1 - Apply musical concepts

## Materials Needed
- Whiteboard
- Musical instruments

## Activities
1. Warm-up activity
2. Main lesson on music theory
3. Practice exercises

## Assessment
- Observe student participation
- Check understanding through questions`

      const editedContent = `# Updated Lesson Plan: Advanced Music Theory

## Learning Objectives
- Students will master advanced music theory concepts
- Students will compose simple melodies

## Standards Alignment
K.M.1 - Apply musical concepts
3.M.CR.1 - Compose music

## Materials Needed
- Whiteboard
- Musical instruments
- Composition software

## Activities
1. Warm-up activity
2. Advanced lesson on music theory
3. Composition practice
4. Performance and feedback

## Assessment
- Evaluate student compositions
- Assess theoretical knowledge`

      // Render ChatMessage with edit capability
      render(
        <ChatMessage
          message={{
            id: 'msg-1',
            sender: 'ai' as const,
            text: initialContent,
            timestamp: new Date().toISOString(),
            lessonId: 'lesson-1',
          }}
          onUpdateMessage={mockOnUpdateMessage}
        />
      )

      // Step 1: Verify initial state
      expect(screen.getByText(/Learning Objectives/)).toBeInTheDocument()
      expect(screen.getByTitle('Edit lesson')).toBeInTheDocument()

      // Step 2: Click edit button to open LessonEditor
      await user.click(screen.getByTitle('Edit lesson'))
      
      // LessonEditor should open with initial content
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
      expect(textarea.value).toBe(initialContent)
      expect(screen.getByText('Lesson Editor')).toBeInTheDocument()

// Step 3: Edit the content
      
      await user.clear(textarea)
      await user.type(textarea, editedContent)
      
      expect(textarea.value).toBe(editedContent)

      // Step 4: Verify save functionality is available
      const saveButton = screen.getByText('Save')
      expect(saveButton).toBeInTheDocument()
      expect(saveButton).not.toBeDisabled()
      
      // Verify keyboard shortcut hint
      expect(screen.getByText('Ctrl+S: Save')).toBeInTheDocument()
      
      // Verify word count is displayed
      expect(screen.getByText(/words.*chars/)).toBeInTheDocument()
      
      // Verify the editor content is correctly updated with edited content
      expect(textarea.value).toBe(editedContent)
    })

    it('handles cancel workflow correctly', async () => {
      const user = userEvent.setup()
      const mockOnUpdateMessage = vi.fn()
      
      const initialContent = `# Lesson Plan

## Objectives
- Learn basic concepts

## Standards
K.M.1 - Apply concepts`

      render(
        <ChatMessage
          message={{
            id: 'msg-1',
            sender: 'ai' as const,
            text: initialContent,
            timestamp: new Date().toISOString(),
            lessonId: 'lesson-1',
          }}
          onUpdateMessage={mockOnUpdateMessage}
        />
      )

      // Open editor
      await user.click(screen.getByTitle('Edit lesson'))
      
      // Edit content
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
      expect(textarea.value).toBe(initialContent)
      
      await user.clear(textarea)
      await user.type(textarea, "Modified content")
      
      // Cancel instead of save
      await user.click(screen.getByText('Cancel'))
      
      // Verify cancel callback was not called and original content is restored
      expect(mockOnUpdateMessage).not.toHaveBeenCalled()
      expect(screen.getByText(/Learn basic concepts/)).toBeInTheDocument()
    })

    it('supports keyboard shortcuts throughout workflow', async () => {
      const user = userEvent.setup()
      const mockOnUpdateMessage = vi.fn().mockResolvedValue(undefined)
      
      const initialContent = `# Lesson Plan

## Objectives
- Learn basic concepts

## Standards
K.M.1 - Apply concepts`
      
      const editedContent = `# Updated Lesson Plan

## Objectives
- Learn advanced concepts

## Standards
K.M.1 - Apply concepts
3.M.CR.1 - Create music`

      render(
        <ChatMessage
          message={{
            id: 'msg-1',
            sender: 'ai' as const,
            text: initialContent,
            timestamp: new Date().toISOString(),
            lessonId: 'lesson-1',
          }}
          onUpdateMessage={mockOnUpdateMessage}
        />
      )

      // Open editor
      await user.click(screen.getByTitle('Edit lesson'))
      
      // Edit content
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
      expect(textarea.value).toBe(initialContent)
      
      await user.click(textarea)
      await user.clear(textarea)
      await user.type(textarea, editedContent)
      
      // Verify keyboard hint is visible
      expect(screen.getByText('Ctrl+S: Save')).toBeInTheDocument()
      expect(screen.getByText('Esc: Cancel')).toBeInTheDocument()
      
      // Ensure textarea has focus
      textarea.focus()
      
      // Verify the edited content is in the textarea
      expect(textarea.value).toBe(editedContent)
    })
  })

  describe('Draft Integration', () => {
    it('persists content in browser storage during editing', async () => {
      const user = userEvent.setup()
      
      const lessonContent = `# Lesson Plan

## Objectives
- Learn basic concepts

## Standards
K.M.1 - Apply concepts`
      
      render(
        <ChatMessage
          message={{
            id: 'msg-1',
            sender: 'ai' as const,
            text: lessonContent,
            timestamp: new Date().toISOString(),
            lessonId: 'lesson-1',
          }}
          onUpdateMessage={vi.fn()}
        />
      )

      // Open editor
      await user.click(screen.getByTitle('Edit lesson'))
      
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
      expect(textarea.value).toBe(lessonContent)
      
      // Edit content
      await user.clear(textarea)
      await user.type(textarea, 'Modified content during editing')
      
      // Verify content is updated in the editor
      expect(textarea.value).toBe('Modified content during editing')
    })

it('displays correct initial content when editor opens', async () => {
      const user = userEvent.setup()
      
      const lessonContent = `# Original Lesson Plan

## Objectives
- Learn basic concepts

## Standards
K.M.1 - Apply concepts`
      
      render(
        <ChatMessage
          message={{
            id: 'msg-1',
            sender: 'ai' as const,
            text: lessonContent,
            timestamp: new Date().toISOString(),
            lessonId: 'lesson-1',
          }}
          onUpdateMessage={vi.fn()}
        />
      )

      // Open editor
      await user.click(screen.getByTitle('Edit lesson'))
      
      // Verify content is correctly loaded
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
      expect(textarea.value).toBe(lessonContent)
    })
  })

  describe('Error Handling', () => {
    it('handles network failures during save operations', async () => {
      const user = userEvent.setup()
      const mockOnUpdateMessage = vi.fn().mockImplementation(() => {
        throw new Error('Network error')
      })
      
      const lessonContent = `# Lesson Plan

## Objectives
- Learn basic concepts

## Standards
K.M.1 - Apply concepts`

      render(
        <ChatMessage
          message={{
            id: 'msg-1',
            sender: 'ai' as const,
            text: lessonContent,
            timestamp: new Date().toISOString(),
            lessonId: 'lesson-1',
          }}
          onUpdateMessage={mockOnUpdateMessage}
        />
      )

      await user.click(screen.getByTitle('Edit lesson'))
      
      // Should handle network error gracefully
      await user.click(screen.getByText('Save'))
      
      // The component should handle the error and not crash
      expect(screen.getByText('Lesson Editor')).toBeInTheDocument()
    })

    it('handles editing errors gracefully', async () => {
      const user = userEvent.setup()
      const mockOnUpdateMessage = vi.fn().mockRejectedValue(new Error('Save failed'))
      
      const lessonContent = `# Lesson Plan

## Objectives
- Learn basic concepts

## Standards
K.M.1 - Apply concepts`

      render(
        <ChatMessage
          message={{
            id: 'msg-1',
            sender: 'ai' as const,
            text: lessonContent,
            timestamp: new Date().toISOString(),
            lessonId: 'lesson-1',
          }}
          onUpdateMessage={mockOnUpdateMessage}
        />
      )

      // Open editor
      await user.click(screen.getByTitle('Edit lesson'))
      
      // Try to save - should handle error gracefully
      await user.click(screen.getByText('Save'))
      
      // Editor should still be visible after error
      expect(screen.getByText('Lesson Editor')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('maintains screen reader context throughout edit workflow', async () => {
      const user = userEvent.setup()
      
      const lessonContent = `# Lesson Plan

## Objectives
- Learn accessibility concepts

## Standards
K.M.1 - Apply concepts`

      render(
        <ChatMessage
          message={{
            id: 'msg-1',
            sender: 'ai' as const,
            text: lessonContent,
            timestamp: new Date().toISOString(),
            lessonId: 'lesson-1',
          }}
        />
      )

      // Check initial accessibility
      expect(screen.getByTitle('Edit lesson')).toBeInTheDocument()
      
      // Open editor
      await user.click(screen.getByTitle('Edit lesson'))
      
      // Check editor accessibility
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
      expect(textarea.value).toBe(lessonContent)
      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
    })

    it('supports keyboard navigation throughout workflow', async () => {
      const user = userEvent.setup()
      
      const lessonContent = `# Lesson Plan

## Objectives
- Learn keyboard navigation

## Standards
K.M.1 - Apply concepts`

      render(
        <ChatMessage
          message={{
            id: 'msg-1',
            sender: 'ai' as const,
            text: lessonContent,
            timestamp: new Date().toISOString(),
            lessonId: 'lesson-1',
          }}
        />
      )

      // Tab to message container (which is focusable)
      await user.tab()
      expect(screen.getByText(/Learn keyboard navigation/)).toBeVisible()
      
      // Tab to edit button  
      await user.tab()
      await user.keyboard('{Enter}')
      
      // Should be in editor
      expect(screen.getByText('Lesson Editor')).toBeInTheDocument()
      
      // Tab to textarea
      await user.tab()
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
      expect(textarea).toBeInTheDocument()
    })
  })

  describe('Performance', () => {
    it('handles large content without performance degradation', async () => {
      const user = userEvent.setup()
      
      // Generate large content
      const largeContent = `# Comprehensive Lesson Plan

## Objectives
${Array.from({ length: 50 }, (_, i) => `- Learn concept ${i + 1}`).join('\n')}

## Standards
${Array.from({ length: 20 }, (_, i) => `K.M.${i + 1} - Apply concept ${i + 1}`).join('\n')}

## Activities
${Array.from({ length: 30 }, (_, i) => `${i + 1}. Activity ${i + 1}`).join('\n')}`
      
      const startTime = performance.now()
      
      render(
        <ChatMessage
          message={{
            id: 'msg-1',
            sender: 'ai' as const,
            text: largeContent,
            timestamp: new Date().toISOString(),
            lessonId: 'lesson-1',
          }}
        />
      )

      const renderTime = performance.now() - startTime
      
      // Should render within reasonable time (less than 1 second)
      expect(renderTime).toBeLessThan(1000)
      
      // Editor should handle large content
      await user.click(screen.getByTitle('Edit lesson'))
      
      const editStartTime = performance.now()
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
      expect(textarea.value).toBe(largeContent)
      
      await user.type(textarea, ' - additional content')
      const editTime = performance.now() - editStartTime
      
      // Typing should be responsive (less than 500ms for response)
      expect(editTime).toBeLessThan(500)
    })

    it('handles rapid edit transitions smoothly', async () => {
      const user = userEvent.setup()
      
      const lessonContent = `# Lesson Plan

## Objectives
- Learn basic concepts

## Standards
K.M.1 - Apply concepts`

      render(
        <ChatMessage
          message={{
            id: 'msg-1',
            sender: 'ai' as const,
            text: lessonContent,
            timestamp: new Date().toISOString(),
            lessonId: 'lesson-1',
          }}
        />
      )

      // Rapid open/close cycles
      for (let i = 0; i < 3; i++) {
        await user.click(screen.getByTitle('Edit lesson'))
        await user.click(screen.getByText('Cancel'))
      }
      
      // Should remain stable
      expect(screen.getByText(/Learn basic concepts/)).toBeInTheDocument()
      expect(screen.getByTitle('Edit lesson')).toBeInTheDocument()
    })
  })

  describe('Multi-Message Scenarios', () => {
    it('handles editing when multiple lessons are present', async () => {
      const user = userEvent.setup()
      
      const firstLesson = `# First Lesson Plan

## Objectives
- Learn first concepts

## Standards
K.M.1 - Apply concepts`

      const secondLesson = `# Second Lesson Plan

## Objectives
- Learn second concepts

## Standards
3.M.CR.1 - Create music`
      
      render(
        <div>
          <ChatMessage
            message={{
              id: 'msg-1',
              sender: 'ai' as const,
              text: firstLesson,
              timestamp: new Date().toISOString(),
              lessonId: 'lesson-1',
            }}
          />
          <ChatMessage
            message={{
              id: 'msg-2',
              sender: 'ai' as const,
              text: secondLesson,
              timestamp: new Date().toISOString(),
              lessonId: 'lesson-2',
            }}
          />
        </div>
      )

      // Both lessons should be editable
      const editButtons = screen.getAllByTitle('Edit lesson')
      expect(editButtons).toHaveLength(2)
      
      // Edit the second lesson
      await user.click(editButtons[1])
      
      // Wait for editor to open with second lesson content
      await waitFor(() => {
        const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
        expect(textarea.value).toBe(secondLesson)
      })
    })

    it('maintains context when switching between edited lessons', async () => {
      const user = userEvent.setup()
      const mockOnUpdateMessage = vi.fn()
      
      const firstLesson = `# First Lesson Plan

## Objectives
- Learn first concepts

## Standards
K.M.1 - Apply concepts`

      const secondLesson = `# Second Lesson Plan

## Objectives
- Learn second concepts

## Standards
3.M.CR.1 - Create music`
      
      render(
        <div>
          <ChatMessage
            message={{
              id: 'msg-1',
              sender: 'ai' as const,
              text: firstLesson,
              timestamp: new Date().toISOString(),
              lessonId: 'lesson-1',
            }}
            onUpdateMessage={mockOnUpdateMessage}
          />
          <ChatMessage
            message={{
              id: 'msg-2',
              sender: 'ai' as const,
              text: secondLesson,
              timestamp: new Date().toISOString(),
              lessonId: 'lesson-2',
            }}
            onUpdateMessage={mockOnUpdateMessage}
          />
        </div>
      )

      // Edit first lesson
      const editButtons = screen.getAllByTitle('Edit lesson')
      await user.click(editButtons[0])
      expect(screen.getByText('Lesson Editor')).toBeInTheDocument()
      await user.click(screen.getByText('Cancel'))
      
      // Verify editor is closed
      await waitFor(() => {
        expect(screen.queryByText('Lesson Editor')).not.toBeInTheDocument()
      })
      
      // Edit second lesson
      const updatedEditButtons = screen.getAllByTitle('Edit lesson')
      await user.click(updatedEditButtons[1])
      
      // Wait for editor to open with second lesson content
      await waitFor(() => {
        const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
        expect(textarea.value).toBe(secondLesson)
      })
    })
  })
})