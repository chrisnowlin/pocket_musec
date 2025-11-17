/* Performance optimization and progressive loading service for presentation generation */

import React from 'react';

export interface PerformanceMetrics {
  startTime: number;
  endTime?: number;
  duration?: number;
  memoryUsage?: number;
  networkLatency?: number;
  renderTime?: number;
}

export interface ProgressiveLoadConfig {
  itemsPerPage: number;
  threshold: number; // Intersection observer threshold
  rootMargin: string;
  debounceMs: number;
  enablePreloading: boolean;
  enableCache: boolean;
}

export class PerformanceService {
  private metrics: Map<string, PerformanceMetrics> = new Map();
  private cache: Map<string, any> = new Map();
  private observers: Map<string, IntersectionObserver> = new Map();
  private defaultConfig: ProgressiveLoadConfig = {
    itemsPerPage: 5,
    threshold: 0.1,
    rootMargin: '50px',
    debounceMs: 100,
    enablePreloading: true,
    enableCache: true
  };

  // Performance monitoring
  startTiming(key: string): void {
    this.metrics.set(key, {
      startTime: performance.now(),
      memoryUsage: this.getMemoryUsage()
    });
  }

  endTiming(key: string): PerformanceMetrics | null {
    const metrics = this.metrics.get(key);
    if (!metrics) return null;

    const endTime = performance.now();
    const updatedMetrics = {
      ...metrics,
      endTime,
      duration: endTime - metrics.startTime,
      memoryUsage: this.getMemoryUsage()
    };

    this.metrics.set(key, updatedMetrics);
    return updatedMetrics;
  }

  getMetrics(key: string): PerformanceMetrics | null {
    return this.metrics.get(key) || null;
  }

  clearMetrics(key?: string): void {
    if (key) {
      this.metrics.delete(key);
    } else {
      this.metrics.clear();
    }
  }

  getMemoryUsage(): number {
    if ('memory' in performance) {
      return (performance as any).memory.usedJSHeapSize;
    }
    return 0;
  }

  // Network optimization
  async fetchWithRetry<T>(
    url: string,
    options: RequestInit = {},
    retries: number = 3,
    delay: number = 1000
  ): Promise<T> {
    const cacheKey = `${url}_${JSON.stringify(options)}`;

    // Check cache first
    if (this.defaultConfig.enableCache && this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }

    let lastError: Error;

    for (let i = 0; i <= retries; i++) {
      try {
        const startTime = performance.now();
        const response = await fetch(url, {
          ...options,
          headers: {
            'Accept': 'application/json',
            ...options.headers
          }
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        const endTime = performance.now();

        // Cache response
        if (this.defaultConfig.enableCache) {
          this.cache.set(cacheKey, data);
        }

        // Record metrics
        this.metrics.set(`fetch_${cacheKey}`, {
          startTime,
          endTime,
          duration: endTime - startTime,
          networkLatency: endTime - startTime
        });

        return data;
      } catch (error) {
        lastError = error as Error;
        if (i < retries) {
          await this.delay(delay * Math.pow(2, i)); // Exponential backoff
        }
      }
    }

    throw lastError!;
  }

  async fetchWithProgress<T>(
    url: string,
    options: RequestInit = {},
    onProgress?: (loaded: number, total: number) => void
  ): Promise<T> {
    const cacheKey = `${url}_progress`;

    if (this.defaultConfig.enableCache && this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const startTime = performance.now();

      xhr.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          onProgress(event.loaded, event.total);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const data = JSON.parse(xhr.responseText);
          const endTime = performance.now();

          if (this.defaultConfig.enableCache) {
            this.cache.set(cacheKey, data);
          }

          this.metrics.set(`fetch_progress_${cacheKey}`, {
            startTime,
            endTime,
            duration: endTime - startTime
          });

          resolve(data);
        } else {
          reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Network error'));
      });

      xhr.open(options.method || 'GET', url);

      // Set headers
      if (options.headers) {
        Object.entries(options.headers).forEach(([key, value]) => {
          xhr.setRequestHeader(key, value as string);
        });
      }

      xhr.send(options.body as XMLHttpRequestBodyInit);
    });
  }

  // Progressive loading utilities
  createIntersectionObserver(
    key: string,
    callback: (entries: IntersectionObserverEntry[]) => void,
    config: Partial<ProgressiveLoadConfig> = {}
  ): IntersectionObserver {
    // Clean up existing observer
    this.cleanupObserver(key);

    const finalConfig = { ...this.defaultConfig, ...config };
    const observer = new IntersectionObserver(callback, {
      threshold: finalConfig.threshold,
      rootMargin: finalConfig.rootMargin
    });

    this.observers.set(key, observer);
    return observer;
  }

  observeElement(key: string, element: Element): void {
    const observer = this.observers.get(key);
    if (observer && element) {
      observer.observe(element);
    }
  }

  unobserveElement(key: string, element: Element): void {
    const observer = this.observers.get(key);
    if (observer && element) {
      observer.unobserve(element);
    }
  }

  cleanupObserver(key: string): void {
    const observer = this.observers.get(key);
    if (observer) {
      observer.disconnect();
      this.observers.delete(key);
    }
  }

  cleanupAllObservers(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();
  }

  // Debounce utility
  debounce<T extends (...args: any[]) => void>(
    func: T,
    delay: number
  ): (...args: Parameters<T>) => void {
    let timeoutId: NodeJS.Timeout;
    return (...args: Parameters<T>) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => func(...args), delay);
    };
  }

  // Throttle utility
  throttle<T extends (...args: any[]) => void>(
    func: T,
    delay: number
  ): (...args: Parameters<T>) => void {
    let lastCall = 0;
    return (...args: Parameters<T>) => {
      const now = performance.now();
      if (now - lastCall >= delay) {
        lastCall = now;
        func(...args);
      }
    };
  }

  // Progressive loading for presentations
  async loadPresentationProgressively(
    presentationId: string,
    onProgress?: (progress: number, loaded: number, total: number) => void
  ): Promise<any> {
    this.startTiming(`load_presentation_${presentationId}`);

    try {
      // First, load metadata
      const metadata = await this.fetchWithRetry(`/api/presentations/${presentationId}?metadata=true`) as any;
      onProgress?.(10, 1, 10);

      // Load slides in batches
      const slides: any[] = [];
      const totalSlides = metadata.slide_count || 0;
      const batchSize = 5;

      for (let i = 0; i < totalSlides; i += batchSize) {
        const batch = await this.fetchWithRetry(
          `/api/presentations/${presentationId}/slides?start=${i}&limit=${batchSize}`
        ) as any[];
        slides.push(...batch);

        const progress = Math.min(100, 10 + (i + batchSize) / totalSlides * 80);
        onProgress?.(progress, i + batchSize, totalSlides);

        // Small delay to prevent overwhelming the network
        await this.delay(100);
      }

      // Load exports
      const exports = await this.fetchWithRetry(`/api/presentations/${presentationId}/exports`);
      onProgress?.(100, totalSlides, totalSlides);

      const metrics = this.endTiming(`load_presentation_${presentationId}`);
      console.log(`Loading metrics for ${presentationId}:`, metrics);

      return {
        ...(metadata as object),
        slides,
        exports
      };
    } catch (error) {
      this.endTiming(`load_presentation_${presentationId}`);
      throw error;
    }
  }

  // Optimized rendering utilities
  requestAnimationFrameThrottle<T extends (...args: any[]) => void>(func: T): T {
    let ticking = false;
    return ((...args: Parameters<T>) => {
      if (!ticking) {
        requestAnimationFrame(() => {
          func(...args);
          ticking = false;
        });
        ticking = true;
      }
    }) as T;
  }

  // Memory management
  cleanup(): void {
    this.cleanupAllObservers();
    this.cache.clear();
    this.metrics.clear();
  }

  // Utilities
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Performance monitoring
  getPerformanceReport(): {
    summary: {
      totalRequests: number;
      averageResponseTime: number;
      cacheHitRate: number;
      memoryUsage: number;
    };
    details: PerformanceMetrics[];
  } {
    const metricsArray = Array.from(this.metrics.values());
    const completedMetrics = metricsArray.filter(m => m.duration !== undefined);

    return {
      summary: {
        totalRequests: completedMetrics.length,
        averageResponseTime: completedMetrics.reduce((sum, m) => sum + (m.duration || 0), 0) / completedMetrics.length || 0,
        cacheHitRate: this.cache.size / (completedMetrics.length + this.cache.size) || 0,
        memoryUsage: this.getMemoryUsage()
      },
      details: metricsArray
    };
  }
}

