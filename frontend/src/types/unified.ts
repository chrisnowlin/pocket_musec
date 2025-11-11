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
  title: string;
  hint: string;
  active: boolean;
}

export interface QuickAccessLink {
  label: string;
  hint: string;
}

export interface QuickStats {
  lessonsCreated: number;
  activeDrafts: number;
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
