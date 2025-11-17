import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'
import type {
  StandardRecord,
  SessionResponsePayload,
  ChatResponsePayload,
} from './types'
import type { DraftItem } from '../types/unified'

const DEFAULT_API_BASE = '/api'

export interface ApiSuccess<T> {
  ok: true
  data: T
  status: number
}

export interface ApiFailure {
  ok: false
  status: number | null
  message: string
  details?: unknown
}

type ApiResult<T> = ApiSuccess<T> | ApiFailure

export interface ListStandardsParams {
  grade_level?: string
  strand_code?: string
  limit?: number
}

export interface SessionCreatePayload {
  grade_level?: string
  strand_code?: string
  standard_id?: string
  additional_context?: string
  lesson_duration?: string
  class_size?: number
  selected_objectives?: string[]
  additional_standards?: string[]
  selected_model?: string
}

export interface SessionUpdatePayload {
  grade_level?: string
  strand_code?: string
  standard_id?: string
  additional_context?: string
  lesson_duration?: string
  class_size?: number
  selected_objectives?: string[]
  additional_standards?: string[]
  selected_model?: string
}

export interface ChatMessagePayload {
  message: string
  lesson_duration?: string
  class_size?: string
}

export interface DashboardDraftSection {
  total: number
  items: DraftItem[]
  latest?: DraftItem | null
}

export interface DashboardStats {
  lessonsCreated: number
  activeDrafts: number
}

export interface WorkspaceDashboardPayload {
  generatedAt: string
  includes: string[]
  sessions?: SessionResponsePayload[]
  drafts?: DashboardDraftSection
  presentations?: Record<string, any>[]
  stats?: DashboardStats
}

export const API_BASE_URL = (window as any).API_BASE_URL || (import.meta.env?.VITE_API_BASE_URL as string) || DEFAULT_API_BASE

const createApiClient = (): AxiosInstance => {
  return axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true,
  })
}

const client = createApiClient()

const handleRequest = async <T>(
  config: AxiosRequestConfig
): Promise<ApiResult<T>> => {
  try {
    const response = await client.request<T>(config)
    return {
      ok: true,
      data: response.data,
      status: response.status,
    }
  } catch (error) {
    const axiosError = error as AxiosError<T>
    const status = axiosError.response?.status ?? null
    const message =
      (axiosError.response?.data as any)?.detail || axiosError.message || 'Request failed'

    return {
      ok: false,
      status,
      message,
      details: axiosError.response?.data,
    }
  }
}

export const apiClient = {
  get: <T>(url: string, config?: AxiosRequestConfig) =>
    handleRequest<T>({ url, method: 'GET', ...config }),
  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    handleRequest<T>({ url, method: 'POST', data, ...config }),
  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    handleRequest<T>({ url, method: 'PUT', data, ...config }),
  patch: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    handleRequest<T>({ url, method: 'PATCH', data, ...config }),
  delete: <T>(url: string, config?: AxiosRequestConfig) =>
    handleRequest<T>({ url, method: 'DELETE', ...config }),
}


