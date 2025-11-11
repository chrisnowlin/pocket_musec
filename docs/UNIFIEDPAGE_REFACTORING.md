# UnifiedPage Refactoring Guide

## Overview

The `UnifiedPage.tsx` file has grown to 1630 lines and needs to be broken down into smaller, more manageable components. This document outlines the refactoring strategy.

## Completed Work

### ✅ 1. Types & Constants Extracted

**Files Created:**
- `frontend/src/types/unified.ts` - All TypeScript interfaces and types
- `frontend/src/constants/unified.ts` - Static data (grades, strands, standards, etc.)

### ✅ 2. Custom Hooks Created

**Files Created:**
- `frontend/src/hooks/useChat.ts` - Chat message handling and streaming (140 lines)
- `frontend/src/hooks/useSession.ts` - Session and standards management (65 lines)
- `frontend/src/hooks/useImages.ts` - Image upload/management (140 lines)
- `frontend/src/hooks/useResizing.ts` - Panel resizing logic (100 lines)

### ✅ 3. Initial Components Created

**Files Created:**
- `frontend/src/components/unified/ChatMessage.tsx` - Individual chat message display
- `frontend/src/components/unified/ChatInput.tsx` - Chat input with error handling

## Remaining Components to Create

### High Priority Components

#### 1. HeroFocus.tsx (~100 lines)
**Purpose:** Display current standard focus banner with learning objectives

**Props:**
```typescript
interface HeroFocusProps {
  selectedStandard: StandardRecord | null;
  selectedGrade: string;
  selectedStrand: string;
  lessonDuration: string;
  classSize: string;
  session: SessionResponsePayload | null;
  sessionError: string | null;
}
```

**Extract:** Lines 691-734 from UnifiedPage.tsx

---

#### 2. ChatPanel.tsx (~150 lines)
**Purpose:** Main chat interface with message list and input

**Props:**
```typescript
interface ChatPanelProps {
  messages: ChatMessage[];
  isTyping: boolean;
  chatInput: string;
  setChatInput: (value: string) => void;
  onSendMessage: () => void;
  sessionError: string | null;
  chatError: string | null;
  messageContainerHeight: number | null;
  onResizerMouseDown: (event: ReactMouseEvent<HTMLDivElement>, ref: RefObject<HTMLDivElement>) => void;
  resizing: boolean;
}
```

**Extract:** Lines 740-868 from UnifiedPage.tsx

---

#### 3. Sidebar.tsx (~180 lines)
**Purpose:** Left sidebar with navigation and conversation history

**Props:**
```typescript
interface SidebarProps {
  width: number;
  mode: ViewMode;
  onModeChange: (mode: ViewMode) => void;
  onNewConversation: () => void;
  onUploadDocuments: () => void;
  onUploadImages: () => void;
  onOpenSettings: () => void;
}
```

**Extract:** Lines 550-681 from UnifiedPage.tsx

---

#### 4. RightPanel.tsx (~200 lines)
**Purpose:** Right panel with context, configuration, and stats

**Props:**
```typescript
interface RightPanelProps {
  width: number;
  selectedGrade: string;
  selectedStrand: string;
  selectedStandard: StandardRecord | null;
  selectedObjective: string | null;
  lessonContext: string;
  lessonDuration: string;
  classSize: string;
  standards: StandardRecord[];
  session: SessionResponsePayload | null;
  sessionError: string | null;
  mode: ViewMode;
  messageCount: number;
  imageCount: number;
  onGradeChange: (grade: string) => void;
  onStrandChange: (strand: string) => void;
  onStandardChange: (standard: StandardRecord | null) => void;
  onObjectiveChange: (objective: string | null) => void;
  onLessonContextChange: (context: string) => void;
  onLessonDurationChange: (duration: string) => void;
  onClassSizeChange: (size: string) => void;
  onBrowseStandards: () => void;
}
```

**Extract:** Lines 1277-1476 from UnifiedPage.tsx

---

### Medium Priority Components

