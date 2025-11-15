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

  return null;
}
