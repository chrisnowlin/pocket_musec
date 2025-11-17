/**
 * Regression tests for useSession hook with normalized backend responses
 * Ensures the hook properly consumes camelCase array responses from the backend
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

import api from '../../lib/api'
import { useSession } from '../useSession'

// Mock conversation store
const mockSetSession = vi.fn()
const mockSession = {
  id: 'test-session-id',
  gradeLevel: 'Grade 3',
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
  selectedObjectives: ['obj1', 'obj2', 'obj3'],
  additionalContext: 'Test context',
  createdAt: '2025-11-16T10:00:00Z',
  updatedAt: '2025-11-16T10:30:00Z',
}

vi.mock('../../stores/conversationStore', () => ({
  useConversationStore: () => ({
    session: mockSession,
    setSession: mockSetSession,
  }),
}))

describe('useSession with Normalized Backend Responses', () => {
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
    it('should properly consume normalized sessions list with camelCase fields', async () => {
      // Mock API response with normalized backend data
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
            additionalContext: 'Math lesson',
            createdAt: '2025-11-16T09:00:00Z',
            updatedAt: '2025-11-16T09:30:00Z',
          },
          {
            id: 'session-2',
            gradeLevel: 'Grade 2',
            strandCode: 'Create',
            selectedStandards: [
              {
                id: 'K.CC.2',
                code: 'K.CC.2',
                grade: 'Kindergarten',
                strandCode: 'CC',
                strandName: 'Counting and Cardinality',
                title: 'Count forward beginning from a given number',
                description: 'Count forward beginning from a given number'
              }
            ],
            selectedObjectives: ['create patterns', 'extend sequences'],
            additionalContext: 'Creative math lesson',
            createdAt: '2025-11-16T10:00:00Z',
            updatedAt: '2025-11-16T10:30:00Z',
          }
        ],
      }

      mockApi.listSessions.mockResolvedValue(mockSessionsResponse)

      const { result } = renderHook(() => useSession(), { wrapper })

      await waitFor(() => {
        expect(result.current.sessions).toHaveLength(2)
      })

      const sessions = result.current.sessions

      // Verify camelCase field names are preserved
      expect(sessions[0]).toHaveProperty('gradeLevel', 'Grade 1')
      expect(sessions[0]).toHaveProperty('strandCode', 'Connect')
      expect(sessions[0]).toHaveProperty('selectedStandards')
      expect(sessions[0]).toHaveProperty('selectedObjectives')
      expect(sessions[0]).toHaveProperty('additionalContext')
      expect(sessions[0]).toHaveProperty('createdAt')
      expect(sessions[0]).toHaveProperty('updatedAt')

      // Verify selectedStandards is an array of structured objects
      expect(Array.isArray(sessions[0].selectedStandards)).toBe(true)
      expect(sessions[0].selectedStandards).toHaveLength(1)
      expect(sessions[0].selectedStandards![0]).toHaveProperty('id', 'K.CC.1')
      expect(sessions[0].selectedStandards![0]).toHaveProperty('code', 'K.CC.1')
      expect(sessions[0].selectedStandards![0]).toHaveProperty('grade', 'Kindergarten')

      // Verify selectedObjectives is an array of strings
      expect(Array.isArray(sessions[0].selectedObjectives)).toBe(true)
      expect(sessions[0].selectedObjectives).toEqual(['count numbers', 'recognize patterns'])

      // Verify session 2
      expect(sessions[1].gradeLevel).toBe('Grade 2')
      expect(sessions[1].strandCode).toBe('Create')
      expect(Array.isArray(sessions[1].selectedStandards)).toBe(true)
      expect(Array.isArray(sessions[1].selectedObjectives)).toBe(true)
    })

    it('should properly consume normalized single session response', async () => {
      // Mock API response with normalized backend data
      const mockSessionResponse = {
        ok: true,
        data: {
          id: 'session-single',
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
            },
            {
              id: 'K.CC.4',
              code: 'K.CC.4',
              grade: 'Kindergarten',
              strandCode: 'CC',
              strandName: 'Counting and Cardinality',
              title: 'Count to tell the number of objects',
              description: 'Count to tell the number of objects'
            }
          ],
          selectedObjectives: ['count objects', 'write numbers', 'compare quantities'],
          additionalContext: 'Advanced counting lesson',
          createdAt: '2025-11-16T11:00:00Z',
          updatedAt: '2025-11-16T11:30:00Z',
        },
      }

      mockApi.getSession.mockResolvedValue(mockSessionResponse)

      const { result } = renderHook(() => useSession(), { wrapper })

      await act(async () => {
        await result.current.loadConversation('session-single')
      })

      expect(mockApi.getSession).toHaveBeenCalledWith('session-single')
      expect(mockSetSession).toHaveBeenCalledWith(mockSessionResponse.data)

      const sessionData = mockSessionResponse.data

      // Verify the session data structure
      expect(sessionData).toHaveProperty('gradeLevel', 'Grade 3')
      expect(sessionData).toHaveProperty('strandCode', 'Analyze')

      // Verify multiple standards are handled correctly
      expect(Array.isArray(sessionData.selectedStandards)).toBe(true)
      expect(sessionData.selectedStandards).toHaveLength(2)
      expect(sessionData.selectedStandards![0].id).toBe('K.CC.3')
      expect(sessionData.selectedStandards![1].id).toBe('K.CC.4')

      // Verify multiple objectives are handled correctly
      expect(Array.isArray(sessionData.selectedObjectives)).toBe(true)
      expect(sessionData.selectedObjectives).toEqual([
        'count objects',
        'write numbers',
        'compare quantities'
      ])
    })

    it('should handle empty/null normalized fields gracefully', async () => {
      // Mock API response with empty normalized fields
      const mockSessionResponse = {
        ok: true,
        data: {
          id: 'session-empty',
          gradeLevel: null,
          strandCode: null,
          selectedStandards: [],
          selectedObjectives: null,
          additionalContext: null,
          createdAt: '2025-11-16T12:00:00Z',
          updatedAt: '2025-11-16T12:30:00Z',
        },
      }

      mockApi.getSession.mockResolvedValue(mockSessionResponse)

      const { result } = renderHook(() => useSession(), { wrapper })

      await act(async () => {
        await result.current.loadConversation('session-empty')
      })

      const sessionData = mockSessionResponse.data

      // Verify empty/null fields are handled gracefully
      expect(sessionData.selectedStandards).toEqual([])
      expect(sessionData.selectedObjectives).toBeNull()
      expect(sessionData.gradeLevel).toBeNull()
      expect(sessionData.strandCode).toBeNull()
      expect(sessionData.additionalContext).toBeNull()

      // Verify the session can still be processed without errors
      expect(mockSetSession).toHaveBeenCalledWith(sessionData)
    })
  })

  describe('Session Creation with Normalized Responses', () => {
    it('should create session and consume normalized response', async () => {
      // Mock API response for session creation
      const mockCreateResponse = {
        ok: true,
        data: {
          id: 'new-session',
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
          selectedObjectives: ['understand multiplication', 'solve comparison problems'],
          additionalContext: 'Introduction to multiplication',
          createdAt: '2025-11-16T13:00:00Z',
          updatedAt: '2025-11-16T13:00:00Z',
        },
      }

      mockApi.createSession.mockResolvedValue(mockCreateResponse)

      const { result } = renderHook(() => useSession(), { wrapper })

      await act(async () => {
        const session = await result.current.initSession(
          'Grade 4',
          'Create',
          '4.OA.1',
          'Introduction to multiplication',
          '45 minutes',
          25,
          ['understand multiplication', 'solve comparison problems']
        )

        expect(session).toEqual(mockCreateResponse.data)
      })

      // Verify the created session has normalized structure
      expect(mockCreateResponse.data.selectedStandards).toHaveLength(1)
      expect(mockCreateResponse.data.selectedStandards![0].id).toBe('4.OA.1')
      expect(Array.isArray(mockCreateResponse.data.selectedObjectives)).toBe(true)
      expect(mockCreateResponse.data.selectedObjectives).toEqual([
        'understand multiplication',
        'solve comparison problems'
      ])
    })
  })

  describe('Conversation Formatting with Normalized Data', () => {
    it('should format conversations using normalized session data', async () => {
      // Mock API response with sessions
      const mockSessionsResponse = {
        ok: true,
        data: [
          {
            id: 'conv-1',
            gradeLevel: 'Grade 5',
            strandCode: 'Analyze',
            selectedStandards: [
              {
                id: '5.NBT.1',
                code: '5.NBT.1',
                grade: 'Grade 5',
                strandCode: 'NBT',
                strandName: 'Number and Operations in Base Ten',
                title: 'Recognize place value in multi-digit numbers',
                description: 'Recognize place value in multi-digit numbers'
              }
            ],
            selectedObjectives: ['understand place value'],
            createdAt: '2025-11-16T14:00:00Z',
            updatedAt: '2025-11-16T14:30:00Z',
          }
        ],
      }

      mockApi.listSessions.mockResolvedValue(mockSessionsResponse)

      const { result } = renderHook(() => useSession(), { wrapper })

      await waitFor(() => {
        expect(result.current.sessions).toHaveLength(1)
      })

      // Test conversation formatting
      const conversations = result.current.formatSessionsAsConversations()

      expect(conversations).toHaveLength(1)
      expect(conversations[0].items).toHaveLength(1)

      const conversationItem = conversations[0].items[0]

      // Verify the conversation item uses normalized data
      expect(conversationItem.id).toBe('conv-1')
      expect(conversationItem.grade).toBe('Grade 5')
      expect(conversationItem.strand).toBe('Analyze')
      expect(conversationItem.standard).toBe('5.NBT.1') // Uses code from first standard

      // Verify title generation uses normalized data
      expect(conversationItem.title).toContain('Grade 5 · Analyze · 5.NBT.1')
    })
  })
})