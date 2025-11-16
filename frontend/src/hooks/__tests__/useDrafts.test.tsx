import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useDrafts } from '../useDrafts'
import type { DraftItem } from '../../types/unified'
import type { LessonDocumentM2 } from '../../lib/types'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

// Mock the API client with factory function to avoid hoisting issues
vi.mock('../../lib/api', () => {
  const mockGetDrafts = vi.fn()
  const mockGetDraft = vi.fn()
  const mockCreateDraft = vi.fn()
  const mockUpdateDraft = vi.fn()
  const mockDeleteDraft = vi.fn()

  return {
    default: {
      getDrafts: mockGetDrafts,
      getDraft: mockGetDraft,
      createDraft: mockCreateDraft,
      updateDraft: mockUpdateDraft,
      deleteDraft: mockDeleteDraft,
    },
  }
})

// Get the mocked functions
const apiModule = await import('../../lib/api')
const mockedApi = vi.mocked(apiModule.default, { shallow: false })
const mockGetDrafts = mockedApi.getDrafts
const mockGetDraft = mockedApi.getDraft
const mockCreateDraft = mockedApi.createDraft
const mockUpdateDraft = mockedApi.updateDraft
const mockDeleteDraft = mockedApi.deleteDraft

const createWrapper = () => {
  const queryClient = new QueryClient()
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useDrafts', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetDrafts.mockResolvedValue({
      ok: true,
      data: [],
      message: null,
    })
    mockGetDraft.mockResolvedValue({
      ok: true,
      data: null,
      message: null,
    })
    mockCreateDraft.mockResolvedValue({
      ok: true,
      data: null,
      message: null,
    })
    mockUpdateDraft.mockResolvedValue({
      ok: true,
      data: null,
      message: null,
    })
    mockDeleteDraft.mockResolvedValue({
      ok: true,
      data: null,
      message: null,
    })
  })

  it('initializes with empty drafts', () => {
    const wrapper = createWrapper()
    const { result } = renderHook(() => useDrafts(), { wrapper })

    expect(result.current.drafts).toEqual([])
    expect(result.current.isLoading).toBe(true)
    expect(result.current.error).toBe(null)
    expect(result.current.draftCount).toBe(0)
  })

  it('loads drafts from API', async () => {
    const apiDrafts = [
      { id: '1', title: 'Test Draft', content: 'Content 1', createdAt: '2024-01-01', updatedAt: '2024-01-01' },
      { id: '2', title: 'Test Draft 2', content: 'Content 2', createdAt: '2024-01-02', updatedAt: '2024-01-02' },
    ] as DraftItem[]

    mockGetDrafts.mockResolvedValue({
      ok: true,
      data: apiDrafts,
      message: null,
    })

    const wrapper = createWrapper()
    const { result } = renderHook(() => useDrafts(), { wrapper })

    // Wait for the initial load to complete
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.drafts).toEqual(apiDrafts)
    expect(result.current.draftCount).toBe(2)
    expect(result.current.isLoading).toBe(false)
  })

  it('creates a new draft', async () => {
    const newDraft = {
      id: 'new-id',
      title: 'New Draft',
      content: 'New content',
      createdAt: '2024-01-01',
      updatedAt: '2024-01-01',
    } as DraftItem

    mockCreateDraft.mockResolvedValue({
      ok: true,
      data: newDraft,
      message: null,
    })

    const wrapper = createWrapper()
    const { result } = renderHook(() => useDrafts(), { wrapper })

    await act(async () => {
      const draft = await result.current.createDraft('session-1', 'New Draft', 'New content')
      expect(draft).toEqual(newDraft)
    })

    expect(mockCreateDraft).toHaveBeenCalledWith({
      session_id: 'session-1',
      title: 'New Draft',
      content: 'New content',
      metadata: undefined,
    })
    expect(result.current.drafts).toContain(newDraft)
    expect(result.current.draftCount).toBe(1)
  })

  it('updates an existing draft', async () => {
    const existingDraft = {
      id: '1',
      title: 'Original Title',
      content: 'Original content',
      createdAt: '2024-01-01',
      updatedAt: '2024-01-01',
    } as DraftItem

    const updatedDraft = {
      ...existingDraft,
      title: 'Updated Title',
      content: 'Updated content',
    }

    mockGetDrafts.mockResolvedValue({
      ok: true,
      data: [existingDraft],
      message: null,
    })

    mockUpdateDraft.mockResolvedValue({
      ok: true,
      data: updatedDraft,
      message: null,
    })

    const wrapper = createWrapper()
    const { result } = renderHook(() => useDrafts(), { wrapper })

    // Wait for initial load
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await act(async () => {
      const draft = await result.current.updateDraft('1', {
        title: 'Updated Title',
        content: 'Updated content',
      })
      expect(draft).toEqual(updatedDraft)
    })

    expect(mockUpdateDraft).toHaveBeenCalledWith('1', {
      title: 'Updated Title',
      content: 'Updated content',
    })
    expect(result.current.drafts[0]).toEqual(updatedDraft)
  })

  it('deletes a draft', async () => {
    const draftToDelete = {
      id: '1',
      title: 'To Delete',
      content: 'Content',
      createdAt: '2024-01-01',
      updatedAt: '2024-01-01',
    } as DraftItem

    mockGetDrafts.mockResolvedValue({
      ok: true,
      data: [draftToDelete],
      message: null,
    })

    mockDeleteDraft.mockResolvedValue({
      ok: true,
      data: null,
      message: null,
    })

    const wrapper = createWrapper()
    const { result } = renderHook(() => useDrafts(), { wrapper })

    // Wait for initial load
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.drafts).toHaveLength(1)

    await act(async () => {
      const success = await result.current.deleteDraft('1')
      expect(success).toBe(true)
    })

    expect(mockDeleteDraft).toHaveBeenCalledWith('1')
    expect(result.current.drafts).toHaveLength(0)
    expect(result.current.draftCount).toBe(0)
  })

  it('manages edit mode state', () => {
    const wrapper = createWrapper()
    const { result } = renderHook(() => useDrafts(), { wrapper })

    expect(result.current.editingDraftId).toBe(null)

    act(() => {
      result.current.setEditMode('draft-123')
    })

    expect(result.current.editingDraftId).toBe('draft-123')

    act(() => {
      result.current.clearEditMode()
    })

    expect(result.current.editingDraftId).toBe(null)
  })

  it('checks if editing draft', () => {
    const { result } = renderHook(() => useDrafts(), { wrapper: createWrapper() })

    expect(result.current.isEditingDraft('draft-1')).toBe(false)

    act(() => {
      result.current.setEditMode('draft-1')
    })

    expect(result.current.isEditingDraft('draft-1')).toBe(true)
    expect(result.current.isEditingDraft('draft-2')).toBe(false)
  })

  it('gets editing draft', async () => {
    const draft = {
      id: '1',
      title: 'Test Draft',
      content: 'Content',
      createdAt: '2024-01-01',
      updatedAt: '2024-01-01',
    } as DraftItem

    mockGetDrafts.mockResolvedValue({
      ok: true,
      data: [draft],
      message: null,
    })

    const { result } = renderHook(() => useDrafts(), { wrapper: createWrapper() })

    // Wait for initial load
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    // No editing draft initially
    expect(result.current.getEditingDraft()).toBe(null)

    act(() => {
      result.current.setEditMode('1')
    })

    expect(result.current.getEditingDraft()).toEqual(draft)
  })

  it('saves edited lesson with optimistic updates', async () => {
    const originalDraft = {
      id: '1',
      title: 'Original Title',
      content: 'Original content',
      createdAt: '2024-01-01',
      updatedAt: '2024-01-01',
    } as DraftItem

    const updatedDraft = {
      ...originalDraft,
      content: 'Updated content',
      originalContent: 'Original content',
      updatedAt: expect.any(String),
    }

    mockGetDrafts.mockResolvedValue({
      ok: true,
      data: [originalDraft],
      message: null,
    })

    mockUpdateDraft.mockResolvedValue({
      ok: true,
      data: updatedDraft,
      message: null,
    })

    const { result } = renderHook(() => useDrafts(), { wrapper: createWrapper() })

    // Wait for initial load
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await act(async () => {
      const saved = await result.current.saveEditedLesson('1', 'Updated content')
      expect(saved).toEqual(updatedDraft)
    })

    expect(mockUpdateDraft).toHaveBeenCalledWith('1', {
      content: 'Updated content',
      originalContent: 'Original content',
      updatedAt: expect.any(String),
    })
    expect(result.current.drafts[0]).toEqual(updatedDraft)
  })

  it('handles API errors gracefully', async () => {
    mockGetDrafts.mockResolvedValue({
      ok: false,
      data: [],
      message: 'API Error',
    })

    const { result } = renderHook(() => useDrafts(), { wrapper: createWrapper() })

    // Wait for initial load
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await waitFor(() => {
      expect(result.current.error).toBe('API Error')
      expect(result.current.isLoading).toBe(false)
    })
  })

  it('clears error state', async () => {
    mockGetDrafts.mockResolvedValue({
      ok: false,
      data: [],
      message: 'API Error',
    })

    const { result } = renderHook(() => useDrafts(), { wrapper: createWrapper() })

    // Wait for initial load with error
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await waitFor(() => {
      expect(result.current.error).toBe('API Error')
    })

    act(() => {
      result.current.clearError()
    })

    expect(result.current.error).toBe(null)
  })

  it('gets draft with updates', async () => {
    const draft = {
      id: '1',
      title: 'Original Title',
      content: 'Original content',
      createdAt: '2024-01-01',
      updatedAt: '2024-01-01',
    } as DraftItem

    mockGetDrafts.mockResolvedValue({
      ok: true,
      data: [draft],
      message: null,
    })

    const { result } = renderHook(() => useDrafts(), { wrapper: createWrapper() })

    // Wait for initial load
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    const updatedDraft = result.current.getDraftWithUpdates('1', {
      title: 'New Title',
    })

    expect(updatedDraft).toEqual({
      ...draft,
      title: 'New Title',
    })

    // Non-existent draft returns null
    const nonExistentDraft = result.current.getDraftWithUpdates('999', {
      title: 'New Title',
    })
    expect(nonExistentDraft).toBe(null)
  })

  it('updates m2.0 lesson_document notes when saving edited lesson', async () => {
    const lessonDocument: LessonDocumentM2 = {
      id: 'doc-1',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      version: 'm2.0',
      title: 'Original Title',
      grade: 'Grade 3',
      strands: ['Rhythm'],
      standards: [],
      objectives: [],
      content: {
        materials: [],
        warmup: '',
        activities: [],
        assessment: '',
        differentiation: '',
        exit_ticket: '',
        notes: 'Original content',
        prerequisites: '',
        accommodations: '',
        homework: '',
        reflection: '',
        timing: { total_minutes: 45 },
      },
      citations: [],
      revision: 1,
    };

    const originalDraft = {
      id: '1',
      title: 'Original Title',
      content: 'Original content',
      metadata: {
        lesson_document: lessonDocument,
      },
      createdAt: '2024-01-01',
      updatedAt: '2024-01-01',
    } as DraftItem;

    const updatedDraft = {
      ...originalDraft,
      content: 'Updated content',
      metadata: {
        lesson_document: {
          ...lessonDocument,
          content: {
            ...lessonDocument.content,
            notes: 'Updated content',
          },
          revision: 2,
        },
      },
      originalContent: 'Original content',
      updatedAt: expect.any(String),
    } as DraftItem;

    mockGetDrafts.mockResolvedValue({
      ok: true,
      data: [originalDraft],
      message: null,
    });

    mockUpdateDraft.mockResolvedValue({
      ok: true,
      data: updatedDraft,
      message: null,
    });

    const { result } = renderHook(() => useDrafts(), { wrapper: createWrapper() });

    // Wait for initial load
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    await act(async () => {
      const saved = await result.current.saveEditedLesson('1', 'Updated content');
      expect(saved).toEqual(updatedDraft);
    });

    expect(mockUpdateDraft).toHaveBeenCalledWith('1', expect.objectContaining({
      content: 'Updated content',
      originalContent: 'Original content',
      updatedAt: expect.any(String),
      metadata: {
        lesson_document: expect.objectContaining({
          content: expect.objectContaining({
            notes: 'Updated content',
          }),
        }),
      },
    }));

    expect(result.current.drafts[0]).toEqual(updatedDraft);
  });
});
