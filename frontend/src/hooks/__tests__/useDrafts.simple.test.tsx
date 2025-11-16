import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useDrafts } from '../useDrafts'
import type { DraftItem } from '../../types/unified'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

// Simple mock approach
vi.mock('../../lib/api', () => ({
  default: {
    getDrafts: vi.fn().mockResolvedValue({ ok: true, data: [], message: null }),
    getDraft: vi.fn().mockResolvedValue({ ok: true, data: null, message: null }),
    createDraft: vi.fn().mockResolvedValue({ ok: true, data: null, message: null }),
    updateDraft: vi.fn().mockResolvedValue({ ok: true, data: null, message: null }),
    deleteDraft: vi.fn().mockResolvedValue({ ok: true, data: null, message: null }),
  },
}))

const createWrapper = () => {
  const queryClient = new QueryClient()
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useDrafts Simple Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('initializes with empty drafts', async () => {
    const wrapper = createWrapper()
    const { result } = renderHook(() => useDrafts(), { wrapper })

    // Initially loading because of useEffect
    expect(result.current.isLoading).toBe(true)
    
    // Wait for initial load to complete
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.drafts).toEqual([])
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBe(null)
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
    const wrapper = createWrapper()
    const { result } = renderHook(() => useDrafts(), { wrapper })

    expect(result.current.isEditingDraft('draft-1')).toBe(false)

    act(() => {
      result.current.setEditMode('draft-1')
    })

    expect(result.current.isEditingDraft('draft-1')).toBe(true)
    expect(result.current.isEditingDraft('draft-2')).toBe(false)
  })

  it('gets editing draft returns null when not editing', () => {
    const wrapper = createWrapper()
    const { result } = renderHook(() => useDrafts(), { wrapper })

    expect(result.current.getEditingDraft()).toBe(null)
  })

  it('clears error state', () => {
    const wrapper = createWrapper()
    const { result } = renderHook(() => useDrafts(), { wrapper })

    // Initially no error
    expect(result.current.error).toBe(null)

    act(() => {
      result.current.clearError()
    })

    expect(result.current.error).toBe(null)
  })

  it('gets draft with updates returns null for non-existent draft', () => {
    const wrapper = createWrapper()
    const { result } = renderHook(() => useDrafts(), { wrapper })

    const updatedDraft = result.current.getDraftWithUpdates('999', {
      title: 'New Title',
    })
    expect(updatedDraft).toBe(null)
  })
})
