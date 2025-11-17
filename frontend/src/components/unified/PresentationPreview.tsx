import React from 'react';
import type { PresentationPreview as PresentationPreviewType } from '@/types/unified';

/**
 * Simple UI for displaying a presentation preview.
 * Shows slide titles, key points and estimated durations.
 */
export const PresentationPreviewComponent: React.FC<{ preview: PresentationPreviewType }> = ({ preview }) => {
  return (
    <div className="p-4 border rounded-md bg-white shadow-md">
      <h2 className="text-xl font-semibold mb-2">Preview for Presentation {preview.presentationId}</h2>
      <p className="text-sm text-gray-600 mb-4">
        Generated at: {new Date(preview.generatedAt).toLocaleString()}
      </p>
      <ul className="space-y-4">
        {preview.slides.map((slide, idx) => (
          <li key={idx} className="border-b pb-2">
            <h3 className="font-medium">{idx + 1}. {slide.title}</h3>
            <ul className="list-disc list-inside ml-4 text-sm text-gray-700">
              {slide.keyPoints.map((point: string, i: number) => (
                <li key={i}>{point}</li>
              ))}
            </ul>
            <p className="text-xs text-gray-500 mt-1">
              Estimated duration: {slide.estimatedDurationSeconds}s
            </p>
          </li>
        ))}
      </ul>
      <div className="mt-4 text-sm text-gray-800">
        <strong>Total estimated duration:</strong> {preview.totalEstimatedDurationSeconds}s
      </div>
    </div>
  );
};
