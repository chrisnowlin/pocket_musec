/**
 * Simplified regression tests for useDrafts hook with normalized backend responses
 * Focused on verifying proper consumption of camelCase array responses
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

describe('useDrafts with Normalized Backend Responses - Simplified', () => {
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

  describe('Draft List Normalization', () => {
    it('should properly consume normalized drafts list', async () => {
      const mockDraftsResponse = {
        ok: true,
        data: [
          {
            id: 'draft-1',
            title: 'Introduction to Counting',
            content: '# Introduction to Counting\n\nThis lesson teaches basic counting skills.',
            metadata: { gradeLevel: 'Grade 1',
              strand_code: 'Connect',
              session_id: 'session-123'
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
              strand_code: 'Analyze'
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

      const { result } = renderHook(() => {
        const { useDrafts } = require('../../hooks/useDrafts')
        return useDrafts()
      }, { wrapper })

      await waitFor(() => {
        expect(result.current.isLoadingDrafts).toBe(false)
        expect(result.current.drafts).toHaveLength(2)
      })

      const drafts = result.current.drafts

      // Verify first draft structure
      const draft1 = drafts[0]
      expect(draft1.id).toBe('draft-1')
      expect(draft1.title).toBe('Introduction to Counting')
      expect(draft1.grade).toBe('Grade 1') // camelCase field
      expect(draft1.strand).toBe('Connect') // camelCase field
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

      // Verify presentation status structure
      expect(draft1.presentationStatus.has_presentation).toBe(true)
      expect(draft1.presentationStatus.status).toBe('completed')

      // Verify second draft structure
      const draft2 = drafts[1]
      expect(draft2.grade).toBe('Grade 4')
      expect(draft2.strand).toBe('Analyze')
      expect(Array.isArray(draft2.selectedStandards)).toBe(true)
      expect(draft2.selectedStandards).toHaveLength(3)
      expect(Array.isArray(draft2.selectedObjectives)).toBe(true)
      expect(draft2.selectedObjectives).toHaveLength(3)

      // Verify the API was called correctly
      expect(mockApi.getDrafts).toHaveBeenCalledTimes(1)
      expect(mockApi.getDrafts).toHaveBeenCalledWith()
    })

    it('should handle drafts with missing normalized fields gracefully', async () => {
      const mockDraftsResponse = {
        ok: true,
        data: [
          {
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
          }
        ],
      }

      mockApi.getDrafts.mockResolvedValue(mockDraftsResponse)

      const { result } = renderHook(() => {
        const { useDrafts } = require('../../hooks/useDrafts')
        return useDrafts()
      }, { wrapper })

      await waitFor(() => {
        expect(result.current.drafts).toHaveLength(1)
      })

      const draft = result.current.drafts[0]

      // Verify null fields are handled gracefully
      expect(draft.grade).toBeNull()
      expect(draft.strand).toBeNull()
      expect(draft.standard).toBeNull()
      expect(draft.selectedStandards).toBeNull()
      expect(draft.selectedObjectives).toBeNull()
      expect(draft.presentationStatus).toBeNull()

      // Verify essential fields are still present
      expect(draft.id).toBe('draft-minimal')
      expect(draft.title).toBe('Minimal Draft')
      expect(draft.content).toBe('# Minimal Draft\n\nBasic content.')
      expect(draft.metadata).toEqual({})
    })
  })

  describe('Draft Creation with Normalized Response', () => {
    it('should create draft and consume normalized response', async () => {
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

      const { result } = renderHook(() => {
        const { useDrafts } = require('../../hooks/useDrafts')
        return useDrafts()
      }, { wrapper })

      let createdDraft: any = null
      await act(async () => {
        createdDraft = await result.current.createDraft(
          'session-123',
          'New Lesson Draft',
          '# New Lesson\n\nContent for the new lesson.',
          { gradeLevel: 'Grade 3',
            strand_code: 'Evaluate',
            selected_standards: ['3.OA.1', '3.OA.2'],
            selected_objectives: ['multiply within 100', 'solve word problems']
          }
        )
      })

      // Verify the created draft has normalized structure
      expect(createdDraft.id).toBe('new-draft')
      expect(createdDraft.grade).toBe('Grade 3') // camelCase field
      expect(createdDraft.strand).toBe('Evaluate') // camelCase field
      expect(createdDraft.standard).toBe('3.OA.1')

      // Verify array fields are properly normalized
      expect(Array.isArray(createdDraft.selectedStandards)).toBe(true)
      expect(createdDraft.selectedStandards).toEqual(['3.OA.1', '3.OA.2'])
      expect(Array.isArray(createdDraft.selectedObjectives)).toBe(true)
      expect(createdDraft.selectedObjectives).toEqual([
        'multiply within 100',
        'solve word problems'
      ])

      // Verify API was called with correct parameters
      expect(mockApi.createDraft).toHaveBeenCalledTimes(1)
      expect(mockApi.createDraft).toHaveBeenCalledWith(
        'session-123',
        'New Lesson Draft',
        '# New Lesson\n\nContent for the new lesson.',
        { gradeLevel: 'Grade 3',
          strand_code: 'Evaluate',
          selected_standards: ['3.OA.1', '3.OA.2'],
          selected_objectives: ['multiply within 100', 'solve word problems']
        }
      )
    })
  })

  describe('Data Structure Verification', () => {
    it('should verify that normalized draft data matches expected frontend contract', () => {
      // Test data that represents what the backend should return
      const normalizedDraftData = {
        id: 'test-draft',
        title: 'Geometry Basics',
        content: '# Geometry Basics\n\nIntroduction to shapes and spatial reasoning.',
        metadata: { gradeLevel: 'Grade 2',
          strand_code: 'Create',
          session_id: 'session-456'
        },
        grade: 'Grade 2',
        strand: 'Create',
        standard: '2.G.1',
        selectedStandards: ['2.G.1', '2.G.2'],
        selectedObjectives: ['identify shapes', 'describe relationships'],
        createdAt: '2025-11-16T14:00:00Z',
        updatedAt: '2025-11-16T14:20:00Z',
        presentationStatus: {
          has_presentation: true,
          status: 'in_progress'
        }
      }

      // Verify the data structure matches what frontend expects
      expect(normalizedDraftData).toHaveProperty('id', 'test-draft')
      expect(normalizedDraftData).toHaveProperty('title', 'Geometry Basics')
      expect(normalizedDraftData).toHaveProperty('grade', 'Grade 2') // camelCase
      expect(normalizedDraftData).toHaveProperty('strand', 'Create') // camelCase
      expect(normalizedDraftData).toHaveProperty('standard', '2.G.1')
      expect(normalizedDraftData).toHaveProperty('selectedStandards')
      expect(normalizedDraftData).toHaveProperty('selectedObjectives')
      expect(normalizedDraftData).toHaveProperty('createdAt')
      expect(normalizedDraftData).toHaveProperty('updatedAt')
      expect(normalizedDraftData).toHaveProperty('presentationStatus')

      // Verify array structures
      expect(Array.isArray(normalizedDraftData.selectedStandards)).toBe(true)
      expect(Array.isArray(normalizedDraftData.selectedObjectives)).toBe(true)

      // Verify standards array
      expect(normalizedDraftData.selectedStandards).toEqual(['2.G.1', '2.G.2'])

      // Verify objectives array
      expect(normalizedDraftData.selectedObjectives).toEqual(['identify shapes', 'describe relationships'])

      // Verify presentation status structure
      expect(normalizedDraftData.presentationStatus.has_presentation).toBe(true)
      expect(normalizedDraftData.presentationStatus.status).toBe('in_progress')

      // Verify metadata structure
      expect(normalizedDraftData.metadata.gradeLevel).toBe('Grade 2')
      expect(normalizedDraftData.metadata.strandCode).toBe('Create')
      expect(normalizedDraftData.metadata.session_id).toBe('session-456')

      // Verify date format (ISO string)
      expect(normalizedDraftData.createdAt).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/)
      expect(normalizedDraftData.updatedAt).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/)
    })
  })
})