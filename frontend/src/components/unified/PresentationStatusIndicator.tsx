import type { PresentationStatus } from '../../types/presentations';

interface PresentationStatusIndicatorProps {
  status: PresentationStatus;
  className?: string;
}

export function PresentationStatusIndicator({ status, className = '' }: PresentationStatusIndicatorProps) {
  const getStatusColor = (status: PresentationStatus): string => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'generating':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: PresentationStatus): string => {
    switch (status) {
      case 'pending':
        return '⏳';
      case 'generating':
        return '🔄';
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      default:
        return '❓';
    }
  };

  const getStatusText = (status: PresentationStatus): string => {
    switch (status) {
      case 'pending':
        return 'Pending';
      case 'generating':
        return 'Generating...';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(status)} ${className}`}>
      <span className="animate-pulse" style={{ animationDuration: status === 'generating' ? '2s' : '0s' }}>
        {getStatusIcon(status)}
      </span>
      <span>{getStatusText(status)}</span>
    </div>
  );
}

export default PresentationStatusIndicator;