#### 5. BrowsePanel.tsx (~120 lines)
**Purpose:** Standards browsing and filtering interface

**Props:**
```typescript
interface BrowsePanelProps {
  standards: StandardRecord[];
  selectedGrade: string;
  selectedStrand: string;
  selectedStandard: StandardRecord | null;
  browseQuery: string;
  onGradeChange: (grade: string) => void;
  onStrandChange: (strand: string) => void;
  onStandardSelect: (standard: StandardRecord) => void;
  onBrowseQueryChange: (query: string) => void;
  onStartChat: (standard: StandardRecord, prompt: string) => void;
}
```

**Extract:** Lines 871-987 from UnifiedPage.tsx

---

#### 6. ImagePanel.tsx (~160 lines)
**Purpose:** Image upload and management interface

**Props:**
```typescript
interface ImagePanelProps {
  images: ImageData[];
  storageInfo: StorageInfo | null;
  selectedImage: ImageData | null;
  isUploading: boolean;
  uploadProgress: number;
  uploadError: string | null;
  imageDragActive: boolean;
  onImageSelect: (image: ImageData) => void;
  onFileSelect: (event: ChangeEvent<HTMLInputElement>) => void;
  onDrop: (event: DragEvent<HTMLDivElement>) => void;
  onDeleteImage: (id: string) => void;
  onDragOver: (active: boolean) => void;
  fileInputRef: RefObject<HTMLInputElement>;
}
```

**Extract:** Lines 1006-1147 from UnifiedPage.tsx

---

#### 7. SettingsPanel.tsx (~120 lines)
**Purpose:** Settings and system status display

**Props:**
```typescript
interface SettingsPanelProps {
  processingMode: string;
  onProcessingModeChange: (mode: string) => void;
}
```

**Extract:** Lines 1149-1266 from UnifiedPage.tsx

---

#### 8. ImageUploadModal.tsx (~90 lines)
**Purpose:** Modal for uploading images

**Props:**
```typescript
interface ImageUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  isUploading: boolean;
  uploadProgress: number;
  uploadError: string | null;
  imageDragActive: boolean;
  onDrop: (event: DragEvent<HTMLDivElement>) => void;
  onDragOver: (active: boolean) => void;
  onFileSelect: (event: ChangeEvent<HTMLInputElement>) => void;
  fileInputRef: RefObject<HTMLInputElement>;
}
```

**Extract:** Lines 1480-1572 from UnifiedPage.tsx

---

#### 9. ImageDetailModal.tsx (~60 lines)
**Purpose:** Modal for viewing image details

**Props:**
```typescript
interface ImageDetailModalProps {
  image: ImageData | null;
  onClose: () => void;
  onDelete: (id: string) => void;
}
```

**Extract:** Lines 1575-1627 from UnifiedPage.tsx

---

## Refactored UnifiedPage.tsx Structure

After refactoring, the main `UnifiedPage.tsx` should be approximately 200-250 lines:

