## 1. Backend Foundations
- [ ] 1.1 Ship a Sqlite migration that creates the `presentations` table (FK to lessons, revision + status columns, JSON payload column, timestamps, indexes) and helper rollback script for dev machines.
- [ ] 1.2 Define `PresentationDocument`, `PresentationSlide`, and helper builder utilities (consistent with `LessonDocumentM2`) plus serialization helpers for markdown/json exports.
- [ ] 1.3 Implement `PresentationRepository` with CRUD, `latest_by_lesson`, stale flagging when lesson revisions change, and export asset helpers.

## 2. Presentation Generation Service
- [ ] 2.1 Build the deterministic slide scaffold builder (pure Python) that maps lesson metadata/activities into ordered slides with bullet limits + source references.
- [ ] 2.2 Implement optional Chutes JSON-polish step with timeout, schema validation, and fallback to deterministic output if the call fails; log metrics for debugging.
- [ ] 2.3 Wrap the orchestration in a `PresentationService` or PocketFlow node that: records `pending` rows, fetches lesson JSON, runs scaffold → polish, saves outputs, updates status, and emits stale flags when lessons update.
- [ ] 2.4 Add a lightweight background job runner (FastAPI `BackgroundTasks` or async task queue) so generation does not block API responses; include retry/backoff on transient failures.

## 3. API + Agent Integration
- [ ] 3.1 Add FastAPI endpoints under `/api/lessons/{lesson_id}/presentations` for (a) POST generate/regen (returns job id + pending record), (b) GET latest/history, (c) GET detail; add `/api/presentations/{id}/export?format=markdown|json`.
- [ ] 3.2 Extend session/lesson payloads so chat/drafts APIs include current presentation status + ids (so frontend knows when to show CTAs).
- [ ] 3.3 Update lesson agent flow (PocketFlow or follow-up hook) to optionally auto-trigger presentation generation on successful lesson creation and mark older decks stale when revision increments.

## 4. Frontend UX
- [ ] 4.1 Introduce presentation-related client state (Zustand slice or hook) plus API hooks to request generation, poll job status, and fetch decks.
- [ ] 4.2 Add CTA + status indicators in Drafts/Editor/RightPanel surfaces, including disabled states while pending, stale warnings, and regen actions.
- [ ] 4.3 Build a `PresentationViewer` component (slide list + detail + teacher script) with copy buttons, download links, and fallback messaging when only baseline scaffold exists.
- [ ] 4.4 Wire exports/download flows (JSON/Markdown) and ensure UI handles API errors & offline fallback gracefully.

## 5. Validation
- [ ] 5.1 Backend: tests for schema builder, repository queries, service logic (deterministic vs LLM fallback), endpoint contract, and stale detection.
- [ ] 5.2 Frontend: tests for hooks and `PresentationViewer` (loading/ready/error states) plus manual e2e run generating a deck, verifying regen, and downloading exports documented in change notes.
