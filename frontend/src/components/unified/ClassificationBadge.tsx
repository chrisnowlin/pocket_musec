import type { ImageClassification } from '../../types/unified';

interface ClassificationBadgeProps {
  classification: ImageClassification;
}

export default function ClassificationBadge({ classification }: ClassificationBadgeProps) {
  const getCategoryColor = (category: string) => {
    const colors = {
      sheet_music: 'bg-blue-100 text-blue-800',
      musical_instruments: 'bg-green-100 text-green-800',
      instructional_diagram: 'bg-purple-100 text-purple-800',
      music_theory: 'bg-yellow-100 text-yellow-800',
      performance: 'bg-red-100 text-red-800',
      classroom: 'bg-indigo-100 text-indigo-800',
      handwritten: 'bg-gray-100 text-gray-800',
    };
    return colors[category as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getEducationColor = (level: string) => {
    const colors = {
      elementary: 'bg-green-50 text-green-700',
      middle_school: 'bg-blue-50 text-blue-700',
      high_school: 'bg-purple-50 text-purple-700',
      college: 'bg-red-50 text-red-700',
      professional: 'bg-gray-50 text-gray-700',
    };
    return colors[level as keyof typeof colors] || 'bg-gray-50 text-gray-700';
  };

  const getDifficultyColor = (level: string) => {
    const colors = {
      beginner: 'bg-green-50 text-green-700',
      intermediate: 'bg-yellow-50 text-yellow-700',
      advanced: 'bg-orange-50 text-orange-700',
      expert: 'bg-red-50 text-red-700',
    };
    return colors[level as keyof typeof colors] || 'bg-gray-50 text-gray-700';
  };

  return (
    <div className="mt-3 space-y-2">
      {/* Category Badge */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-ink-600">Category:</span>
        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(classification.category)}`}>
          {classification.category.replace('_', ' ')}
        </span>
        <span className="text-xs text-ink-500">
          {Math.round(classification.confidence * 100)}% confidence
        </span>
      </div>

      {/* Education Level */}
      {classification.education_level && (
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-ink-600">Level:</span>
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getEducationColor(classification.education_level)}`}>
            {classification.education_level.replace('_', ' ')}
          </span>
        </div>
      )}

      {/* Difficulty Level */}
      {classification.difficulty_level && (
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-ink-600">Difficulty:</span>
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(classification.difficulty_level)}`}>
            {classification.difficulty_level}
          </span>
        </div>
      )}

      {/* Tags */}
      {classification.tags && classification.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          <span className="text-xs font-medium text-ink-600">Tags:</span>
          {classification.tags.slice(0, 5).map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-parchment-100 text-parchment-700"
            >
              {tag}
            </span>
          ))}
          {classification.tags.length > 5 && (
            <span className="text-xs text-ink-500">+{classification.tags.length - 5} more</span>
          )}
        </div>
      )}

      {/* Musical Metadata */}
      {classification.musical_metadata && (
        <div className="text-xs text-ink-600 space-y-1">
          {classification.musical_metadata.key_signature && (
            <div>Key: {classification.musical_metadata.key_signature}</div>
          )}
          {classification.musical_metadata.time_signature && (
            <div>Time: {classification.musical_metadata.time_signature}</div>
          )}
          {classification.musical_metadata.tempo && (
            <div>Tempo: {classification.musical_metadata.tempo}</div>
          )}
          {classification.musical_metadata.instruments && classification.musical_metadata.instruments.length > 0 && (
            <div>Instruments: {classification.musical_metadata.instruments.join(', ')}</div>
          )}
        </div>
      )}
    </div>
  );
}