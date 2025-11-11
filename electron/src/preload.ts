import { contextBridge, ipcRenderer } from 'electron';

// Define the API interface for type safety
export interface ElectronAPI {
  // App information
  getVersion: () => Promise<string>;
  getPlatform: () => Promise<string>;
  
  // Backend management
  getBackendStatus: () => Promise<{ isRunning: boolean; port?: number; pid?: number; error?: string }>;
  restartBackend: () => Promise<number>;
  
  // File dialogs
  showSaveDialog: (options: Electron.SaveDialogOptions) => Promise<Electron.SaveDialogReturnValue>;
  showOpenDialog: (options: Electron.OpenDialogOptions) => Promise<Electron.OpenDialogReturnValue>;
  
  // App control
  quit: () => Promise<void>;
  
  // Update events
  onUpdateAvailable: (callback: (info: any) => void) => void;
  onUpdateDownloaded: (callback: (info: any) => void) => void;
  onUpdateError: (callback: (error: string) => void) => void;
  
  // Menu events
  onMenuNewLesson: (callback: () => void) => void;
  
  // Remove all listeners
  removeAllListeners: (channel: string) => void;
}

// Expose the API to the renderer process
const electronAPI: ElectronAPI = {
  getVersion: () => ipcRenderer.invoke('app:getVersion'),
  getPlatform: () => ipcRenderer.invoke('app:getPlatform'),
  
  getBackendStatus: () => ipcRenderer.invoke('backend:getStatus'),
  restartBackend: () => ipcRenderer.invoke('backend:restart'),
  
  showSaveDialog: (options) => ipcRenderer.invoke('dialog:showSaveDialog', options),
  showOpenDialog: (options) => ipcRenderer.invoke('dialog:showOpenDialog', options),
  
  quit: () => ipcRenderer.invoke('app:quit'),
  
  onUpdateAvailable: (callback) => ipcRenderer.on('update-available', (_, info) => callback(info)),
  onUpdateDownloaded: (callback) => ipcRenderer.on('update-downloaded', (_, info) => callback(info)),
  onUpdateError: (callback) => ipcRenderer.on('update-error', (_, error) => callback(error)),
  
  onMenuNewLesson: (callback) => ipcRenderer.on('menu-new-lesson', () => callback()),
  
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel),
};

// Expose the API to the global window object
contextBridge.exposeInMainWorld('electronAPI', electronAPI);

// Type declaration for the global window object
declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}