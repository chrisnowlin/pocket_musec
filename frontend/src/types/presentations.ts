// Presentation types aligned with backend schema

export const PresentationStatus = {
  PENDING: 'pending',
  GENERATING: 'pending',
  COMPLETED: 'complete',
  FAILED: 'error',
  STALE: 'stale',
} as const;
export type PresentationStatus =
  (typeof PresentationStatus)[keyof typeof PresentationStatus];

export type PresentationJobStatus = 'pending' | 'running' | 'completed' | 'failed';

export type SourceSection =
  | 'overview'
  | 'objectives'
  | 'materials'
  | 'warmup'
  | 'activity'
  | 'assessment'
  | 'differentiation'
  | 'closure';

export type SlideType = 'title' | 'content' | 'activity' | 'assessment' | 'closure';

export interface PresentationSlide {
  id: string;
  order?: number;
  slideNumber?: number;
  slideType?: SlideType;
  title: string;
  subtitle?: string | null;
  content?: string;
  keyPoints?: string[];
  teacherScript: string;
  visualPrompt?: string | null;
  durationMinutes?: number | null;
  materialsNeeded?: string[];
  sourceSection?: SourceSection;
  activityId?: string | null;
  standardCodes?: string[];
}

export interface PresentationExport {
  format: 'json' | 'markdown' | 'pptx' | 'pdf';
  urlOrPath: string;
  generatedAt: string;
  fileSizeBytes?: number | null;
}

export interface PresentationSummary {
  id: string;
  presentationId?: string; // alias for convenience
  lessonId: string;
  lessonRevision: number;
  version: string;
  status: PresentationStatus;
  style: string;
  slideCount: number;
  createdAt: string;
  updatedAt: string;
  hasExports: boolean;
  errorCode?: string | null;
  errorMessage?: string | null;
  title?: string;
  description?: string;
  totalSlides?: number;
  totalDurationMinutes?: number;
  isStale?: boolean;
}

export interface PresentationDetail extends PresentationSummary {
  title?: string;
  description?: string;
  slides: PresentationSlide[];
  exportAssets: PresentationExport[];
  totalSlides?: number;
  totalDurationMinutes?: number;
  isStale?: boolean;
}

export type PresentationDocument = PresentationDetail;

export interface PresentationGenerateResponse {
  jobId: string;
  status: string;
  message: string;
}

export interface PresentationJobInfo {
  jobId: string;
  status: PresentationJobStatus;
  lessonId: string;
  createdAt: string;
  startedAt?: string | null;
  completedAt?: string | null;
  presentationId?: string | null;
  error?: string | null;
}

// UI-specific props
export interface PresentationViewerProps {
  presentation: PresentationDetail;
  isOpen: boolean;
  onClose: () => void;
  onExport?: (format: 'json' | 'markdown' | 'pptx' | 'pdf') => void;
  isExporting?: boolean;
}

export interface PresentationStatusIndicatorProps {
  status: PresentationStatus;
  className?: string;
}

export interface PresentationCTAProps {
  lessonId: string;
  presentationStatus?: PresentationStatus;
  presentationId?: string;
  onGenerate?: () => void;
  onView?: (presentationId: string) => void;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}
