import type { PresentationStatus } from '../../types/presentations';

interface PresentationStatusIndicatorProps {
  status: PresentationStatus;
  className?: string;
}

export function PresentationStatusIndicator({ status, className = '' }: PresentationStatusIndicatorProps) {
  const getStatusColor = (status: PresentationStatus): string => {
    switch (status) {
      case 'pending':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'complete':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'stale':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: PresentationStatus): string => {
    switch (status) {
      case 'pending':
        return '🔄';
      case 'complete':
        return '✅';
      case 'error':
        return '❌';
      case 'stale':
        return '⚠️';
      default:
        return '❓';
    }
  };

  const getStatusText = (status: PresentationStatus): string => {
    switch (status) {
      case 'pending':
        return 'Generating...';
      case 'complete':
        return 'Completed';
      case 'error':
        return 'Failed';
      case 'stale':
        return 'Stale';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(status)} ${className}`}>
      <span className={status === 'pending' ? 'animate-spin' : ''}>
        {getStatusIcon(status)}
      </span>
      <span>{getStatusText(status)}</span>
    </div>
  );
}

export default PresentationStatusIndicator;
