# Design: Milestone 2 Lesson JSON Schema (m2.0)

## Context

Milestone 2 introduces a structured, versioned JSON schema (`m2.0`) for lessons that becomes the contract between the FastAPI backend and the Electron/React frontend. Lessons are currently stored and exchanged in a more ad hoc shape (title/content/metadata), which is insufficient for per-activity editing, timing, standards alignment, and citations.

This design describes how to represent the m2.0 schema in code, where validation occurs, and how it fits into existing lesson-generation and storage flows.

## Goals / Non-Goals

- **Goals**
  - Represent the `m2.0` lesson schema as a strongly-typed model in the backend.
  - Validate lesson JSON on all create/update operations at the API boundary.
  - Ensure lesson-generation produces documents that conform to `m2.0`.
  - Provide a stable contract for frontend lesson editor and viewer components.

- **Non-Goals**
  - Implement full data migration for legacy lessons (covered in a follow-up change if needed).
  - Redesign lesson editing UX; only structural changes to the underlying data.
  - Specify export formats (PDF/Markdown) beyond leveraging the schema.

## Decisions

1. **Schema Representation**
   - Use **Pydantic models** to represent the m2.0 lesson schema in Python.
   - Optionally export a JSON Schema document from the Pydantic models for tooling (validation, docs).

2. **Version Field**
   - Introduce a required `version: Literal["m2.0"]` top-level field on the main lesson model.
   - Use this field to discriminate between schema versions when loading from storage.

3. **Validation Boundary**
   - Perform schema validation in the **FastAPI layer** when handling lesson create/update requests.
   - Reject invalid payloads with `400 Bad Request` and structured error messages.
   - Ensure any internal producers (e.g., lesson-generation pipeline) also instantiate the Pydantic model so invalid structures fail fast.

4. **Storage**
   - Store the serialized m2.0 lesson document as JSON in the existing lesson storage mechanism (e.g., JSON column or serialized field), without further normalization for this milestone.
   - Preserve `id`, `created_at`, `updated_at`, and `revision` fields as first-class metadata alongside the JSON payload if the existing model already does so.

5. **Frontend Types**
   - Mirror the backend schema with TypeScript interfaces/types in the frontend to ensure static checking in the editor and viewer.
   - Treat the m2.0 shape as the single source of truth for lesson-related UI.

## Risks / Trade-offs

- **Risk: Strict validation breaks existing clients**
  - Mitigation: Roll out m2.0 only on endpoints that are guaranteed to be used by the updated app version, or add a compatibility layer for older payloads.

- **Risk: Schema evolution**
  - Mitigation: Use explicit `version` and keep m2.0 stable; future changes will introduce `m3.x` schemas and migration logic in separate changes.

- **Risk: Overly rigid structure**
  - Mitigation: Allow some optional fields (e.g., empty arrays/strings) while still enforcing overall structure.

## Migration Plan

- **Phase 1: Spec & Validation**
  - Finalize `m2.0` requirements in OpenSpec (this change).
  - Implement Pydantic models and wire them into FastAPI endpoints.
  - Ensure lesson-generation code builds instances of the new models before returning.

- **Phase 2: Frontend Alignment**
  - Update TypeScript types and ensure editor/viewer components use the m2.0 shape.
  - Run manual and automated tests for generate → edit → save → reopen flows.

- **Phase 3: Legacy Data (optional, follow-up)**
  - If legacy lessons exist, add adapters/migrations to upgrade them to m2.0 on read or via a one-time migration.
  - Document migration strategy in a separate change if complexity is non-trivial.

## Open Questions

- Should the JSON Schema be exported and versioned as a standalone artifact (e.g., `schemas/lesson-m2.json`) for use outside the backend (e.g., validation in tooling)?
- Do we need a second, lighter-weight shape for listing lessons (e.g., cards) or should lists return full m2.0 documents and let the frontend project down to cards?
- How strict should timing validation be (exact sum of `activities[].duration_minutes` vs `content.timing.total_minutes`, or an allowed tolerance)?


## Final Migration & Rollout Decisions

For this change we:

- Do **not** maintain any on-read migration logic for legacy lessons. The
  drafts API returns whatever metadata is stored for a lesson; if there is
  no `lesson_document` inside `metadata`, the frontend falls back to the
  narrative `content` string for display.
- Store any authored m2.0 documents inside `metadata.lesson_document` and
  validate them via `_validate_and_attach_m2_document`, which wraps
  `build_m2_lesson_document`. This adds/maintains `id`, `created_at`,
  `updated_at`, `version`, and `revision` fields on every write.
- Treat `metadata.lesson_document` as the canonical source of truth on the
  frontend when present. The drafts viewer/editor (`DraftPreview`,
  `DraftsModal`, and `useDrafts.saveEditedLesson`) prefer
  `lesson_document.content.notes` for display and editing, while keeping
  the legacy `content` string in sync.
- Rely on the fact that there is currently no lesson data that needs to be
  preserved. Any previously generated lessons were test data and can be
  safely discarded, so there is no separate data migration step for this
  change.