```typescript
import { useState } from 'react';
import { useChat } from '../hooks/useChat';
import { useSession } from '../hooks/useSession';
import { useImages } from '../hooks/useImages';
import { useResizing, useMessageContainerResizing } from '../hooks/useResizing';
import Sidebar from '../components/unified/Sidebar';
import HeroFocus from '../components/unified/HeroFocus';
import ChatPanel from '../components/unified/ChatPanel';
import BrowsePanel from '../components/unified/BrowsePanel';
import ImagePanel from '../components/unified/ImagePanel';
import SettingsPanel from '../components/unified/SettingsPanel';
import RightPanel from '../components/unified/RightPanel';
import ImageUploadModal from '../components/unified/ImageUploadModal';
import ImageDetailModal from '../components/unified/ImageDetailModal';
import type { ViewMode } from '../types/unified';

export default function UnifiedPage() {
  // View state
  const [mode, setMode] = useState<ViewMode>('chat');
  
  // Custom hooks
  const { session, sessionError, standards, setSession } = useSession();
  const {
    messages,
    isTyping,
    chatError,
    appendMessage,
    processChatMessage,
    resetMessages,
  } = useChat({ session, lessonDuration, classSize });
  
  const imageHooks = useImages();
  const { sidebarWidth, rightPanelWidth, resizingPanel, handleResizerMouseDown } = 
    useResizing(256, 384);
  
  // Selection state
  const [selectedStandard, setSelectedStandard] = useState<StandardRecord | null>(null);
  const [selectedGrade, setSelectedGrade] = useState('Grade 3');
  const [selectedStrand, setSelectedStrand] = useState('Connect');
  // ... other state
  
  return (
    <div className="flex h-screen">
      <Sidebar
        width={sidebarWidth}
        mode={mode}
        onModeChange={setMode}
        // ... other props
      />
      
      <div className={`resizer ${resizingPanel === 'sidebar' ? 'resizing' : ''}`}
        onMouseDown={(e) => handleResizerMouseDown('sidebar', e)}
      />
      
      <section className="flex-1 flex flex-col panel workspace-panel-glass">
        <HeroFocus
          selectedStandard={selectedStandard}
          selectedGrade={selectedGrade}
          // ... other props
        />
        
        <div className="flex-1 overflow-hidden">
          {mode === 'chat' && <ChatPanel /* props */ />}
          {mode === 'browse' && <BrowsePanel /* props */ />}
          {mode === 'ingestion' && <DocumentIngestion /* props */ />}
          {mode === 'images' && <ImagePanel /* props */ />}
          {mode === 'settings' && <SettingsPanel /* props */ />}
        </div>
      </section>
      
      <div className={`resizer ${resizingPanel === 'right' ? 'resizing' : ''}`}
        onMouseDown={(e) => handleResizerMouseDown('right', e)}
      />
      
      <RightPanel
        width={rightPanelWidth}
        // ... other props
      />
      
      <ImageUploadModal /* props */ />
      <ImageDetailModal /* props */ />
    </div>
  );
}
```

## File Organization Summary

```
frontend/src/
├── types/
│   └── unified.ts              (60 lines)
├── constants/
│   └── unified.ts              (90 lines)
├── hooks/
│   ├── useChat.ts              (140 lines)
│   ├── useSession.ts           (65 lines)
│   ├── useImages.ts            (140 lines)
│   └── useResizing.ts          (100 lines)
├── components/
│   └── unified/
│       ├── ChatMessage.tsx     (65 lines) ✅
│       ├── ChatInput.tsx       (75 lines) ✅
│       ├── HeroFocus.tsx       (100 lines)
│       ├── ChatPanel.tsx       (150 lines)
│       ├── Sidebar.tsx         (180 lines)
│       ├── RightPanel.tsx      (200 lines)
│       ├── BrowsePanel.tsx     (120 lines)
│       ├── ImagePanel.tsx      (160 lines)
│       ├── SettingsPanel.tsx   (120 lines)
│       ├── ImageUploadModal.tsx (90 lines)
│       └── ImageDetailModal.tsx (60 lines)
└── pages/
    └── UnifiedPage.tsx         (250 lines - refactored)
```

**Total:** ~2,000 lines across 17 files (vs. 1,630 in one file)

## Benefits

1. **Maintainability:** Each component has a single responsibility
2. **Reusability:** Components can be reused in other contexts
3. **Testability:** Smaller components are easier to test
4. **Performance:** Can optimize individual components with React.memo
5. **Collaboration:** Multiple developers can work on different components
6. **Code Navigation:** Easier to find and understand specific functionality

## Next Steps

1. Create remaining component files following the structure above
2. Test each component in isolation
3. Gradually migrate UnifiedPage.tsx to use the new components
4. Add unit tests for hooks and components
5. Document component APIs with JSDoc comments

## Migration Strategy

To avoid breaking the application:

1. Create all component files first
2. Import components one at a time into UnifiedPage.tsx
3. Test after each component integration
4. Keep the old code commented out until fully verified
5. Remove old code once all components are integrated and tested
