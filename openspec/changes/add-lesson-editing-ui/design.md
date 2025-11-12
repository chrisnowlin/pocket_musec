# Lesson Editing UI Design

## Context

Teachers currently receive AI-generated lessons in the web interface but cannot modify them inline. The existing CLI workflow supports external editor integration, but this doesn't translate to the web UI. The backend already has full CRUD support via `/api/drafts` endpoints and the `LessonRepository.update_lesson()` method, so this change focuses purely on frontend UI/UX enhancements.

**Current state:**
- Backend: Full draft CRUD via FastAPI endpoints
- Frontend: View-only lesson display, external editing required
- CLI: System editor integration for modifications

**Constraints:**
- Must work within existing TypeScript/React/Vite stack
- No backend API changes required
- Must preserve standards alignment metadata through edits
- Should feel natural within conversational UI flow

## Goals / Non-Goals

**Goals:**
- Enable inline editing of AI-generated lessons in the web UI
- Provide export in teacher-friendly formats (Markdown, PDF, DOCX)
- Auto-save to prevent data loss
- Track modifications while preserving original generation context
- Maintain conversational workflow continuity

**Non-Goals:**
- Real-time collaborative editing (multi-user)
- Full version control with diff visualization (future enhancement)
- Complex rich text editor (WYSIWYG) - stick with markdown
- Backend API modifications
- Mobile-optimized editing experience (desktop-first)

## Decisions

### Decision 1: Inline Editing vs Separate Editor Page

**Choice:** Inline editing within ChatMessage component

**Rationale:**
- Maintains conversational flow - users don't lose context
- Faster iteration - no page navigation required
- Consistent with modern chat-based UX patterns (Discord, Slack edits)
- Simpler state management - edit mode is local to message

**Alternatives considered:**
- Separate editor page: More space but breaks flow, adds navigation complexity
- Modal editor: Similar benefits to inline but less intuitive for "edit this message"

### Decision 2: Markdown Editor Library

**Choice:** Build lightweight custom textarea with preview toggle

**Rationale:**
- Lessons are already in markdown format
- Teachers familiar with simple markdown from documentation
- Lighter bundle size than full rich text editors
- Full control over UX and keyboard shortcuts
- Easy to integrate preview using existing MarkdownRenderer

**Alternatives considered:**
- react-markdown-editor-lite: Full-featured but heavy (~200KB), adds dependency
- react-mde: Good option but still adds 100KB+ to bundle
- Monaco Editor: Overkill for lesson editing, very heavy

**Implementation details:**
- Use native textarea with monospace font option
- Add simple toolbar for common markdown (bold, italic, headers, lists)
- Debounced preview update in split view
- Keyboard shortcuts: Ctrl+S (save), Esc (cancel), Ctrl+B (bold), etc.

### Decision 3: Export Format Support

**Choice:** Support Markdown (native), PDF (browser print), DOCX (docx.js)

**Rationale:**
- **Markdown:** Already native format, zero-cost export
- **PDF:** Teachers need printable lesson plans, browser print API sufficient
- **DOCX:** Required for school submissions, docx.js is mature and well-maintained

**Alternatives considered:**
- Server-side PDF generation: Adds backend complexity, not needed with modern browser APIs
- HTML export: Less useful than PDF, teachers need print-ready format
- Google Docs integration: Over-engineering, requires auth/permissions

**Implementation details:**
- Markdown: Direct download with frontmatter metadata
- PDF: Use window.print() with custom CSS for print media
- DOCX: docx.js library (~100KB gzipped, worth it for Word compatibility)

### Decision 4: Auto-Save Strategy

**Choice:** Debounced auto-save (30s interval + 2s typing pause)

**Rationale:**
- Prevents data loss during editing sessions
- 30-second interval balances safety vs API call frequency
- 2-second typing pause prevents save-while-typing interruptions
- Proven pattern from Google Docs, Notion, etc.

**Alternatives considered:**
- No auto-save: Risky, teachers might lose work
- Very frequent auto-save (every keystroke): Too many API calls, potential UX jank
- Only save on navigation: Misses browser crashes, power loss

**Implementation details:**
- Use debounce from lodash or custom implementation
- Store in IndexedDB immediately on browser
- Sync to backend API after debounce
- Show "Saving..." and "Saved" indicators
- Recover unsaved changes on page refresh

### Decision 5: Version Tracking Approach

**Choice:** Simple modification tracking (original + current only)

