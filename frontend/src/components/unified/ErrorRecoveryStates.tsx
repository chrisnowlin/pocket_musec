import React, { useState } from 'react';
import { PresentationError } from '../../errors/presentationErrors';

interface ErrorRecoveryStatesProps {
  error: PresentationError;
  onRetry?: () => void;
  onContactSupport?: () => void;
  onAlternativeAction?: () => void;
  showDetails?: boolean;
  compact?: boolean;
  className?: string;
}

export function ErrorRecoveryStates({
  error,
  onRetry,
  onContactSupport,
  onAlternativeAction,
  showDetails = false,
  compact = false,
  className = ''
}: ErrorRecoveryStatesProps) {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  const getErrorIcon = (errorCode: string): string => {
    const iconMap: Record<string, string> = {
      'LESSON_NOT_FOUND': '📚',
      'LESSON_ACCESS_DENIED': '🔒',
      'JOB_NOT_FOUND': '🔍',
      'JOB_ACCESS_DENIED': '🔒',
      'VALIDATION_FAILED': '⚠️',
      'INVALID_STYLE': '🎨',
      'INVALID_TIMEOUT': '⏰',
      'INVALID_EXPORT_FORMAT': '📄',
      'JOB_TIMEOUT': '⏱️',
      'LLM_TIMEOUT': '🤖',
      'LLM_RATE_LIMITED': '🚦',
      'SERVICE_UNAVAILABLE': '🔧',
      'EXPORT_FAILED': '📤',
      'DATABASE_ERROR': '💾',
      'INTERNAL_ERROR': '⚡',
      'JOB_CANCELLED': '🛑',
      'NETWORK_ERROR': '🌐'
    };

    return iconMap[errorCode] || '❌';
  };

  const getErrorColor = (errorCode: string): string => {
    const colorMap: Record<string, string> = {
      'NETWORK_ERROR': 'text-orange-600 bg-orange-50',
      'SERVICE_UNAVAILABLE': 'text-yellow-600 bg-yellow-50',
      'LLM_RATE_LIMITED': 'text-yellow-600 bg-yellow-50',
      'LLM_TIMEOUT': 'text-blue-600 bg-blue-50',
      'JOB_TIMEOUT': 'text-blue-600 bg-blue-50',
      'VALIDATION_FAILED': 'text-purple-600 bg-purple-50',
      'EXPORT_FAILED': 'text-red-600 bg-red-50',
      'INTERNAL_ERROR': 'text-red-600 bg-red-50'
    };

    return colorMap[errorCode] || 'text-red-600 bg-red-50';
  };

  const getErrorActions = (errorCode: string) => {
    const actionMap: Record<string, Array<{
      label: string;
      action: string;
      type: 'primary' | 'secondary' | 'danger';
      icon?: string;
    }>> = {
      'NETWORK_ERROR': [
        { label: 'Retry', action: 'retry', type: 'primary', icon: '🔄' },
        { label: 'Check Connection', action: 'check_network', type: 'secondary', icon: '🌐' }
      ],
      'SERVICE_UNAVAILABLE': [
        { label: 'Try Again Later', action: 'retry_later', type: 'primary', icon: '⏰' },
        { label: 'Use Without AI', action: 'skip_ai', type: 'secondary', icon: '⏭️' }
      ],
      'LLM_RATE_LIMITED': [
        { label: 'Retry in 1 Minute', action: 'retry_delayed', type: 'primary', icon: '⏱️' },
        { label: 'Skip AI Polish', action: 'skip_ai', type: 'secondary', icon: '⏭️' }
      ],
      'LLM_TIMEOUT': [
        { label: 'Try Again', action: 'retry', type: 'primary', icon: '🔄' },
        { label: 'Increase Timeout', action: 'increase_timeout', type: 'secondary', icon: '⏰' },
        { label: 'Skip AI Polish', action: 'skip_ai', type: 'secondary', icon: '⏭️' }
      ],
      'VALIDATION_FAILED': [
        { label: 'Fix Input', action: 'fix_input', type: 'primary', icon: '✏️' },
        { label: 'Reset Form', action: 'reset', type: 'secondary', icon: '🔄' }
      ],
      'EXPORT_FAILED': [
        { label: 'Try Again', action: 'retry', type: 'primary', icon: '🔄' },
        { label: 'Download Another Format', action: 'alternative_format', type: 'secondary', icon: '📄' }
      ],
      'INTERNAL_ERROR': [
        { label: 'Try Again', action: 'retry', type: 'primary', icon: '🔄' },
        { label: 'Contact Support', action: 'contact_support', type: 'secondary', icon: '💬' },
        { label: 'Start Over', action: 'start_over', type: 'danger', icon: '🛑' }
      ]
    };

    return actionMap[errorCode] || [
      { label: 'Try Again', action: 'retry', type: 'primary', icon: '🔄' },
      { label: 'Contact Support', action: 'contact_support', type: 'secondary', icon: '💬' }
    ];
  };

  const handleAction = async (action: string) => {
    switch (action) {
      case 'retry':
      case 'retry_delayed':
        if (onRetry) {
          setIsRetrying(true);
          try {
            await onRetry();
          } finally {
            setIsRetrying(false);
          }
        }
        break;
      case 'contact_support':
        if (onContactSupport) {
          onContactSupport();
        } else {
          window.open('mailto:support@pocketmusec.com?subject=Error Report', '_blank');
        }
        break;
      case 'skip_ai':
      case 'alternative_format':
        if (onAlternativeAction) {
          onAlternativeAction();
        }
        break;
      case 'check_network':
        window.location.reload();
        break;
      case 'start_over':
        window.location.href = '/lessons';
        break;
      case 'fix_input':
        // Focus on first input field
        const firstInput = document.querySelector('input, textarea, select') as HTMLElement;
        if (firstInput) {
          firstInput.focus();
          firstInput.scrollIntoView({ behavior: 'smooth' });
        }
        break;
      default:
        console.log(`Action not implemented: ${action}`);
    }
  };

  const errorColorClass = getErrorColor(error.error.code);
  const errorIcon = getErrorIcon(error.error.code);
  const actions = getErrorActions(error.error.code);

  if (compact) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-3 ${className}`}>
        <div className="flex items-center gap-3">
          <div className="text-2xl">{errorIcon}</div>
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-900">{error.error.user_message}</p>
            <div className="flex items-center gap-2 mt-2">
              {actions.slice(0, 2).map((action, index) => (
                <button
                  key={index}
                  onClick={() => handleAction(action.action)}
                  disabled={isRetrying && action.action === 'retry'}
                  className={`px-3 py-1 text-xs rounded-md transition-colors ${
                    action.type === 'primary'
                      ? 'bg-blue-600 hover:bg-blue-700 text-white disabled:bg-blue-300'
                      : action.type === 'danger'
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-gray-200 hover:bg-gray-300 text-gray-900'
                  }`}
                >
                  {isRetrying && action.action === 'retry' ? 'Retrying...' : action.label}
                </button>
              ))}
            </div>
          </div>
          {(showDetails || import.meta.env.DEV) && (
            <button
              onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
          )}
        </div>

        {showTechnicalDetails && (
          <div className="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-600">
            <div><strong>Code:</strong> {error.error.code}</div>
            <div><strong>Technical:</strong> {error.error.technical_message}</div>
            {error.error.retry_after_seconds && (
              <div><strong>Retry after:</strong> {error.error.retry_after_seconds}s</div>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden ${className}`}>
      {/* Header */}
      <div className={`${errorColorClass.split(' ')[1]} p-4 border-b border-gray-200`}>
        <div className="flex items-center gap-3">
          <div className="text-3xl">{errorIcon}</div>
          <div>
            <h3 className="font-semibold text-gray-900">Something went wrong</h3>
            <p className="text-sm text-gray-600 mt-1">{error.error.user_message}</p>
          </div>
        </div>
      </div>

      {/* Recommended Actions */}
      <div className="p-4 border-b border-gray-200">
        <h4 className="font-medium text-gray-900 mb-3">Recommended Actions</h4>
        <div className="space-y-2">
          {actions.map((action, index) => (
            <button
              key={index}
              onClick={() => handleAction(action.action)}
              disabled={isRetrying && action.action === 'retry'}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-md border transition-colors ${
                action.type === 'primary'
                  ? 'border-blue-600 bg-blue-50 hover:bg-blue-100 text-blue-700 disabled:bg-gray-100 disabled:text-gray-400'
                  : action.type === 'danger'
                  ? 'border-red-600 bg-red-50 hover:bg-red-100 text-red-700'
                  : 'border-gray-300 bg-gray-50 hover:bg-gray-100 text-gray-700'
              }`}
            >
              <span className="text-lg">{action.icon}</span>
              <div className="flex-1 text-left">
                <div className="font-medium">{action.label}</div>
                <div className="text-sm opacity-75">
                  {getActionDescription(action.action)}
                </div>
              </div>
              {isRetrying && action.action === 'retry' && (
                <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Error Context */}
      {error.error.context && Object.keys(error.error.context).length > 0 && (
        <div className="p-4 border-b border-gray-200">
          <h4 className="font-medium text-gray-900 mb-2">Context</h4>
          <div className="text-sm text-gray-600 space-y-1">
            {Object.entries(error.error.context).map(([key, value]) => (
              <div key={key}>
                <span className="font-medium capitalize">{key.replace(/_/g, ' ')}:</span> {String(value)}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Technical Details */}
      {(showDetails || import.meta.env.DEV) && (
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
            className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {showTechnicalDetails ? 'Hide' : 'Show'} Technical Details
          </button>

          {showTechnicalDetails && (
            <div className="mt-3 space-y-2 text-sm text-gray-600">
              <div><strong>Error Code:</strong> {error.error.code}</div>
              <div><strong>Technical Message:</strong> {error.error.technical_message}</div>
              {error.error.retry_after_seconds && (
                <div><strong>Retry After:</strong> {error.error.retry_after_seconds} seconds</div>
              )}
              {error.error.retry_recommended !== undefined && (
                <div><strong>Retry Recommended:</strong> {error.error.retry_recommended ? 'Yes' : 'No'}</div>
              )}
              <div><strong>Timestamp:</strong> {new Date().toISOString()}</div>
            </div>
          )}
        </div>
      )}

      {/* Recovery Tips */}
      <div className="p-4 bg-gray-50">
        <h4 className="font-medium text-gray-900 mb-2">💡 Tips</h4>
        <div className="text-sm text-gray-600 space-y-1">
          {getErrorTips(error.error.code).map((tip, index) => (
            <div key={index} className="flex items-start gap-2">
              <span className="text-blue-500 mt-0.5">•</span>
              <span>{tip}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function getActionDescription(action: string): string {
  const descriptions: Record<string, string> = {
    retry: 'Attempt the operation again',
    retry_later: 'Try again after a short delay',
    retry_delayed: 'Wait for rate limit to reset',
    skip_ai: 'Continue without AI enhancement',
    increase_timeout: 'Allow more time for processing',
    check_network: 'Check your internet connection',
    contact_support: 'Get help from our support team',
    alternative_format: 'Try downloading in another format',
    start_over: 'Return to the beginning',
    fix_input: 'Correct any invalid input fields',
    reset: 'Clear all form fields'
  };

  return descriptions[action] || 'Execute this action';
}

function getErrorTips(errorCode: string): string[] {
  const tipsMap: Record<string, string[]> = {
    'NETWORK_ERROR': [
      'Check your internet connection',
      'Try refreshing the page',
      'If the problem persists, contact support'
    ],
    'SERVICE_UNAVAILABLE': [
      'Our services are temporarily unavailable',
      'Try again in a few minutes',
      'You can continue without AI features if needed'
    ],
    'LLM_RATE_LIMITED': [
      'You\'ve reached the usage limit for AI features',
      'Wait a minute before trying again',
      'Consider upgrading your plan for higher limits'
    ],
    'LLM_TIMEOUT': [
      'AI processing is taking longer than expected',
      'Try again with a longer timeout',
      'Continue without AI enhancement if needed'
    ],
    'VALIDATION_FAILED': [
      'Check that all required fields are filled',
      'Ensure file formats are supported',
      'Review any validation messages'
    ],
    'EXPORT_FAILED': [
      'Try downloading in a different format',
      'Check your browser download settings',
      'Clear your browser cache and try again'
    ],
    'INTERNAL_ERROR': [
      'This appears to be a system issue',
      'Try the operation once more',
      'Contact support if the problem continues'
    ]
  };

  return tipsMap[errorCode] || [
    'Try the operation again',
    'Refresh the page and retry',
    'Contact support if the issue persists'
  ];
}

// Specialized error components
export function GenerationErrorState({
  error,
  onRetry,
  onSkipAI,
  onContactSupport
}: {
  error: PresentationError;
  onRetry?: () => void;
  onSkipAI?: () => void;
  onContactSupport?: () => void;
}) {
  return (
    <div className="text-center py-8">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
        <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">Presentation Generation Failed</h3>
      <p className="text-sm text-gray-500 mb-6 max-w-md mx-auto">
        {error.error.user_message}
      </p>
      <div className="flex flex-col gap-3 max-w-sm mx-auto">
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
          >
            Try Again
          </button>
        )}
        {onSkipAI && (
          <button
            onClick={onSkipAI}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
          >
            Continue Without AI
          </button>
        )}
        {onContactSupport && (
          <button
            onClick={onContactSupport}
            className="px-4 py-2 text-blue-600 hover:text-blue-700 transition-colors"
          >
            Contact Support
          </button>
        )}
      </div>
    </div>
  );
}

export function ExportErrorState({
  error,
  onRetry,
  onTryAlternative,
  onContactSupport
}: {
  error: PresentationError;
  onRetry?: () => void;
  onTryAlternative?: () => void;
  onContactSupport?: () => void;
}) {
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <svg className="h-5 w-5 text-yellow-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div className="flex-1">
          <h4 className="text-sm font-medium text-yellow-800">Export Error</h4>
          <p className="mt-1 text-sm text-yellow-700">{error.error.user_message}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {onRetry && (
              <button
                onClick={onRetry}
                className="px-3 py-1 text-sm bg-yellow-600 hover:bg-yellow-700 text-white rounded-md transition-colors"
              >
                Retry Export
              </button>
            )}
            {onTryAlternative && (
              <button
                onClick={onTryAlternative}
                className="px-3 py-1 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
              >
                Try Different Format
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ErrorRecoveryStates;