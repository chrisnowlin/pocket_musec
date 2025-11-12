import type { StandardRecord } from '../lib/types';

export type PanelSide = 'sidebar' | 'right';
export type ChatSender = 'user' | 'ai';
export type ViewMode = 'chat' | 'browse' | 'ingestion' | 'images' | 'settings';

export interface ChatMessage {
  id: string;
  sender: ChatSender;
  text: string;
  timestamp: string;
}

export interface ImageData {
  id: string;
  filename: string;
  uploaded_at: string;
  ocr_text?: string | null;
  vision_analysis?: string | null;
  file_size: number;
  mime_type: string;
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

export interface DraftItem {
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

export interface TemplateItem {
  id: string;
  name: string;
  description: string;
  content: string;
  grade: string;
  strand: string;
  standardId?: string;
  standardCode?: string;
  standardTitle?: string;
  objective?: string;
  lessonDuration?: string;
  classSize?: string;
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
}

export interface TemplatesModalProps {
  isOpen: boolean;
  onClose: () => void;
  templates: TemplateItem[];
  isLoading: boolean;
  onSelectTemplate: (templateId: string) => void;
  onDeleteTemplate: (templateId: string) => void;
}

// Grouped state interfaces for better organization
export interface UIState {
  mode: ViewMode;
  imageModalOpen: boolean;
}

export interface ChatState {
  input: string;
}

export interface LessonSettings {
  selectedStandard: StandardRecord | null;
  selectedGrade: string;
  selectedStrand: string;
  selectedObjective: string | null;
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
  selectedStandard: StandardRecord | null;
  selectedGrade: string;
  selectedStrand: string;
  selectedObjective: string | null;
  lessonContext: string;
  lessonDuration: string;
  classSize: string;
  browseQuery: string;
}
