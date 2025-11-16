# Proposal: Promote Draft to Lesson

## Why

Teachers need a clear workflow to transition draft lessons to permanent, reusable lesson plans. Currently, drafts are indistinguishable from finalized work except by the hidden `is_draft` flag, creating confusion and preventing teachers from building a curated lesson library.

This change enables teachers to:
- Mark lessons as "complete" and ready for reuse
- Browse finalized lessons separately from work-in-progress drafts
- Organize their lesson planning workflow more effectively
- Optionally revert finalized lessons back to drafts for further editing

Without this feature, teachers lose the semantic distinction between experimental/draft work and polished, classroom-ready lessons.

## Problem Statement
Currently, draft lessons exist as temporary work-in-progress items marked with `is_draft=True` in the database. Teachers create and edit drafts but have no way to "finalize" them as permanent, reusable lesson plans that can be:
- Browsed separately from drafts
- Shared or exported as completed work
- Referenced in future planning sessions
- Organized into a personal lesson library

This creates a workflow gap where teachers must manually copy draft content or lose the distinction between work-in-progress and finalized lessons.

## What Changes

- Add backend endpoints `POST /api/lessons/{id}/promote` and `POST /api/lessons/{id}/demote`
- Extend `LessonRepository` with `promote_lesson()` and `demote_lesson()` methods
- Add "My Lessons" tab in MusecDB frontend to view permanent lessons (`is_draft=false`)
- Add "Promote to Lesson" button on draft cards in the drafts UI
- Add "Move to Drafts" button on lesson cards in the lessons UI
- Implement `useLessons` hook for managing permanent lessons state
- Provide search and filter capabilities in "My Lessons" tab (parity with drafts tab)

## Impact

**Affected specs:**
- `lesson-generation` (new promotion/demotion capabilities)
- `session-management` (distinction between drafts and permanent lessons)
- `web-interface` (new "My Lessons" tab and UI actions)

**Affected code:**
- `backend/repositories/lesson_repository.py` - add promotion/demotion methods
- `backend/api/routes/lessons.py` - add promotion/demotion endpoints
- `frontend/src/pages/MusecDBPage.tsx` - add "My Lessons" tab
- `frontend/src/hooks/useLessons.ts` - new hook for lesson management
- `frontend/src/types/unified.ts` - add `LessonItem` type

## Open Questions
1. **Copy vs. Toggle**: Should promoting create a new lesson record (preserving the draft) or simply toggle `is_draft=False` on the existing record?
   - **Recommendation**: Toggle by default for simplicity; add "Save as Lesson" (copy) as a separate action if needed

2. **Metadata Review**: Should promotion require a confirmation modal with metadata review, or be a single-click action?
   - **Recommendation**: Single-click for speed, with optional "Edit & Promote" for metadata review

3. **Permanent Lessons UI**: Where should promoted lessons be viewed—new tab in MusecDB page, separate page, or integrated into existing views?
   - **Recommendation**: New "My Lessons" tab in MusecDB page alongside "Saved Drafts"

4. **Demotion**: Should teachers be able to convert a permanent lesson back to a draft?
   - **Recommendation**: Yes, via "Move to Drafts" action in the lessons view

## Related Work
- Session management spec defines draft history but doesn't distinguish permanent lessons
- Current draft endpoints (`/api/drafts`) filter by `is_draft=True`; we'll need parallel `/api/lessons` endpoints or extend existing ones

## Rollout Plan
1. Backend: Add lesson promotion/demotion endpoints
2. Frontend: Add "Promote to Lesson" button in drafts UI
3. Frontend: Create "My Lessons" tab/view for browsing permanent lessons
4. Optional: Add metadata review modal for promotion workflow
