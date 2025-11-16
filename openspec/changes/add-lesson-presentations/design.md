# Presentation Generation Design

## Overview
We extend the lesson workflow with an opt-in presentation builder so teachers receive a lightweight slide deck plus accompanying script. The deck is derived from the canonical `LessonDocumentM2` structure so we never scrape Markdown. Generation happens asynchronously (triggered by user action or after a lesson revision) and results are persisted as `PresentationDocument` records tied to lesson revisions.

## Data Model
- **PresentationDocument (Pydantic):** Mirrors lesson schema patterns with strict typing and helper builder. Fields: `id`, `lesson_id`, `lesson_revision`, `version` (start with `p1.0`), `status` (`pending`, `complete`, `error`, `stale`), `style`, timestamps, `slides`, `export_assets`.
- **PresentationSlide:** `{id, order, title, subtitle?, key_points[], teacher_script, visual_prompt?, duration_minutes?, source_section, activity_id?, standard_codes[]}`. `source_section` is an enum referencing lesson sections (overview, warmup, activity, etc.) for traceability.
- **PresentationExport:** optional child model storing cached Markdown/JSON (and future PPTX/PDF) metadata: `{format, url/path, generated_at}`.
- **SQLite tables:**
  - `presentations`: columns for identifiers, lesson linkage, revision, status, style, payload JSON (slides), export blobs, timestamps.
  - `presentation_exports` (optional now, required later) with FK to `presentations` for multiple formats. Initially we can inline Markdown/JSON in the main table to reduce joins.
- Index `(lesson_id, lesson_revision)` for quick latest lookup; unique constraint ensures only one active `complete` record per lesson revision.
- Schema migration script must be idempotent and cover rollback for local dev databases.

## Generation Flow
1. **Trigger:** User hits "Generate presentation" (frontend) or lesson agent auto-triggers after finalizing a lesson. The API creates a `presentations` row with `status=pending` and enqueues a background task (FastAPI background task or lightweight Celery worker).
2. **Fetch lesson:** Presentation service pulls the latest `LessonDocumentM2` (via repository or cached store), verifying required fields exist. Missing lesson data yields an error that marks the presentation row as `error` with reason.
3. **Scaffold slides (deterministic):** Builder receives the lesson and returns a `PresentationDocument` with baseline slides:
   - Slide 0: Title + grade + duration.
   - Slide 1: Learning objectives (bullets) with standards tags.
   - Slide 2: Materials & setup (optional).
   - Slide 3+: Warmup/Prerequisites, each `LessonActivity`, Assessment, Differentiation/Accommodations, Exit Ticket/Closure.
   It enforces bullet limits (e.g., 3–5) and carries over aligned standards/time hints.
4. **LLM copy polish (optional):** If the workspace is allowed to use Chutes, pass the scaffold + guardrail instructions through a JSON-mode prompt (max tokens/time). The prompt includes:
   - Slide schema definition.
   - Requirements for plain-language teacher script (<= 80 words) and 3 concise bullet points.
   - Safety instructions (no new learning objectives, keep NC standards references).
   Timeout/failure reverts to scaffold but logs telemetry + attaches warning metadata.
5. **Persist + cache exports:** Presentation service persists the final document, increments revision, stores JSON payload, and optionally emits Markdown export (header per slide) saved alongside. PPTX/PDF exporters will later read the same JSON.
6. **Status & stale tracking:** Presentation row stores `status=complete` plus `lesson_revision`. When a lesson is edited, a hook flips `status=stale` for prior rows. UI surfaces `stale` and prompts regenerate.

## API + Frontend
- Backend routes under `/api/lessons/{lesson_id}/presentations` handle:
  - `POST`: create/regen; returns 202 with job id + pending presentation metadata.
  - `GET`: fetch latest (filter by `status!=stale`) or history.
  - `GET /{presentation_id}`: detail view including slides + exports.
  Downloads reuse `/api/presentations/{presentation_id}/export?format=json|markdown` streaming the cached asset or regenerating on demand.
- SSE/WebSocket events notify the frontend when `status` transitions to `complete` or `error`; minimal version polls the API every few seconds until complete.
- Frontend Draft view and `LessonEditor` summary show:
  - CTA with states (`Generate`, `Generating…`, `Ready`, `Stale`).
  - `PresentationViewer` component: left nav (slide titles), main panel (bullets + metadata), teacher script drawer, copy buttons, download actions.
  - Surface script + visual prompt hints so teachers can prep quickly. Provide fallback text if only scaffold available.

## Error Handling & Telemetry
- Generation failures mark the row `error` with machine-readable `error_code` + human-friendly message surfaced through the API. Partial decks are not exposed.
- Telemetry captures: time to build scaffold, LLM latency, fallback usage, slide counts, export durations. Useful for analytics and cost tracking.

## Future Extensions
- Multi-style templates (e.g., "performance-focused" vs "discussion") by passing a `style` parameter.
- PPTX/PDF export microservice or Python-based generator.
- Inline editing of slides + script with round-trip persistence back to `PresentationDocument`.
