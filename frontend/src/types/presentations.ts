// Presentation types based on backend schema

export enum PresentationStatus {
  PENDING = 'pending',
  GENERATING = 'generating', 
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export enum SlideType {
  TITLE = 'title',
  CONTENT = 'content',
  ACTIVITY = 'activity',
  ASSESSMENT = 'assessment',
  CLOSURE = 'closure'
}

export interface PresentationSlide {
  id: string;
  slide_number: number;
  slide_type: SlideType;
  title: string;
  content: string;
  teacher_script: string;
  duration_minutes: number;
  materials_needed: string[];
  created_at: string;
  updated_at: string;
}

export interface PresentationDocument {
  id: string;
  lesson_id: string;
  title: string;
  description: string;
  total_slides: number;
  total_duration_minutes: number;
  status: PresentationStatus;
  slides: PresentationSlide[];
  created_at: string;
  updated_at: string;
  generation_started_at?: string;
  generation_completed_at?: string;
  error_message?: string;
  is_stale: boolean;
}

export interface PresentationExport {
  id: string;
  presentation_id: string;
  export_format: 'json' | 'markdown';
  file_url: string;
  file_size_bytes: number;
  created_at: string;
  expires_at: string;
}

export interface PresentationGenerationRequest {
  lesson_id: string;
  options?: {
    include_teacher_scripts?: boolean;
    include_materials?: boolean;
    slide_duration_minutes?: number;
  };
}

export interface PresentationSummary {
  id: string;
  lesson_id: string;
  title: string;
  status: PresentationStatus;
  total_slides: number;
  total_duration_minutes: number;
  created_at: string;
  updated_at: string;
  is_stale: boolean;
}

// UI-specific types
export interface PresentationViewerProps {
  presentation: PresentationDocument;
  isOpen: boolean;
  onClose: () => void;
  onExport?: (format: 'json' | 'markdown') => void;
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