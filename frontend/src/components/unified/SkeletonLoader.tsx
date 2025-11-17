import React from 'react';

interface SkeletonLoaderProps {
  type: 'presentation' | 'slide' | 'list' | 'text' | 'card' | 'progress' | 'button' | 'avatar';
  lines?: number;
  width?: string | number;
  height?: string | number;
  className?: string;
  animate?: boolean;
}

export function SkeletonLoader({
  type,
  lines = 1,
  width,
  height,
  className = '',
  animate = true
}: SkeletonLoaderProps) {
  const baseClasses = `bg-gray-200 rounded ${animate ? 'animate-pulse' : ''} ${className}`;

  const renderSkeleton = () => {
    switch (type) {
      case 'presentation':
        return (
          <div className="space-y-4">
            {/* Header skeleton */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <div className="flex items-center gap-3">
                <div className="w-32 h-6 bg-gray-200 rounded animate-pulse" />
                <div className="w-20 h-4 bg-gray-200 rounded animate-pulse" />
              </div>
              <div className="flex items-center gap-2">
                <div className="w-16 h-8 bg-gray-200 rounded animate-pulse" />
                <div className="w-16 h-8 bg-gray-200 rounded animate-pulse" />
                <div className="w-8 h-4 bg-gray-200 rounded animate-pulse" />
              </div>
            </div>

            {/* Content skeleton */}
            <div className="p-6 space-y-4">
              <div className="space-y-3">
                <div className="w-3/4 h-8 bg-gray-200 rounded animate-pulse" />
                <div className="w-1/2 h-6 bg-gray-200 rounded animate-pulse" />
                <div className="space-y-2">
                  <div className="w-full h-4 bg-gray-200 rounded animate-pulse" />
                  <div className="w-5/6 h-4 bg-gray-200 rounded animate-pulse" />
                  <div className="w-4/5 h-4 bg-gray-200 rounded animate-pulse" />
                </div>
              </div>
            </div>

            {/* Sidebar skeleton */}
            <div className="w-96 border-l border-gray-200 p-4">
              <div className="space-y-3">
                <div className="w-24 h-6 bg-gray-200 rounded animate-pulse" />
                <div className="space-y-2">
                  <div className="w-full h-3 bg-gray-200 rounded animate-pulse" />
                  <div className="w-full h-3 bg-gray-200 rounded animate-pulse" />
                  <div className="w-3/4 h-3 bg-gray-200 rounded animate-pulse" />
                </div>
              </div>
            </div>

            {/* Navigation skeleton */}
            <div className="border-t border-gray-200 p-4 flex items-center justify-between">
              <div className="w-16 h-8 bg-gray-200 rounded animate-pulse" />
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="w-2 h-2 bg-gray-200 rounded-full animate-pulse" />
                ))}
              </div>
              <div className="w-16 h-8 bg-gray-200 rounded animate-pulse" />
            </div>
          </div>
        );

      case 'slide':
        return (
          <div className="p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-24 h-4 bg-gray-200 rounded animate-pulse" />
              <div className="w-16 h-4 bg-gray-200 rounded animate-pulse" />
              <div className="w-20 h-4 bg-gray-200 rounded animate-pulse" />
            </div>
            <div className="w-3/4 h-10 bg-gray-200 rounded animate-pulse" />
            <div className="w-1/2 h-6 bg-gray-200 rounded animate-pulse" />
            <div className="space-y-2">
              <div className="w-full h-4 bg-gray-200 rounded animate-pulse" />
              <div className="w-5/6 h-4 bg-gray-200 rounded animate-pulse" />
              <div className="w-4/5 h-4 bg-gray-200 rounded animate-pulse" />
              <div className="w-3/4 h-4 bg-gray-200 rounded animate-pulse" />
            </div>
          </div>
        );

      case 'list':
        return (
          <div className="space-y-3">
            {Array.from({ length: lines }).map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-200 rounded-full animate-pulse" />
                <div className="flex-1 space-y-2">
                  <div className="w-3/4 h-4 bg-gray-200 rounded animate-pulse" />
                  <div className="w-1/2 h-3 bg-gray-200 rounded animate-pulse" />
                </div>
                <div className="w-20 h-6 bg-gray-200 rounded animate-pulse" />
              </div>
            ))}
          </div>
        );

      case 'card':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="w-32 h-6 bg-gray-200 rounded animate-pulse" />
              <div className="w-16 h-4 bg-gray-200 rounded animate-pulse" />
            </div>
            <div className="space-y-2">
              <div className="w-full h-4 bg-gray-200 rounded animate-pulse" />
              <div className="w-5/6 h-4 bg-gray-200 rounded animate-pulse" />
            </div>
            <div className="flex items-center gap-2">
              <div className="w-16 h-8 bg-gray-200 rounded animate-pulse" />
              <div className="w-16 h-8 bg-gray-200 rounded animate-pulse" />
            </div>
          </div>
        );

      case 'progress':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 bg-gray-200 rounded animate-pulse" />
                <div className="w-32 h-6 bg-gray-200 rounded animate-pulse" />
              </div>
              <div className="w-16 h-4 bg-gray-200 rounded animate-pulse" />
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full w-1/3 animate-pulse" />
            </div>
            <div className="flex items-center gap-2">
              <div className="w-20 h-3 bg-gray-200 rounded animate-pulse" />
              <div className="w-16 h-3 bg-gray-200 rounded animate-pulse" />
            </div>
          </div>
        );

      case 'avatar':
        return (
          <div className="w-10 h-10 bg-gray-200 rounded-full animate-pulse" />
        );

      case 'button':
        return (
          <div
            className={`h-8 bg-gray-200 rounded animate-pulse ${className}`}
            style={{ width: width || 'auto' }}
          />
        );

      case 'text':
      default:
        return (
          <div className={`space-y-2 ${className}`}>
            {Array.from({ length: lines }).map((_, i) => (
              <div
                key={i}
                className="bg-gray-200 rounded animate-pulse"
                style={{
                  width: Array.isArray(width) ? width[i] : width || '100%',
                  height: height || '1rem'
                }}
              />
            ))}
          </div>
        );
    }
  };

  return renderSkeleton();
}

