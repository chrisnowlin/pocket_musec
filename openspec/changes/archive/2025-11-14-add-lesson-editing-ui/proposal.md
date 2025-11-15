# Add Lesson Editing UI

## Why

Teachers need to modify AI-generated lessons directly in the web interface rather than exporting to external editors. Currently, the web UI displays generated lessons but lacks inline editing capabilities, forcing teachers to save drafts and edit externally. This breaks the conversational workflow and creates friction in the lesson refinement process.

## What Changes

- Add inline lesson editor component with markdown support and preview mode
- Extend ChatMessage component with edit/save/cancel actions for AI-generated lessons
- Add lesson export functionality (Markdown, PDF, DOCX formats)
- Enhance DraftsModal with direct editing capabilities
- Implement auto-save for in-progress edits
- Add visual indicators for modified lessons and version tracking
- Integrate draft editing back into session context

## Impact

**Affected specs:**
- `web-interface` - New inline editing components and export features
- `session-management` - Enhanced draft editing and version tracking
- `lesson-generation` - Modified lessons maintain standard alignment metadata

**Affected code:**
- `frontend/src/components/unified/ChatMessage.tsx` - Add edit mode and action buttons
- `frontend/src/components/unified/LessonEditor.tsx` - New inline markdown editor (NEW)
- `frontend/src/components/unified/DraftsModal.tsx` - Add edit and export actions
- `frontend/src/components/unified/ExportModal.tsx` - New export dialog (NEW)
- `frontend/src/hooks/useDrafts.ts` - Add edit mode state management
- `frontend/src/hooks/useLessonExport.ts` - Export utilities (NEW)
- `frontend/src/lib/api.ts` - Export helper methods
- `frontend/src/pages/UnifiedPage.tsx` - Wire up editing workflow

**Breaking changes:**
- None - purely additive functionality

**Migration notes:**
- Existing drafts remain compatible
- No database schema changes required
- Export formats leverage existing backend draft API
