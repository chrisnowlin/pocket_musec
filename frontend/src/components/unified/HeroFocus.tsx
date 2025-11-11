import type { StandardRecord, SessionResponsePayload } from '../../lib/types';

interface HeroFocusProps {
  selectedStandard: StandardRecord | null;
  selectedGrade: string;
  selectedStrand: string;
  lessonDuration: string;
  classSize: string;
  session: SessionResponsePayload | null;
  sessionError: string | null;
}

export default function HeroFocus({
  selectedStandard,
  selectedGrade,
  selectedStrand,
  lessonDuration,
  classSize,
  session,
  sessionError,
}: HeroFocusProps) {
  const heroFocusTitle = selectedStandard
    ? `${selectedStandard.code} · ${selectedStandard.title}`
    : 'Guide a new lesson with PocketMusec';
  const heroFocusSubtitle =
    selectedStandard?.description ??
    'Select a standard or describe your lesson so the AI can help.';
  const heroBadges = [
    { label: selectedGrade || 'Grade level', id: 'grade' },
    { label: selectedStrand || 'Strand', id: 'strand' },
    { label: lessonDuration, id: 'duration' },
    { label: `${classSize} students`, id: 'class-size' },
  ];

  return (
    <div className="px-6 pt-6 pb-4">
      <div className="flex flex-col gap-5">
        <div className="rounded-2xl bg-gradient-to-r from-ink-700 to-ink-800 p-6 text-parchment-100 shadow-2xl overflow-hidden border border-ink-600">
          <p className="text-xs uppercase tracking-[0.4em] text-parchment-200">Current Focus</p>
          <h3 className="mt-3 text-xl font-semibold leading-tight">{heroFocusTitle}</h3>
          <p className="mt-2 text-sm text-parchment-200">{heroFocusSubtitle}</p>
          <div className="mt-4 flex flex-wrap gap-2 text-[11px]">
            {heroBadges.map((badge) => (
              <span
                key={badge.id}
                className="rounded-full border border-parchment-300/40 bg-parchment-200/20 px-3 py-1 text-parchment-100"
              >
                {badge.label}
              </span>
            ))}
          </div>
          {selectedStandard &&
            selectedStandard.learningObjectives &&
            selectedStandard.learningObjectives.length > 0 && (
              <div className="mt-6 pt-4 border-t border-parchment-200/20">
                <h4 className="text-xs font-semibold text-parchment-200 uppercase mb-3 tracking-wider">
                  Learning Objectives
                </h4>
                <ul className="space-y-2 text-sm text-parchment-200">
                  {selectedStandard.learningObjectives.map((objective, index) => (
                    <li className="flex items-start gap-2" key={index}>
                      <svg
                        className="w-4 h-4 text-parchment-100 mt-0.5 flex-shrink-0"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                      <span>{objective}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          <div className="mt-4 flex items-center gap-2 text-xs text-parchment-200">
            <span className="inline-flex h-3 w-3 rounded-full bg-parchment-100 animate-pulse" />
            <span>
              {session
                ? 'Learning session live'
                : sessionError
                ? 'Waiting on your last request'
                : 'Preparing PocketMusec AI'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