// Pre-defined skeleton combinations
export const PresentationSkeleton = () => (
  <SkeletonLoader type="presentation" />
);

export const SlideSkeleton = () => (
  <SkeletonLoader type="slide" />
);

export const ProgressSkeleton = () => (
  <SkeletonLoader type="progress" />
);

export const CardSkeleton = () => (
  <SkeletonLoader type="card" />
);

export const ListSkeleton = ({ items = 3 }: { items?: number }) => (
  <SkeletonLoader type="list" lines={items} />
);

// Loading overlay component
interface LoadingOverlayProps {
  isVisible: boolean;
  message?: string;
  skeleton?: React.ReactNode;
  showProgress?: boolean;
  progress?: number;
}

export function LoadingOverlay({
  isVisible,
  message = 'Loading...',
  skeleton,
  showProgress = false,
  progress = 0
}: LoadingOverlayProps) {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mb-4">
            <svg className="w-6 h-6 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>

          <h3 className="text-lg font-medium text-gray-900 mb-2">{message}</h3>

          {showProgress && (
            <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          )}

          {skeleton ? (
            <div className="mt-4">
              {skeleton}
            </div>
          ) : (
            <div className="mt-4 space-y-2">
              <SkeletonLoader type="text" lines={3} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Skeleton for presentation generation flow
export const PresentationGenerationSkeleton = () => {
  const steps = [
    { name: 'Fetching lesson', icon: '📚' },
    { name: 'Building scaffold', icon: '🏗️' },
    { name: 'Processing with AI', icon: '🤖' },
    { name: 'Generating exports', icon: '📤' }
  ];

  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-semibold text-gray-900">Generating Presentation</h3>
        <div className="flex items-center gap-2 text-sm text-blue-600">
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
          Processing...
        </div>
      </div>

      {/* Progress bar skeleton */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Progress</span>
          <span className="text-sm font-bold text-gray-900">--%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div className="bg-blue-500 h-3 rounded-full w-1/4 animate-pulse" />
        </div>
      </div>

      {/* Steps skeleton */}
      <div className="space-y-3">
        {steps.map((step, index) => (
          <div
            key={index}
            className={`flex items-center gap-3 p-3 rounded-lg border ${
              index === 0 ? 'border-blue-200 bg-blue-50' : 'border-gray-200'
            }`}
          >
            <div className="flex items-center gap-2">
              <div className="text-lg">{step.icon}</div>
              <div className="text-sm">
                {index === 0 ? '⏳' : '⏸️'}
              </div>
            </div>
            <div className="flex-1">
              <div className={`font-medium text-sm ${
                index === 0 ? 'text-blue-600' : 'text-gray-500'
              }`}>
                {step.name}
              </div>
              <div className="text-xs text-gray-500">Processing...</div>
            </div>
            <div className="text-xs text-gray-400">
              {index === 0 ? '0s' : '--s'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SkeletonLoader;