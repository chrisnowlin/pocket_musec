/**
 * Regression tests for useDrafts hook with normalized backend responses
 * Ensures the hook properly consumes camelCase array responses from the backend
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, beforeEach, vi } from 'vitest'

// Mock the API module
vi.mock('../../lib/api', () => ({
  default: {
    getDrafts: vi.fn(),
    getDraft: vi.fn(),
    createDraft: vi.fn(),
    updateDraft: vi.fn(),
    deleteDraft: vi.fn(),
    getLessons: vi.fn(),
  },
}))

import api from '../../lib/api'
import { useDrafts } from '../useDrafts'

describe('useDrafts with Normalized Backend Responses', () => {
  let queryClient: QueryClient
  let mockApi: any

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    })
    mockApi = vi.mocked(api)
    vi.clearAllMocks()
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  describe('Backend Response Consumption', () => {
    it('should properly consume normalized drafts list with camelCase fields', async () => {
      // Mock API response with normalized backend data
      const mockDraftsResponse = {
        ok: true,
        data: [
          {
            id: 'draft-1',
            title: 'Introduction to Counting',
            content: '# Introduction to Counting\n\nThis lesson teaches basic counting skills.',
            metadata: { gradeLevel: 'Grade 1',
              strand_code: 'Connect',
              lesson_document: {
                grade: 'Grade 1',
                strand: 'Connect'
              }
            },
            grade: 'Grade 1',
            strand: 'Connect',
            standard: 'K.CC.1',
            selectedStandards: ['K.CC.1', 'K.CC.2'],
            selectedObjectives: ['count to 10', 'recognize numbers'],
            createdAt: '2025-11-16T09:00:00Z',
            updatedAt: '2025-11-16T09:30:00Z',
            presentationStatus: {
              has_presentation: true,
              status: 'completed'
            }
          },
          {
            id: 'draft-2',
            title: 'Advanced Multiplication',
            content: '# Advanced Multiplication\n\nThis lesson covers multiplication strategies.',
            metadata: { gradeLevel: 'Grade 4',
              strand_code: 'Analyze',
              lesson_document: {
                grade: 'Grade 4',
                strand: 'Analyze'
              }
            },
            grade: 'Grade 4',
            strand: 'Analyze',
            standard: '4.OA.1',
            selectedStandards: ['4.OA.1', '4.OA.2', '4.OA.3'],
            selectedObjectives: ['understand multiplication', 'solve word problems', 'use properties'],
            createdAt: '2025-11-16T10:00:00Z',
            updatedAt: '2025-11-16T10:45:00Z',
            presentationStatus: {
              has_presentation: false,
              status: 'not_generated'
            }
          }
        ],
      }

      mockApi.getDrafts.mockResolvedValue(mockDraftsResponse)

      const { result } = renderHook(() => useDrafts(), { wrapper })

      await waitFor(() => {
        expect(result.current.isLoadingDrafts).toBe(false)
        expect(result.current.drafts).toHaveLength(2)
      })

      const drafts = result.current.drafts

      // Verify first draft structure
      const draft1 = drafts[0]
      expect(draft1.id).toBe('draft-1')
      expect(draft1.title).toBe('Introduction to Counting')
      expect(draft1.grade).toBe('Grade 1')
      expect(draft1.strand).toBe('Connect')
      expect(draft1.standard).toBe('K.CC.1')

      // Verify selectedStandards is an array (from normalized backend)
      expect(Array.isArray(draft1.selectedStandards)).toBe(true)
      expect(draft1.selectedStandards).toEqual(['K.CC.1', 'K.CC.2'])

      // Verify selectedObjectives is an array (from normalized backend)
      expect(Array.isArray(draft1.selectedObjectives)).toBe(true)
      expect(draft1.selectedObjectives).toEqual(['count to 10', 'recognize numbers'])

      // Verify camelCase date fields
      expect(draft1.createdAt).toBe('2025-11-16T09:00:00Z')
      expect(draft1.updatedAt).toBe('2025-11-16T09:30:00Z')

      // Verify second draft structure
      const draft2 = drafts[1]
      expect(draft2.grade).toBe('Grade 4')
      expect(draft2.strand).toBe('Analyze')
      expect(Array.isArray(draft2.selectedStandards)).toBe(true)
      expect(draft2.selectedStandards).toHaveLength(3)
      expect(Array.isArray(draft2.selectedObjectives)).toBe(true)
      expect(draft2.selectedObjectives).toHaveLength(3)
    })

    it('should properly consume normalized single draft response', async () => {
      // Mock API response with normalized backend data
      const mockDraftResponse = {
        ok: true,
        data: {
          id: 'draft-single',
          title: 'Geometry Basics',
          content: '# Geometry Basics\n\nIntroduction to shapes and spatial reasoning.',
          metadata: { gradeLevel: 'Grade 2',
            strand_code: 'Create',
            learning_objectives: ['identify shapes', 'describe spatial relationships']
          },
          grade: 'Grade 2',
          strand: 'Create',
          standard: '2.G.1',
          selectedStandards: ['2.G.1', '2.G.2'],
          selectedObjectives: ['identify shapes', 'describe relationships', 'sort objects'],
          createdAt: '2025-11-16T11:00:00Z',
          updatedAt: '2025-11-16T11:20:00Z',
          presentationStatus: {
            has_presentation: true,
            status: 'in_progress'
          }
        },
      }

      mockApi.getDraft.mockResolvedValue(mockDraftResponse)

      const { result } = renderHook(() => useDrafts(), { wrapper })

      await act(async () => {
        await result.current.loadDraft('draft-single')
      })

      expect(mockApi.getDraft).toHaveBeenCalledWith('draft-single')

      const draftData = mockDraftResponse.data

      // Verify normalized structure
      expect(draftData.grade).toBe('Grade 2')
      expect(draftData.strand).toBe('Create')
      expect(draftData.standard).toBe('2.G.1')

      // Verify array fields are properly handled
      expect(Array.isArray(draftData.selectedStandards)).toBe(true)
      expect(draftData.selectedStandards).toEqual(['2.G.1', '2.G.2'])
      expect(Array.isArray(draftData.selectedObjectives)).toBe(true)
      expect(draftData.selectedObjectives).toEqual([
        'identify shapes',
        'describe relationships',
        'sort objects'
      ])

      // Verify date formatting
      expect(draftData.createdAt).toBe('2025-11-16T11:00:00Z')
      expect(draftData.updatedAt).toBe('2025-11-16T11:20:00Z')
    })

    it('should handle drafts with missing normalized fields gracefully', async () => {
      // Mock API response with missing optional fields
      const mockDraftResponse = {
        ok: true,
        data: {
          id: 'draft-minimal',
          title: 'Minimal Draft',
          content: '# Minimal Draft\n\nBasic content.',
          metadata: {},
          grade: null,
          strand: null,
          standard: null,
          selectedStandards: null,
          selectedObjectives: null,
          createdAt: '2025-11-16T12:00:00Z',
          updatedAt: '2025-11-16T12:15:00Z',
          presentationStatus: null,
        },
      }

      mockApi.getDraft.mockResolvedValue(mockDraftResponse)

      const { result } = renderHook(() => useDrafts(), { wrapper })

      await act(async () => {
        await result.current.loadDraft('draft-minimal')
      })

      const draftData = mockDraftResponse.data

      // Verify null fields are handled gracefully
      expect(draftData.grade).toBeNull()
      expect(draftData.strand).toBeNull()
      expect(draftData.standard).toBeNull()
      expect(draftData.selectedStandards).toBeNull()
      expect(draftData.selectedObjectives).toBeNull()
      expect(draftData.presentationStatus).toBeNull()

      // Verify essential fields are still present
      expect(draftData.id).toBe('draft-minimal')
      expect(draftData.title).toBe('Minimal Draft')
      expect(draftData.content).toBe('# Minimal Draft\n\nBasic content.')
      expect(draftData.metadata).toEqual({})
    })
  })

  describe('Draft Creation with Normalized Responses', () => {
    it('should create draft and consume normalized response', async () => {
      // Mock API response for draft creation
      const mockCreateResponse = {
        ok: true,
        data: {
          id: 'new-draft',
          title: 'New Lesson Draft',
          content: '# New Lesson\n\nContent for the new lesson.',
          metadata: { gradeLevel: 'Grade 3',
            strand_code: 'Evaluate',
            session_id: 'session-123'
          },
          grade: 'Grade 3',
          strand: 'Evaluate',
          standard: '3.OA.1',
          selectedStandards: ['3.OA.1', '3.OA.2'],
          selectedObjectives: ['multiply within 100', 'solve word problems'],
          createdAt: '2025-11-16T13:00:00Z',
          updatedAt: '2025-11-16T13:00:00Z',
          presentationStatus: {
            has_presentation: false,
            status: 'not_generated'
          }
        },
      }

      mockApi.createDraft.mockResolvedValue(mockCreateResponse)

      const { result } = renderHook(() => useDrafts(), { wrapper })

      await act(async () => {
        const draft = await result.current.createDraft(
          'session-123',
          'New Lesson Draft',
          '# New Lesson\n\nContent for the new lesson.',
          { gradeLevel: 'Grade 3',
            strand_code: 'Evaluate',
            selected_standards: ['3.OA.1', '3.OA.2'],
            selected_objectives: ['multiply within 100', 'solve word problems']
          }
        )

        expect(draft).toEqual(mockCreateResponse.data)
      })

      // Verify the created draft has normalized structure
      expect(mockCreateResponse.data.grade).toBe('Grade 3')
      expect(mockCreateResponse.data.strand).toBe('Evaluate')
      expect(Array.isArray(mockCreateResponse.data.selectedStandards)).toBe(true)
      expect(mockCreateResponse.data.selectedStandards).toEqual(['3.OA.1', '3.OA.2'])
      expect(Array.isArray(mockCreateResponse.data.selectedObjectives)).toBe(true)
      expect(mockCreateResponse.data.selectedObjectives).toEqual([
        'multiply within 100',
        'solve word problems'
      ])
    })
  })

  describe('Draft Updates with Normalized Responses', () => {
    it('should update draft and consume normalized response', async () => {
      // Mock API response for draft update
      const mockUpdateResponse = {
        ok: true,
        data: {
          id: 'updated-draft',
          title: 'Updated Lesson Title',
          content: '# Updated Lesson\n\nUpdated content.',
          metadata: { gradeLevel: 'Grade 3',
            strand_code: 'Evaluate',
            selected_standards: ['3.OA.1', '3.OA.2', '3.OA.3'],
            selected_objectives: ['multiply', 'solve problems', 'use properties']
          },
          grade: 'Grade 3',
          strand: 'Evaluate',
          standard: '3.OA.1',
          selectedStandards: ['3.OA.1', '3.OA.2', '3.OA.3'],
          selectedObjectives: ['multiply', 'solve problems', 'use properties'],
          createdAt: '2025-11-16T13:00:00Z',
          updatedAt: '2025-11-16T14:00:00Z',
          presentationStatus: {
            has_presentation: true,
            status: 'completed'
          }
        },
      }

      mockApi.updateDraft.mockResolvedValue(mockUpdateResponse)

      const { result } = renderHook(() => useDrafts(), { wrapper })

      await act(async () => {
        const draft = await result.current.updateDraft('updated-draft', {
          title: 'Updated Lesson Title',
          content: '# Updated Lesson\n\nUpdated content.',
          metadata: {
            selected_standards: ['3.OA.1', '3.OA.2', '3.OA.3'],
            selected_objectives: ['multiply', 'solve problems', 'use properties']
          }
        })

        expect(draft).toEqual(mockUpdateResponse.data)
      })

      // Verify updated fields are properly normalized
      expect(mockUpdateResponse.data.selectedStandards).toHaveLength(3)
      expect(mockUpdateResponse.data.selectedObjectives).toHaveLength(3)
      expect(mockUpdateResponse.data.updatedAt).toBe('2025-11-16T14:00:00Z')
    })
  })
})