const api = {
  health: () => apiClient.get('/health'),
  listStandards: (params?: ListStandardsParams) =>
    apiClient.get<StandardRecord[]>('/standards', { params }),
  createSession: (payload: SessionCreatePayload) =>
    apiClient.post<SessionResponsePayload>('/sessions', payload),
  listSessions: () => apiClient.get<SessionResponsePayload[]>('/sessions'),
  updateSession: (sessionId: string, payload: SessionUpdatePayload) =>
    apiClient.put<SessionResponsePayload>(`/sessions/${sessionId}`, payload),
  sendChatMessage: (sessionId: string, payload: ChatMessagePayload) =>
    apiClient.post<ChatResponsePayload>(`/sessions/${sessionId}/messages`, payload),
  getSession: (sessionId: string) => apiClient.get<SessionResponsePayload>(`/sessions/${sessionId}`),
  deleteSession: (sessionId: string) => apiClient.delete<{ message: string }>(`/sessions/${sessionId}`),
  deleteAllSessions: () => apiClient.delete<{ message: string; count: number }>('/sessions'),
  generateLesson: (request: unknown) => apiClient.post('/lessons/generate', request),
  getLesson: (sessionId: string) => apiClient.get(`/lessons/${sessionId}`),
  getLessonBySession: (sessionId: string) =>
    apiClient.get<DraftItem[]>('/drafts', { params: { session_id: sessionId } }),
  getImages: (params?: {
    category?: string;
    education_level?: string;
    difficulty_level?: string;
  }) => apiClient.get('/images', { params }),
  getImageStorageInfo: () => apiClient.get('/images/storage/info'),
  uploadImages: (formData: FormData, onUploadProgress?: (progress: number) => void) =>
    apiClient.post('/images/upload/batch', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (event) => {
        if (!onUploadProgress || !event.total) return
        const progress = Math.round((event.loaded * 100) / event.total)
        onUploadProgress(progress)
      },
    }),
  deleteImage: (imageId: string) => apiClient.delete(`/images/${imageId}`),
  getProcessingModes: () => apiClient.get('/settings/processing-modes'),
  getLocalModelStatus: () => apiClient.get('/settings/models/local/status'),
  updateProcessingMode: (mode: string) =>
    apiClient.put('/settings/processing-mode', { mode }),
  downloadLocalModel: () => apiClient.post('/settings/models/local/download'),
  streamChatMessage: async (sessionId: string, payload: ChatMessagePayload, retryCount: number = 0): Promise<Response> => {
    const maxRetries = 2;
    
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        
        // Network errors or server errors might be retryable
        if (retryCount < maxRetries && (response.status >= 500 || response.status === 0)) {
          console.warn(`Streaming request failed (attempt ${retryCount + 1}/${maxRetries + 1}), retrying...`);
          
          // Exponential backoff with jitter
          const baseDelay = 1000;
          const jitter = Math.random() * 0.3 * baseDelay;
          const delay = baseDelay * Math.pow(2, retryCount) + jitter;
          
          await new Promise(resolve => setTimeout(resolve, delay));
          return api.streamChatMessage(sessionId, payload, retryCount + 1);
        }
        
        throw new Error(`HTTP ${response.status}: ${errorText || 'Unknown error'}`);
      }

      if (!response.body) {
        throw new Error('Response body is not available');
      }

      return response;
    } catch (error: any) {
      // Handle network errors with retry
      if (retryCount < maxRetries && error.name === 'TypeError' && error.message.includes('fetch')) {
        console.warn(`Network error in streaming (attempt ${retryCount + 1}/${maxRetries + 1}), retrying...`);
        
        const baseDelay = 1000;
        const jitter = Math.random() * 0.3 * baseDelay;
        const delay = baseDelay * Math.pow(2, retryCount) + jitter;
        
        await new Promise(resolve => setTimeout(resolve, delay));
        return api.streamChatMessage(sessionId, payload, retryCount + 1);
      }
      
      throw error;
    }
  },
  // Draft operations
  getDrafts: () => apiClient.get<DraftItem[]>('/drafts'),
  getDraft: (draftId: string) => apiClient.get<DraftItem>(`/drafts/${draftId}`),
  deleteDraft: (draftId: string) => apiClient.delete(`/drafts/${draftId}`),
  createDraft: (payload: { session_id: string; title: string; content: string; metadata?: Record<string, unknown> }) =>
    apiClient.post<DraftItem>('/drafts', payload),
  updateDraft: (draftId: string, payload: { title?: string; content?: string; metadata?: Record<string, unknown> }) =>
    apiClient.put<DraftItem>(`/drafts/${draftId}`, payload),

  // Lesson operations (permanent lessons)
  getLessons: () => apiClient.get<DraftItem[]>('/lessons', { params: { is_draft: false } }),
  getPermanentLesson: (lessonId: string) => apiClient.get<DraftItem>(`/lessons/${lessonId}`),
  promoteLesson: (lessonId: string) => apiClient.post<DraftItem>(`/lessons/${lessonId}/promote`),
  demoteLesson: (lessonId: string) => apiClient.post<DraftItem>(`/lessons/${lessonId}/demote`),
  deleteLesson: (lessonId: string) => apiClient.delete(`/lessons/${lessonId}`),

  // Presentation operations
  getPresentations: (lessonId?: string) => {
    const url = lessonId ? `/presentations?lesson_id=${lessonId}` : '/presentations';
    return apiClient.get(url);
  },
  getPresentation: (presentationId: string) => apiClient.get(`/presentations/${presentationId}`),
  generatePresentation: (payload: { lessonId: string; options?: any }) =>
    apiClient.post('/presentations/generate', payload),
  getPresentationStatus: (presentationId: string) => 
    apiClient.get(`/presentations/${presentationId}/status`),
  deletePresentation: (presentationId: string) => 
    apiClient.delete(`/presentations/${presentationId}`),
  exportPresentation: (presentationId: string, format: 'json' | 'markdown') =>
    apiClient.post(`/presentations/${presentationId}/export`, { format }),
  refreshPresentation: (presentationId: string) =>
    apiClient.post(`/presentations/${presentationId}/refresh`),
  getWorkspaceDashboard: (sections?: string[]) => {
    const params = sections && sections.length > 0 ? { include: sections.join(',') } : undefined;
    return apiClient.get<WorkspaceDashboardPayload>('/workspace/dashboard', { params });
  },
}

export default api