**Rationale:**
- Sufficient for teacher needs - "what did I change?"
- Keeps storage requirements minimal
- Easy to understand UI (modified badge, view original option)
- Can upgrade to full versioning later if needed

**Alternatives considered:**
- Full version history with diffs: Complex UI, storage overhead, rarely needed
- No version tracking: Loses valuable context about modifications
- Server-side version control: Backend changes, over-engineering

**Implementation details:**
- Store `original_content` in draft metadata on first edit
- Track `modified_at` timestamp
- Show "Modified" badge on edited lessons
- Optional "View Original" action in lesson menu
- Keep metadata (grade, strand, standards) from original generation

### Decision 6: Edit State Management

**Choice:** Local component state + useDrafts hook for persistence

**Rationale:**
- Edit mode is transient UI state - no need for global state
- useDrafts hook already manages draft lifecycle
- Keeps components simple and testable
- Prevents edit conflicts by tracking editingDraftId

**Alternatives considered:**
- Zustand global store: Over-engineering for local UI state
- Context API: Adds unnecessary provider complexity
- Pure local state: Works but misses cross-component coordination

**Implementation details:**
- ChatMessage: local `isEditing` state
- useDrafts: `editingDraftId` + `setEditMode()` for conflict prevention
- IndexedDB: persistence layer for auto-save recovery

## Risks / Trade-offs

### Risk 1: Large Lesson Content Performance

**Risk:** Editing very long lessons (5000+ words) could be slow in textarea

**Mitigation:**
- Start with standard textarea, measure performance
- If needed, virtualize rendering or switch to Monaco (lazy loaded)
- Lessons typically <2000 words based on existing generations

**Impact:** Low - typical lessons are well within performance limits

### Risk 2: Export Format Compatibility

**Risk:** Generated DOCX files may not render perfectly in all Word versions

**Mitigation:**
- Test with Word 2016, 2019, Office 365, LibreOffice
- Use conservative DOCX features (avoid complex formatting)
- Provide Markdown export as fallback
- Document known limitations

**Impact:** Medium - Word compatibility is important but Markdown fallback exists

### Risk 3: Auto-Save Conflicts

**Risk:** Multiple tabs editing same draft could create conflicts

**Mitigation:**
- Track `editingDraftId` in session storage
- Use BroadcastChannel API to coordinate across tabs
- Show read-only warning in tabs where edit is already active
- Last-write-wins conflict resolution if both tabs save

**Impact:** Low - teachers rarely edit same lesson in multiple tabs

### Risk 4: Metadata Loss on Export

**Risk:** Standards alignment metadata might be lost in export formats

**Mitigation:**
- Include metadata as frontmatter (Markdown)
- Add metadata page/header (PDF)
- Use DOCX document properties (DOCX)
- Always preserve metadata in backend draft record

**Impact:** Low - multiple safeguards in place

## Migration Plan

**Phase 1: Core Editing (Week 1-2)**
1. Implement LessonEditor component
2. Add edit mode to ChatMessage
3. Integrate with existing useDrafts hook
4. Deploy and gather teacher feedback

**Phase 2: Export Features (Week 3)**
1. Add export modal and format selection
2. Implement Markdown export
3. Implement PDF export (print API)
4. Implement DOCX export (docx.js)
5. Test format compatibility

**Phase 3: Polish & Testing (Week 4)**
1. Add auto-save with indicators
2. Implement version tracking
3. Comprehensive testing (unit, integration, e2e)
4. Accessibility audit
5. Documentation updates

**Rollback strategy:**
- Feature flags for new editing UI (enable per user)
- Keep existing view-only mode as fallback
- Backend API unchanged, so no migration needed
- Can disable export formats independently if issues arise

**No database migration required** - all changes are frontend-only, leveraging existing `/api/drafts` endpoints.

## Open Questions

1. **Character limits for lessons?**
   - Current: No enforced limit
   - Recommendation: Add soft warning at 5000 words, hard limit at 10000
   - Decision needed from product team

2. **Should we support draft sharing/collaboration in future?**
   - Out of scope for this change
   - Would require backend changes (sharing permissions, user management)
   - Flag as potential future enhancement

3. **Export format preferences - save per user or per session?**
   - Decision: Per session for now (simpler)
   - Can upgrade to user preferences with backend support later

4. **Mobile editing experience?**
   - Explicitly out of scope (desktop-first)
   - Touch-friendly UI on tablets should work but not optimized
   - Full mobile optimization is separate future work
