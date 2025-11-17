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
  educationLevel?: string;
  difficultyLevel?: string;
  tags?: string[];
  musicalMetadata?: {
    keySignature?: string;
    timeSignature?: string;
    tempo?: string;
    instruments?: string[];
    elements?: string[];
  };
}

export interface ImageData {
  id: string;
  filename: string;
  uploadedAt: string;
  ocrText?: string | null;
  visionAnalysis?: string | null;
  fileSize: number;
  mimeType: string;
  classification?: ImageClassification | null;
}

export interface StorageInfo {
  imageCount: number;
  usageMb: number;
  limitMb: number;
  availableMb: number;
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
    lessonDocument?: LessonDocumentM2;
    [key: string]: unknown;
  };
  grade?: string;
  strand?: string;
  standard?: string;
  createdAt: string;
  updatedAt: string;
  presentationStatus?: {
    id?: string;
    presentationId?: string;
    status: PresentationStatus;
    lessonRevision?: number;
    updatedAt?: string;
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

// Presentation preview types
export interface SlidePreview {
  title: string;
  keyPoints: string[];
  estimatedDurationSeconds: number;
}

export interface PresentationPreview {
  presentationId: string;
  generatedAt: string; // ISO timestamp
  slides: SlidePreview[];
  totalEstimatedDurationSeconds: number;
  styleId?: string;
}

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
  is_default?: boolean;
}

export interface ModelAvailability {
  availableModels: ChatModel[];
  currentModel: string | null;
  processingMode: string;
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
