import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'
import type {
  StandardRecord,
  SessionResponsePayload,
  ChatResponsePayload,
} from './types'

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
}

export interface SessionUpdatePayload {
  grade_level?: string
  strand_code?: string
  standard_id?: string
  additional_context?: string
}

export interface ChatMessagePayload {
  message: string
  lesson_duration?: string
  class_size?: string
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
  generateLesson: (request: unknown) => apiClient.post('/lessons/generate', request),
  getLesson: (sessionId: string) => apiClient.get(`/lessons/${sessionId}`),
  getImages: () => apiClient.get('/images'),
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
  streamChatMessage: (sessionId: string, payload: ChatMessagePayload) =>
    fetch(`${API_BASE_URL}/sessions/${sessionId}/messages/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(payload),
    }),
}

export default api
