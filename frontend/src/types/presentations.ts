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
  slide_number?: number;
  slide_type?: SlideType;
  title: string;
  subtitle?: string | null;
  content?: string;
  key_points?: string[];
  teacher_script: string;
  visual_prompt?: string | null;
  duration_minutes?: number | null;
  materials_needed?: string[];
  source_section?: SourceSection;
  activity_id?: string | null;
  standard_codes?: string[];
}

export interface PresentationExport {
  format: 'json' | 'markdown' | 'pptx' | 'pdf';
  url_or_path: string;
  generated_at: string;
  file_size_bytes?: number | null;
}

export interface PresentationSummary {
  id: string;
  presentation_id?: string; // alias for convenience
  lesson_id: string;
  lesson_revision: number;
  version: string;
  status: PresentationStatus;
  style: string;
  slide_count: number;
  created_at: string;
  updated_at: string;
  has_exports: boolean;
  error_code?: string | null;
  error_message?: string | null;
  title?: string;
  description?: string;
  total_slides?: number;
  total_duration_minutes?: number;
  is_stale?: boolean;
}

export interface PresentationDetail extends PresentationSummary {
  title?: string;
  description?: string;
  slides: PresentationSlide[];
  export_assets: PresentationExport[];
  total_slides?: number;
  total_duration_minutes?: number;
  is_stale?: boolean;
}

export type PresentationDocument = PresentationDetail;

export interface PresentationGenerateResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface PresentationJobInfo {
  job_id: string;
  status: PresentationJobStatus;
  lesson_id: string;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  presentation_id?: string | null;
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
