/**
 * IndexedDB utilities for LessonEditor auto-save functionality
 * Provides browser-based storage recovery for unsaved lesson content
 */

interface LessonEditorStorageItem {
  id: string;
  content: string;
  timestamp: string;
}

class LessonEditorStorage {
  private readonly DB_NAME = 'LessonEditorDB';
  private readonly DB_VERSION = 1;
  private readonly STORE_NAME = 'autosave';

  /**
   * Save content to IndexedDB with timestamp
   */
  async saveContent(id: string, content: string): Promise<void> {
    try {
      if (!this.isIndexedDBAvailable()) {
        console.warn('IndexedDB not available, skipping auto-save storage');
        return;
      }

      const db = await this.openDB();
      const transaction = db.transaction([this.STORE_NAME], 'readwrite');
      const store = transaction.objectStore(this.STORE_NAME);
      
      const item: LessonEditorStorageItem = {
        id,
        content,
        timestamp: new Date().toISOString(),
      };

      await store.put(item);
      
      return new Promise((resolve, reject) => {
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
      });
    } catch (error) {
      console.error('Failed to save to IndexedDB:', error);
      throw error;
    }
  }

  /**
   * Load content from IndexedDB by ID
   */
  async loadContent(id: string): Promise<string | null> {
    try {
      if (!this.isIndexedDBAvailable()) {
        return null;
      }

      const db = await this.openDB();
      const transaction = db.transaction([this.STORE_NAME], 'readonly');
      const store = transaction.objectStore(this.STORE_NAME);
      
      return new Promise((resolve) => {
        const request = store.get(id);
        request.onsuccess = () => {
          const result = request.result as LessonEditorStorageItem | undefined;
          resolve(result ? result.content : null);
        };
        request.onerror = () => {
          console.error('Failed to load from IndexedDB:', request.error);
          resolve(null);
        };
      });
    } catch (error) {
      console.error('Failed to load from IndexedDB:', error);
      return null;
    }
  }

  /**
   * Get all saved items from IndexedDB
   */
  async getAllSavedContent(): Promise<LessonEditorStorageItem[]> {
    try {
      if (!this.isIndexedDBAvailable()) {
        return [];
      }

      const db = await this.openDB();
      const transaction = db.transaction([this.STORE_NAME], 'readonly');
      const store = transaction.objectStore(this.STORE_NAME);
      
      return new Promise((resolve) => {
        const request = store.getAll();
        request.onsuccess = () => {
          resolve(request.result as LessonEditorStorageItem[]);
        };
        request.onerror = () => {
          console.error('Failed to get all from IndexedDB:', request.error);
          resolve([]);
        };
      });
    } catch (error) {
      console.error('Failed to get all from IndexedDB:', error);
      return [];
    }
  }

  /**
   * Delete content from IndexedDB by ID
   */
  async deleteContent(id: string): Promise<void> {
    try {
      if (!this.isIndexedDBAvailable()) {
        return;
      }

      const db = await this.openDB();
      const transaction = db.transaction([this.STORE_NAME], 'readwrite');
      const store = transaction.objectStore(this.STORE_NAME);
      
      await store.delete(id);
      
      return new Promise((resolve, reject) => {
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
      });
    } catch (error) {
      console.error('Failed to delete from IndexedDB:', error);
      throw error;
    }
  }

  /**
   * Clear all content from IndexedDB
   */
  async clearAllContent(): Promise<void> {
    try {
      if (!this.isIndexedDBAvailable()) {
        return;
      }

      const db = await this.openDB();
      const transaction = db.transaction([this.STORE_NAME], 'readwrite');
      const store = transaction.objectStore(this.STORE_NAME);
      
      await store.clear();
      
      return new Promise((resolve, reject) => {
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
      });
    } catch (error) {
      console.error('Failed to clear IndexedDB:', error);
      throw error;
    }
  }

  /**
   * Check if IndexedDB is available in the browser
   */
  private isIndexedDBAvailable(): boolean {
    return 'indexedDB' in window;
  }

  /**
   * Open IndexedDB database and create object store if needed
   */
  private openDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);
      
      request.onerror = () => {
        reject(request.error);
      };

      request.onsuccess = () => {
        resolve(request.result);
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        
        if (!db.objectStoreNames.contains(this.STORE_NAME)) {
          const objectStore = db.createObjectStore(this.STORE_NAME, { keyPath: 'id' });
          objectStore.createIndex('timestamp', 'timestamp', { unique: false });
        }
      };
    });
  }

  /**
   * Format timestamp for display
   */
  formatTimestamp(timestamp: string): string {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / (1000 * 60));
      
      if (diffMins < 1) {
        return 'Just now';
      } else if (diffMins < 60) {
        return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
      } else if (diffMins < 1440) { // 24 hours
        const diffHours = Math.floor(diffMins / 60);
        return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
      } else {
        return date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: diffMs > (365 * 24 * 60 * 60 * 1000) ? 'numeric' : undefined,
          hour: '2-digit',
          minute: '2-digit',
        });
      }
    } catch (error) {
      console.error('Failed to format timestamp:', error);
      return 'Unknown time';
    }
  }
}

// Export a singleton instance
export const lessonEditorStorage = new LessonEditorStorage();

// Export types for external use
export type { LessonEditorStorageItem };