// React hooks for performance optimization
export function usePerformanceOptimizations() {
  const [performanceRef] = React.useState(() => new PerformanceService());

  React.useEffect(() => {
    return () => {
      performanceRef.cleanup();
    };
  }, [performanceRef]);

  return {
    performanceService: performanceRef,
    startTiming: performanceRef.startTiming.bind(performanceRef),
    endTiming: performanceRef.endTiming.bind(performanceRef),
    fetchWithRetry: performanceRef.fetchWithRetry.bind(performanceRef),
    fetchWithProgress: performanceRef.fetchWithProgress.bind(performanceRef),
    createIntersectionObserver: performanceRef.createIntersectionObserver.bind(performanceRef),
    debounce: performanceRef.debounce.bind(performanceRef),
    throttle: performanceRef.throttle.bind(performanceRef),
    loadPresentationProgressively: performanceRef.loadPresentationProgressively.bind(performanceRef)
  };
}

export interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  placeholder?: string;
  onLoad?: () => void;
  onError?: () => void;
}

export function LazyImage({
  src,
  placeholder = '',
  onLoad,
  onError,
  className = '',
  ...props
}: LazyImageProps) {
  const [isLoaded, setIsLoaded] = React.useState(false);
  const [isInView, setIsInView] = React.useState(false);
  const [hasError, setHasError] = React.useState(false);
  const imgRef = React.useRef<HTMLImageElement>(null);

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, []);

  const handleLoad = React.useCallback(() => {
    setIsLoaded(true);
    onLoad?.();
  }, [onLoad]);

  const handleError = React.useCallback(() => {
    setHasError(true);
    onError?.();
  }, [onError]);

  return (
    <div className={`relative ${className}`}>
      {/* Placeholder */}
      {!isLoaded && (
        <div
          className="absolute inset-0 bg-gray-200 animate-pulse rounded"
          style={{
            backgroundImage: placeholder ? `url(${placeholder})` : undefined,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            filter: placeholder ? 'blur(10px)' : undefined
          }}
        />
      )}

      {/* Actual image */}
      <img
        ref={imgRef}
        src={isInView ? src : undefined}
        onLoad={handleLoad}
        onError={handleError}
        className={`transition-opacity duration-300 ${
          isLoaded ? 'opacity-100' : 'opacity-0'
        } ${hasError ? 'hidden' : ''}`}
        {...props}
      />

      {/* Error state */}
      {hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded">
          <span className="text-gray-400 text-sm">Failed to load image</span>
        </div>
      )}
    </div>
  );
}

// Singleton instance
export const performanceService = new PerformanceService();

export default performanceService;