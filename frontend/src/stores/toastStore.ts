import { create } from 'zustand';
import type { Toast, ToastType } from '../components/unified/Toast';

interface ToastStoreState {
  toasts: Toast[];
  showToast: (message: string, type?: ToastType, duration?: number) => string;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

export const useToastStore = create<ToastStoreState>((set, get) => ({
  toasts: [],
  showToast: (message, type = 'info', duration) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const toast: Toast = { id, message, type, duration };
    set((state) => ({ toasts: [...state.toasts, toast] }));
    return id;
  },
  removeToast: (id) => set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) })),
  clearToasts: () => set({ toasts: [] }),
}));

export const toastActions = {
  success: (message: string, duration?: number) => useToastStore.getState().showToast(message, 'success', duration),
  error: (message: string, duration?: number) => useToastStore.getState().showToast(message, 'error', duration),
  info: (message: string, duration?: number) => useToastStore.getState().showToast(message, 'info', duration),
  warning: (message: string, duration?: number) => useToastStore.getState().showToast(message, 'warning', duration),
};
