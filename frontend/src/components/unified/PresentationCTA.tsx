import type { PresentationStatus } from '../../types/presentations';
import { PresentationStatusIndicator } from './PresentationStatusIndicator';

interface PresentationCTAProps {
  lessonId: string;
  presentationStatus?: PresentationStatus;
  presentationId?: string;
  onGenerate?: () => void;
  onView?: (presentationId: string) => void;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function PresentationCTA({ 
  lessonId,
  presentationStatus,
  presentationId,
  onGenerate,
  onView,
  disabled = false,
  size = 'md'
}: PresentationCTAProps) {
  
  const getSizeClasses = (size: 'sm' | 'md' | 'lg'): string => {
    switch (size) {
      case 'sm':
        return 'px-3 py-1 text-sm';
      case 'lg':
        return 'px-6 py-3 text-lg';
      default:
        return 'px-4 py-2 text-base';
    }
  };

  const canGenerate = !presentationStatus || presentationStatus === 'failed' || presentationStatus === 'completed';
  const canView = presentationStatus === 'completed' && presentationId;

  if (presentationStatus) {
    return (
      <div className="flex items-center gap-2">
        <PresentationStatusIndicator status={presentationStatus} />
        {presentationStatus === 'completed' && canView && onView && (
          <button
            onClick={() => onView(presentationId!)}
            disabled={disabled}
            className={`bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-md font-medium transition-colors ${getSizeClasses(size)}`}
          >
            View Presentation
          </button>
        )}
        {presentationStatus === 'completed' && canGenerate && onGenerate && (
          <button
            onClick={onGenerate}
            disabled={disabled}
            className={`bg-gray-600 hover:bg-gray-700 disabled:bg-gray-300 text-white rounded-md font-medium transition-colors ${getSizeClasses(size)}`}
          >
            Regenerate
          </button>
        )}
        {presentationStatus === 'failed' && onGenerate && (
          <button
            onClick={onGenerate}
            disabled={disabled}
            className={`bg-gray-600 hover:bg-gray-700 disabled:bg-gray-300 text-white rounded-md font-medium transition-colors ${getSizeClasses(size)}`}
          >
            Regenerate
          </button>
        )}
      </div>
    );
  }

  if (onGenerate) {
    return (
      <button
        onClick={onGenerate}
        disabled={disabled}
        className={`bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white rounded-md font-medium transition-colors ${getSizeClasses(size)}`}
      >
        Generate Presentation
      </button>
    );
  }

  return null;
}

export default PresentationCTA;
