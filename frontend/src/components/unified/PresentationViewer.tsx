import { useState } from 'react';
import type { PresentationDocument, SlideType } from '../../types/presentations';
import { PresentationStatusIndicator } from './PresentationStatusIndicator';

interface PresentationViewerProps {
  presentation: PresentationDocument;
  isOpen: boolean;
  onClose: () => void;
  onExport?: (format: 'json' | 'markdown') => void;
  isExporting?: boolean;
}

export function PresentationViewer({ 
  presentation, 
  isOpen, 
  onClose, 
  onExport, 
  isExporting = false 
}: PresentationViewerProps) {
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [showTeacherScript, setShowTeacherScript] = useState(true);

  if (!isOpen) return null;

  const currentSlide = presentation.slides[currentSlideIndex];
  const totalSlides = presentation.slides.length;

  const goToSlide = (index: number) => {
    if (index >= 0 && index < totalSlides) {
      setCurrentSlideIndex(index);
    }
  };

  const nextSlide = () => goToSlide(currentSlideIndex + 1);
  const prevSlide = () => goToSlide(currentSlideIndex - 1);

  const getSlideTypeColor = (type: SlideType): string => {
    switch (type) {
      case 'title':
        return 'bg-purple-100 text-purple-800';
      case 'content':
        return 'bg-blue-100 text-blue-800';
      case 'activity':
        return 'bg-green-100 text-green-800';
      case 'assessment':
        return 'bg-orange-100 text-orange-800';
      case 'closure':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSlideTypeIcon = (type: SlideType): string => {
    switch (type) {
      case 'title':
        return '📋';
      case 'content':
        return '📝';
      case 'activity':
        return '🎯';
      case 'assessment':
        return '📊';
      case 'closure':
        return '🎯';
      default:
        return '📄';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 p-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold text-gray-900">{presentation.title}</h2>
            <PresentationStatusIndicator status={presentation.status} />
          </div>
          <div className="flex items-center gap-2">
            {onExport && (
              <>
                <button
                  onClick={() => onExport('json')}
                  disabled={isExporting}
                  className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-md transition-colors"
                >
                  {isExporting ? 'Exporting...' : 'Export JSON'}
                </button>
                <button
                  onClick={() => onExport('markdown')}
                  disabled={isExporting}
                  className="px-3 py-1 text-sm bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white rounded-md transition-colors"
                >
                  {isExporting ? 'Exporting...' : 'Export Markdown'}
                </button>
              </>
            )}
            <button
              onClick={onClose}
              className="px-3 py-1 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
            >
              Close
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex">
          {/* Slide Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {currentSlide && (
              <div className="space-y-4">
                {/* Slide Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-500">
                      Slide {currentSlide.slide_number} of {totalSlides}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSlideTypeColor(currentSlide.slide_type)}`}>
                      {getSlideTypeIcon(currentSlide.slide_type)} {currentSlide.slide_type}
                    </span>
                    <span className="text-sm text-gray-500">
                      {currentSlide.duration_minutes} min
                    </span>
                  </div>
                </div>

                {/* Slide Title */}
                <h3 className="text-2xl font-bold text-gray-900">{currentSlide.title}</h3>

                {/* Slide Content */}
                <div className="prose prose-lg max-w-none">
                  <div className="whitespace-pre-wrap text-gray-700">{currentSlide.content}</div>
                </div>

                {/* Materials */}
                {currentSlide.materials_needed.length > 0 && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">Materials Needed:</h4>
                    <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                      {currentSlide.materials_needed.map((material, index) => (
                        <li key={index}>{material}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Teacher Script Sidebar */}
          <div className="w-96 border-l border-gray-200 flex flex-col">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="font-medium text-gray-900">Teacher Script</h3>
              <button
                onClick={() => setShowTeacherScript(!showTeacherScript)}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                {showTeacherScript ? 'Hide' : 'Show'}
              </button>
            </div>
            {showTeacherScript && currentSlide && (
              <div className="flex-1 p-4 overflow-y-auto">
                <div className="bg-yellow-50 rounded-lg p-4">
                  <div className="whitespace-pre-wrap text-sm text-gray-700">
                    {currentSlide.teacher_script}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Navigation */}
        <div className="border-t border-gray-200 p-4 flex items-center justify-between">
          <button
            onClick={prevSlide}
            disabled={currentSlideIndex === 0}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-300 text-white rounded-md transition-colors"
          >
            Previous
          </button>

          {/* Slide Navigation Dots */}
          <div className="flex items-center gap-2">
            {presentation.slides.map((_, index) => (
              <button
                key={index}
                onClick={() => goToSlide(index)}
                className={`w-2 h-2 rounded-full transition-colors ${
                  index === currentSlideIndex
                    ? 'bg-blue-600'
                    : 'bg-gray-300 hover:bg-gray-400'
                }`}
              />
            ))}
          </div>

          <button
            onClick={nextSlide}
            disabled={currentSlideIndex === totalSlides - 1}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-300 text-white rounded-md transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

export default PresentationViewer;