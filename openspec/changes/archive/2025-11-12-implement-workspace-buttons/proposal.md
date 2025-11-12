# Change Proposal: Implement Workspace Button Functionality

**Change ID**: `implement-workspace-buttons`  
**Status**: DRAFT  
**Created**: 2025-11-11  
**Author**: AI Assistant

## Why

During frontend UI testing, several buttons in the workspace interface were identified as non-functional:

1. **Retry Button** (Session Pulse): Displays "Retry" when session errors occur but clicking it does nothing
2. **Templates Button** (Quick Access): Button becomes active but shows no content
3. **Saved Drafts Button** (Quick Access): Button becomes active but shows no content  
4. **Conversation History Buttons** (Sidebar): Buttons become active but don't load conversation content

These buttons provide visual affordances that suggest functionality, but clicking them produces no result. This creates a poor user experience where users expect features that don't work. Implementing these buttons will:

- Improve user trust by making UI elements functional
- Enable users to retry failed operations
- Provide access to saved templates and drafts
- Allow users to resume previous conversations

Currently, users cannot:
- Recover from session errors without refreshing the page
- Access any saved lesson templates
- View or manage saved drafts
- Resume previous conversation sessions

## What Changes

Implement functionality for four button groups:

1. **Session Retry Functionality**
   - Add retry logic to Session Pulse "Retry" button
   - Re-initialize session when clicked during error state
   - Show loading state during retry attempt
   - Display success/error feedback

2. **Templates Management**
   - Create templates view/modal when Templates button is clicked
   - Display list of saved lesson templates
   - Allow users to create new templates from existing lessons
   - Enable template selection to start new lessons with template structure

3. **Drafts Management**
   - Create drafts view/modal when Saved Drafts button is clicked
   - Display list of saved lesson drafts with metadata (title, date, grade, strand)
   - Allow users to open, edit, delete, or continue working on drafts
   - Show draft count in button hint

4. **Conversation History Loading**
   - Load conversation data when history buttons are clicked
   - Restore chat messages and session state
   - Update UI to show selected conversation as active
   - Display conversation content in chat panel

**BREAKING**: None - this is additive functionality

## Impact

### Affected Specs
- **MODIFIED**: `workspace-shell` - Add requirements for button functionality, templates, drafts, and conversation history

### Affected Code
- **Modified files**:
  - `frontend/src/components/unified/RightPanel.tsx` - Add retry button handler
  - `frontend/src/components/unified/Sidebar.tsx` - Add click handlers for Templates, Drafts, and conversation history
  - `frontend/src/hooks/useSession.ts` - Add retry session method
  - `frontend/src/pages/UnifiedPage.tsx` - Add state management for templates, drafts, and conversation loading

- **New files**:
  - `frontend/src/components/unified/TemplatesModal.tsx` - Templates management UI
  - `frontend/src/components/unified/DraftsModal.tsx` - Drafts management UI
  - `frontend/src/hooks/useTemplates.ts` - Template management logic
  - `frontend/src/hooks/useDrafts.ts` - Draft management logic
  - `backend/api/routes/templates.py` - Templates API endpoints (if backend storage needed)
  - `backend/api/routes/drafts.py` - Drafts API endpoints (if backend storage needed)
  - `backend/repositories/template_repository.py` - Template database operations
  - `backend/repositories/draft_repository.py` - Draft database operations

### Database Changes
- **New tables** (if storing templates/drafts in database):
  - `templates` - Store lesson templates
  - `drafts` - Store lesson drafts
  - Migration to create these tables

## Technical Decisions

### Templates Storage
- **Option 1**: Store in browser localStorage (simple, no backend)
- **Option 2**: Store in database (persistent, shareable)
- **Decision**: Start with localStorage for v1 (simpler), migrate to database if needed for persistence across devices

### Drafts Storage
- **Option 1**: Use existing `lessons` table with `is_draft` flag
- **Option 2**: Separate `drafts` table
- **Decision**: Use existing `lessons` table with `is_draft` boolean flag to avoid duplication

### Conversation History
- **Option 1**: Load from existing `sessions` table
- **Option 2**: Store conversation messages separately
- **Decision**: Load from `sessions` table and restore session state; messages can be regenerated or stored in session metadata

### Retry Implementation
- **Option 1**: Simple re-initialization of session
- **Option 2**: Exponential backoff with retry limits
- **Decision**: Start with simple re-initialization; add backoff if needed

## Implementation Phases

### Phase 1: Session Retry (Priority: High)
- Add retry handler to RightPanel
- Implement `retrySession` method in useSession hook
- Add loading state during retry
- Test error recovery

### Phase 2: Conversation History (Priority: High)
- Load sessions list on sidebar mount
- Add click handler to conversation buttons
- Implement session restoration logic
- Load and display conversation messages

### Phase 3: Drafts Management (Priority: Medium)
- Create DraftsModal component
- Implement useDrafts hook
- Add API endpoints for draft operations (if using database)
- Add draft creation/editing/deletion

### Phase 4: Templates Management (Priority: Medium)
- Create TemplatesModal component
- Implement useTemplates hook
- Add template creation from lessons
- Add template selection for new lessons

## Dependencies

### Required
- Existing session management (`useSession` hook)
- Existing API client (`api.ts`)
- Existing database schema (sessions, lessons tables)

### New Dependencies
- None (using existing React patterns and API structure)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Templates/drafts data loss with localStorage | Medium | Add export/import functionality; migrate to database in future |
| Performance issues loading many conversations | Low | Implement pagination; lazy load conversation content |
| Session restoration complexity | Medium | Start simple; restore basic state first, add message history later |
| UI clutter with new modals | Low | Use existing modal patterns; keep UI consistent |

## Open Questions

1. **Templates scope**: Should templates include full lesson content or just structure/metadata?
2. **Draft auto-save**: Should drafts auto-save during editing or require explicit save?
3. **Conversation message storage**: Should we store full message history or regenerate on load?
4. **Template sharing**: Should templates be shareable between users (future consideration)?

## Success Criteria

- [ ] Retry button successfully re-initializes session when clicked during error state
- [ ] Templates button opens modal showing saved templates
- [ ] Users can create templates from existing lessons
- [ ] Users can select templates to start new lessons
- [ ] Drafts button opens modal showing saved drafts
- [ ] Users can open, edit, and delete drafts
- [ ] Conversation history buttons load and display conversation content
- [ ] Selected conversation shows as active in sidebar
- [ ] All buttons provide visual feedback (loading states, success/error messages)
- [ ] No regressions in existing functionality

## Related Changes

- Complements: `implement-milestone2-web-interface` (uses existing UI structure)
- Complements: `implement-milestone3-advanced-features` (extends workspace functionality)
- Future: May enable `add-template-sharing` or `add-draft-collaboration` features

