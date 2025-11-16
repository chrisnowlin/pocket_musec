import type { StandardRecord, LessonDocumentM2 } from '../lib/types';

export type PanelSide = 'sidebar' | 'right';
export type ChatSender = 'user' | 'ai';
export type ViewMode = 'chat' | 'browse' | 'ingestion' | 'images' | 'settings' | 'embeddings';

export interface ChatMessage {
  id: string;
  sender: ChatSender;
  text: string;
  timestamp: string;
  isModified?: boolean;
  originalText?: string;
  citations?: string[];
  lessonId?: string;
}

export interface ImageClassification {
  category: string;
  confidence: number;
  education_level?: string;
  difficulty_level?: string;
  tags?: string[];
  musical_metadata?: {
    key_signature?: string;
    time_signature?: string;
    tempo?: string;
    instruments?: string[];
    elements?: string[];
  };
}

export interface ImageData {
  id: string;
  filename: string;
  uploaded_at: string;
  ocr_text?: string | null;
  vision_analysis?: string | null;
  file_size: number;
  mime_type: string;
  classification?: ImageClassification | null;
}

export interface StorageInfo {
  image_count: number;
  usage_mb: number;
  limit_mb: number;
  available_mb: number;
  percentage: number;
}

export interface ConversationGroup {
  label: string;
  items: ConversationItem[];
}

export interface ConversationItem {
  id: string;
  title: string;
  hint: string;
  active: boolean;
  grade?: string;
  strand?: string;
  standard?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface QuickAccessLink {
  label: string;
  hint: string;
}

export interface QuickStats {
  lessonsCreated: number;
  activeDrafts: number;
}

import type { PresentationStatus } from './presentations';

export interface DraftItem {
  id: string;
  title: string;
  content: string;
  originalContent?: string;
  metadata?: {
    lesson_document?: LessonDocumentM2;
    [key: string]: unknown;
  };
  grade?: string;
  strand?: string;
  standard?: string;
  createdAt: string;
  updatedAt: string;
  presentation_status?: {
    id?: string;
    presentation_id?: string;
    status: PresentationStatus;
    lesson_revision?: number;
    updated_at?: string;
  };
}

export interface LessonItem {
  id: string;
  title: string;
  content: string;
  metadata?: Record<string, unknown>;
  grade?: string;
  strand?: string;
  standard?: string;
  createdAt: string;
  updatedAt: string;
}

export interface DraftsModalProps {
  isOpen: boolean;
  onClose: () => void;
  drafts: DraftItem[];
  isLoading: boolean;
  onOpenDraft: (draftId: string) => void;
  onDeleteDraft: (draftId: string) => void;
  onEditDraft?: (draftId: string) => void;
  onUpdateDraft?: (draftId: string, updates: { title?: string; content?: string; metadata?: Record<string, unknown> }) => Promise<DraftItem | null>;
}

export type ExportFormat = 'markdown' | 'pdf' | 'docx';

export interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  draft: DraftItem | null;
  onExport: (format: ExportFormat) => void;
  isLoading: boolean;
}

export interface LessonEditorProps {
  content: string;
  onSave: (content: string) => Promise<void>;
  onCancel: () => void;
  autoSave?: boolean;
}

export type EditorMode = 'edit' | 'preview' | 'split';
export type SaveStatus = 'saved' | 'saving' | 'unsaved' | 'error';

// Grouped state interfaces for better organization
export interface UIState {
  mode: ViewMode;
  imageModalOpen: boolean;
}

export interface ChatState {
  input: string;
}

export interface LessonSettings {
  selectedStandards: StandardRecord[];
  selectedGrade: string;
  selectedStrand: string;
  selectedObjectives: string[];
  lessonContext: string;
  lessonDuration: string;
  classSize: string;
}

export interface BrowseState {
  query: string;
}

export interface SettingsState {
  processingMode: string;
}

export interface ChatModel {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  available: boolean;
  recommended?: boolean;
}

export interface ModelAvailability {
  available_models: ChatModel[];
  current_model: string | null;
  processing_mode: string;
}

export interface UnifiedPageState {
  ui: UIState;
  chat: ChatState;
  lessonSettings: LessonSettings;
  browse: BrowseState;
  settings: SettingsState;
}

// Legacy interface for backward compatibility
export interface LegacyUnifiedPageState {
  mode: ViewMode;
  messages: ChatMessage[];
  chatInput: string;
  isTyping: boolean;
  selectedStandards: StandardRecord[];
  selectedGrade: string;
  selectedStrand: string;
  selectedObjectives: string[];
  lessonContext: string;
  lessonDuration: string;
  classSize: string;
  browseQuery: string;
}
