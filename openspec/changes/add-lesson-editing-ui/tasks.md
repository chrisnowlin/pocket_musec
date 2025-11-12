# Implementation Tasks

## 1. Core Editing Components

- [ ] 1.1 Create LessonEditor component (`frontend/src/components/unified/LessonEditor.tsx`)
  - Markdown textarea with syntax highlighting
  - Preview toggle (split view mode)
  - Character/word count display
  - Keyboard shortcuts (Ctrl+S, Esc)
  - Validation: Editor loads, displays content, allows editing, shows preview

- [ ] 1.2 Extend ChatMessage component with edit mode (`frontend/src/components/unified/ChatMessage.tsx`)
  - Add edit/save/cancel buttons on hover for AI messages
  - Track edit mode state (view/edit)
  - Integrate LessonEditor when in edit mode
  - Show "modified" visual indicator
  - Validation: Edit button appears, switches to edit mode, saves changes, cancels properly

- [ ] 1.3 Add edit mode state management to useDrafts hook (`frontend/src/hooks/useDrafts.ts`)
  - Add `editingDraftId` state
  - Add `setEditMode()` function
  - Add `saveEditedLesson()` function
  - Handle optimistic UI updates
  - Validation: State updates correctly, API calls work, UI reflects changes

## 2. Export Functionality

- [ ] 2.1 Create ExportModal component (`frontend/src/components/unified/ExportModal.tsx`)
  - Format selector (Markdown, PDF, DOCX)
  - Export preview
  - Download triggers
  - Metadata inclusion options
  - Validation: Modal opens, format selection works, exports download correctly

- [ ] 2.2 Create useLessonExport hook (`frontend/src/hooks/useLessonExport.ts`)
  - Export as Markdown (direct download)
  - Export as PDF (browser print API or jsPDF)
  - Export as DOCX (using docx.js library)
  - Include metadata in exports
  - Validation: Each format exports correctly with proper formatting and metadata

- [ ] 2.3 Add export helper methods to API client (`frontend/src/lib/api.ts`)
  - Format lesson content for export
  - Generate filenames with metadata
  - Handle download triggers
  - Validation: Helper methods work correctly, filenames are generated properly

## 3. Enhanced Draft Management

- [ ] 3.1 Extend DraftsModal with edit and export actions (`frontend/src/components/unified/DraftsModal.tsx`)
  - Add "Edit" button alongside "Open" and "Delete"
  - Add "Export" button with format selector
  - Add preview pane for quick viewing
  - Add search/filter by grade/strand
  - Validation: All new buttons work, preview shows correctly, filtering works

- [ ] 3.2 Integrate draft editing into UnifiedPage (`frontend/src/pages/UnifiedPage.tsx`)
  - Wire up handleEditDraft function
  - Load draft into chat in edit mode
  - Link edited lessons back to session context
  - Preserve conversation history when editing
  - Validation: Draft editing flow works end-to-end, session context preserved

## 4. Auto-Save Functionality

- [ ] 4.1 Implement auto-save logic in LessonEditor
  - Debounced auto-save every 30 seconds
  - Save on navigation away
  - Wait for 2-second pause in typing
  - Show last save time indicator
  - Validation: Auto-save triggers correctly, doesn't interrupt typing, indicator updates

- [ ] 4.2 Add auto-save state to session management
  - Track unsaved changes in IndexedDB
  - Recover on browser refresh
  - Prevent data loss
  - Validation: Refresh recovers unsaved work, no data loss occurs

## 5. Version Tracking and Metadata

- [ ] 5.1 Add modification tracking to draft metadata
  - Store original content separately
  - Track modification timestamp
  - Mark lessons as "modified" in UI
  - Preserve original generation parameters
  - Validation: Metadata updates correctly, original preserved, UI shows badges

- [ ] 5.2 Implement version comparison UI (optional enhancement)
  - Show original vs modified view
  - Highlight changes (future enhancement)
  - Validation: Can view original, comparison visible

## 6. Testing and Validation

- [ ] 6.1 Write component tests for LessonEditor
  - Test edit mode entry/exit
  - Test save/cancel actions
  - Test keyboard shortcuts
  - Test preview mode
  - Validation: All tests pass with >80% coverage

- [ ] 6.2 Write component tests for enhanced ChatMessage
  - Test edit button visibility
  - Test edit mode transitions
  - Test save/cancel flows
  - Validation: All tests pass

- [ ] 6.3 Write hook tests for useDrafts and useLessonExport
  - Test state management
  - Test API integration
  - Test export functionality
  - Validation: All tests pass

- [ ] 6.4 Write integration tests for edit workflow
  - End-to-end edit flow
  - Export from drafted lesson
  - Auto-save recovery
  - Validation: Full user workflows work correctly

## 7. Documentation and Polish

- [ ] 7.1 Update user documentation
  - Add lesson editing guide to docs
  - Document export formats and features
  - Add screenshots/examples
  - Validation: Documentation is clear and complete

- [ ] 7.2 Add accessibility features
  - Keyboard navigation for all controls
  - ARIA labels for screen readers
  - Focus management in modals
  - Validation: Passes accessibility audit

- [ ] 7.3 Performance optimization
  - Lazy load editor component
  - Optimize markdown rendering
  - Debounce auto-save properly
  - Validation: No performance regressions, fast loading

- [ ] 7.4 Error handling and edge cases
  - Handle export failures gracefully
  - Prevent concurrent edit conflicts
  - Validate content before save
  - Validation: Error states handled properly, user informed

## Dependencies and Parallelization

**Can work in parallel:**
- Tasks 1.1, 2.1, 2.2 (independent components and hooks)
- Tasks 6.1, 6.2, 6.3 (independent test suites)

**Must be sequential:**
- 1.1 → 1.2 (ChatMessage depends on LessonEditor)
- 1.2 → 1.3 (useDrafts extends ChatMessage functionality)
- 2.1, 2.2 → 3.1 (DraftsModal uses export components)
- All of 1-3 → 3.2 (UnifiedPage integrates everything)
- All implementation → Testing (6.x)
- All implementation → Documentation (7.x)

**Critical path:**
1. LessonEditor (1.1)
2. ChatMessage edit mode (1.2)
3. useDrafts state management (1.3)
4. Export functionality (2.x)
5. Integration (3.2)
6. Testing (6.x)
