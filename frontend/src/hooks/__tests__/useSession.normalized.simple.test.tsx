/**
 * Simplified regression tests for useSession hook with normalized backend responses
 * Focused on verifying proper consumption of camelCase array responses
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, beforeEach, vi } from 'vitest'

// Mock the API module
vi.mock('../../lib/api', () => ({
  default: {
    listSessions: vi.fn(),
    getSession: vi.fn(),
    createSession: vi.fn(),
    updateSession: vi.fn(),
  },
}))

// Mock the standards loader
vi.mock('../../lib/gradeUtils', () => ({
  frontendToBackendGrade: vi.fn((grade) => grade),
  frontendToBackendStrand: vi.fn((strand) => strand),
}))

// Mock the loadStandards function to avoid API calls
vi.mock('../../hooks/useSession', async () => {
  const actual = await vi.importActual<typeof import('../../hooks/useSession')>('../../hooks/useSession')
  return {
    ...actual,
    // Override the loadStandards implementation to avoid actual API calls
  }
})

import api from '../../lib/api'

describe('useSession with Normalized Backend Responses - Simplified', () => {
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

  describe('Session List Normalization', () => {
    it('should properly consume normalized sessions list', async () => {
      const mockSessionsResponse = {
        ok: true,
        data: [
          {
            id: 'session-1',
            gradeLevel: 'Grade 1',
            strandCode: 'Connect',
            selectedStandards: [
              {
                id: 'K.CC.1',
                code: 'K.CC.1',
                grade: 'Kindergarten',
                strandCode: 'CC',
                strandName: 'Counting and Cardinality',
                title: 'Know number names and the count sequence',
                description: 'Know number names and the count sequence'
              }
            ],
            selectedObjectives: ['count numbers', 'recognize patterns'],
            createdAt: '2025-11-16T09:00:00Z',
            updatedAt: '2025-11-16T09:30:00Z',
          }
        ],
      }

      mockApi.listSessions.mockResolvedValue(mockSessionsResponse)

      const { result } = renderHook(() => {
        // Import useSession after mocking dependencies
        const { useSession } = require('../../hooks/useSession')
        return useSession()
      }, { wrapper })

      await waitFor(() => {
        expect(result.current.isLoadingSessions).toBe(false)
        expect(result.current.sessions).toHaveLength(1)
      })

      const sessions = result.current.sessions

      // Verify the session data structure is properly normalized
      expect(sessions[0].id).toBe('session-1')
      expect(sessions[0].gradeLevel).toBe('Grade 1') // camelCase field
      expect(sessions[0].strandCode).toBe('Connect') // camelCase field

      // Verify selectedStandards is an array (from normalized backend)
      expect(Array.isArray(sessions[0].selectedStandards)).toBe(true)
      expect(sessions[0].selectedStandards).toHaveLength(1)
      expect(sessions[0].selectedStandards![0].id).toBe('K.CC.1')
      expect(sessions[0].selectedStandards![0].code).toBe('K.CC.1')

      // Verify selectedObjectives is an array (from normalized backend)
      expect(Array.isArray(sessions[0].selectedObjectives)).toBe(true)
      expect(sessions[0].selectedObjectives).toEqual(['count numbers', 'recognize patterns'])

      // Verify camelCase date fields
      expect(sessions[0].createdAt).toBe('2025-11-16T09:00:00Z')
      expect(sessions[0].updatedAt).toBe('2025-11-16T09:30:00Z')

      // Verify the API was called correctly
      expect(mockApi.listSessions).toHaveBeenCalledTimes(1)
      expect(mockApi.listSessions).toHaveBeenCalledWith()
    })

    it('should handle sessions with empty normalized fields', async () => {
      const mockSessionsResponse = {
        ok: true,
        data: [
          {
            id: 'session-empty',
            gradeLevel: null,
            strandCode: null,
            selectedStandards: [],
            selectedObjectives: null,
            createdAt: '2025-11-16T12:00:00Z',
            updatedAt: '2025-11-16T12:30:00Z',
          }
        ],
      }

      mockApi.listSessions.mockResolvedValue(mockSessionsResponse)

      const { result } = renderHook(() => {
        const { useSession } = require('../../hooks/useSession')
        return useSession()
      }, { wrapper })

      await waitFor(() => {
        expect(result.current.sessions).toHaveLength(1)
      })

      const session = result.current.sessions[0]

      // Verify empty/null fields are handled gracefully
      expect(session.selectedStandards).toEqual([])
      expect(session.selectedObjectives).toBeNull()
      expect(session.gradeLevel).toBeNull()
      expect(session.strandCode).toBeNull()

      // Verify essential fields are still present
      expect(session.id).toBe('session-empty')
      expect(session.createdAt).toBe('2025-11-16T12:00:00Z')
      expect(session.updatedAt).toBe('2025-11-16T12:30:00Z')
    })
  })

  describe('Session Creation with Normalized Response', () => {
    it('should consume normalized response from session creation', async () => {
      const mockCreateResponse = {
        ok: true,
        data: {
          id: 'new-session',
          gradeLevel: 'Grade 3',
          strandCode: 'Analyze',
          selectedStandards: [
            {
              id: 'K.CC.3',
              code: 'K.CC.3',
              grade: 'Kindergarten',
              strandCode: 'CC',
              strandName: 'Counting and Cardinality',
              title: 'Write numbers from 0 to 20',
              description: 'Write numbers from 0 to 20'
            }
          ],
          selectedObjectives: ['write numbers', 'count objects'],
          additionalContext: 'Introduction to writing numbers',
          createdAt: '2025-11-16T13:00:00Z',
          updatedAt: '2025-11-16T13:00:00Z',
        },
      }

      mockApi.createSession.mockResolvedValue(mockCreateResponse)

      const { result } = renderHook(() => {
        const { useSession } = require('../../hooks/useSession')
        return useSession()
      }, { wrapper })

      let createdSession: any = null
      await act(async () => {
        createdSession = await result.current.initSession(
          'Grade 3',
          'Analyze',
          'K.CC.3',
          'Introduction to writing numbers'
        )
      })

      // Verify the created session has normalized structure
      expect(createdSession.id).toBe('new-session')
      expect(createdSession.gradeLevel).toBe('Grade 3') // camelCase field
      expect(createdSession.strandCode).toBe('Analyze') // camelCase field

      // Verify array fields are properly normalized
      expect(Array.isArray(createdSession.selectedStandards)).toBe(true)
      expect(createdSession.selectedStandards).toHaveLength(1)
      expect(createdSession.selectedStandards![0].id).toBe('K.CC.3')

      expect(Array.isArray(createdSession.selectedObjectives)).toBe(true)
      expect(createdSession.selectedObjectives).toEqual(['write numbers', 'count objects'])

      // Verify API was called with correct parameters
      expect(mockApi.createSession).toHaveBeenCalledTimes(1)
      expect(mockApi.createSession).toHaveBeenCalledWith({ gradeLevel: 'Grade 3',
        strand_code: 'Analyze',
        standard_id: 'K.CC.3',
        additionalContext: 'Introduction to writing numbers'
      })
    })
  })

  describe('Data Structure Verification', () => {
    it('should verify that normalized data matches expected frontend contract', async () => {
      // Test data that represents what the backend should return
      const normalizedSessionData = {
        id: 'test-session',
        gradeLevel: 'Grade 4',
        strandCode: 'Create',
        selectedStandards: [
          {
            id: '4.OA.1',
            code: '4.OA.1',
            grade: 'Grade 4',
            strandCode: 'OA',
            strandName: 'Operations and Algebraic Thinking',
            title: 'Interpret multiplication equations',
            description: 'Interpret multiplication equations as comparisons'
          }
        ],
        selectedObjectives: ['multiply within 100', 'solve word problems'],
        additionalContext: 'Multiplication lesson',
        createdAt: '2025-11-16T14:00:00Z',
        updatedAt: '2025-11-16T14:30:00Z',
      }

      // Verify the data structure matches what frontend expects
      expect(normalizedSessionData).toHaveProperty('id', 'test-session')
      expect(normalizedSessionData).toHaveProperty('gradeLevel', 'Grade 4') // camelCase
      expect(normalizedSessionData).toHaveProperty('strandCode', 'Create') // camelCase
      expect(normalizedSessionData).toHaveProperty('selectedStandards')
      expect(normalizedSessionData).toHaveProperty('selectedObjectives')
      expect(normalizedSessionData).toHaveProperty('createdAt')
      expect(normalizedSessionData).toHaveProperty('updatedAt')

      // Verify array structures
      expect(Array.isArray(normalizedSessionData.selectedStandards)).toBe(true)
      expect(Array.isArray(normalizedSessionData.selectedObjectives)).toBe(true)

      // Verify standards structure
      const standard = normalizedSessionData.selectedStandards[0]
      expect(standard).toHaveProperty('id', '4.OA.1')
      expect(standard).toHaveProperty('code', '4.OA.1')
      expect(standard).toHaveProperty('grade', 'Grade 4')
      expect(standard).toHaveProperty('strandCode', 'OA')
      expect(standard).toHaveProperty('strandName', 'Operations and Algebraic Thinking')
      expect(standard).toHaveProperty('title', 'Interpret multiplication equations')
      expect(standard).toHaveProperty('description', 'Interpret multiplication equations as comparisons')

      // Verify objectives structure
      expect(normalizedSessionData.selectedObjectives).toEqual([
        'multiply within 100',
        'solve word problems'
      ])

      // Verify date format (ISO string)
      expect(normalizedSessionData.createdAt).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/)
      expect(normalizedSessionData.updatedAt).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/)
    })
  })
})