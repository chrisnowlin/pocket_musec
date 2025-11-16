import '@testing-library/jest-dom'
import { vi } from 'vitest'

declare const global: typeof globalThis;

// Mock IndexedDB for lessonEditorStorage
const indexedDB = {
  open: vi.fn(),
  deleteDatabase: vi.fn(),
}

Object.defineProperty(window, 'indexedDB', {
  value: indexedDB,
  writable: true,
})

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  warn: vi.fn(),
  error: vi.fn(),
}

// Mock window.alert and window.confirm
Object.defineProperty(window, 'alert', {
  value: vi.fn(),
  writable: true,
})

Object.defineProperty(window, 'confirm', {
  value: vi.fn(() => true),
  writable: true,
})
