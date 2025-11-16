# Proposal: Milestone 2 Lesson JSON Schema (Version m2.0)

## Why

The current lesson representation is primarily free-form Markdown/text with loosely structured metadata. As we add richer lesson editing, revision history, and front-end tooling, we need a **stable, explicit JSON schema** that:

- Defines a contract between the FastAPI backend and the Electron/React frontend
- Supports structured lesson editing (per-activity editing, timing, alignment, citations)
- Enables validation, migration, and versioning of stored lessons

The decision log already describes a "Milestone 2 Lesson JSON Schema" with version `m2.0`. This change formalizes that schema into OpenSpec so:

- Backend and frontend teams share a single authoritative specification
- Automated validation can be added at API boundaries
- Future versions (m2.1, m3.x, etc.) can evolve in a controlled way

## Problem Statement

Today, lessons are passed around and stored as loosely structured content (title, content, metadata) without a canonical JSON envelope that:

- Captures per-activity structure (title, steps, alignment, citations)
- Encodes timing and revision information
- Provides a clear place to attach standards and objectives

This makes it difficult to:

- Safely evolve the lesson editor without breaking saved data
- Validate exported/imported lessons
- Implement features like per-activity standards alignment, duration management, and citations

## What Changes

This change introduces a **versioned JSON schema `m2.0`** for lessons and wires it into the backend/frontend contract at the spec level.

High level changes:

- Add an OpenSpec for the **Milestone 2 Lesson JSON Schema (m2.0)** that formalizes:
  - Top-level metadata (IDs, timestamps, versioning)
  - Instructional metadata (grade, strands, standards, objectives)
  - Structured content (materials, warmup, activities with steps & timing, assessment, differentiation, etc.)
  - Citations and revision fields
- Define the schema as the **canonical representation** for:
  - API responses that return full lessons
  - API requests that create or update lessons
  - Local lesson exports (JSON) used by the desktop app
- Require backend endpoints that work with full lesson payloads to validate against `m2.0` before persisting
- Require the frontend to treat the schema as the single source of truth for the lesson editor shape

## Impact

**Affected specs:**

- `lesson-generation` – references to lesson output must use the `m2.0` structure
- `promote-draft-to-lesson` – finalized lessons should be persisted/returned in `m2.0` format
- `web-interface` – lesson editor and viewer UIs will operate on `m2.0` lesson documents

**Affected code (conceptual):**

- Backend:
  - `backend/api/routes/lessons.py` (lesson create/update/read endpoints)
  - `backend/repositories/lesson_repository.py` (storage and retrieval of lesson documents)
  - JSON validation layer (pydantic models or schema-based validation)
- Frontend:
  - Lesson editor components
  - Lesson viewer/preview components
  - Types used to model lessons (e.g., `LessonItem` / `LessonDocument`)

## Non-Goals

- Implementing the full UI for editing every field; this change only defines the schema.
- Defining PDF/Markdown export formats (they will be derived from `m2.0` but are out of scope here).
- Designing migration paths from any existing pre-m2.0 lesson storage; this will be covered in a separate change.

## Open Questions

1. **Partial payloads:** Can some endpoints accept partial lesson payloads (e.g., only updating `activities`), or must all writes send a full `m2.0` document?
2. **Backward compatibility:** Do we need explicit support for reading legacy lessons that predate `m2.0`? If yes, how do we annotate them (`version`, `schema_version`, etc.)?
3. **Schema storage:** Should the JSON Schema be bundled in the backend repo (e.g., `schemas/lesson-m2.json`) or generated from pydantic models?
4. **Validation strictness:** Should extra fields be rejected (strict schema) or tolerated (for forwards compatibility)?
5. **Per-activity IDs:** Are `activities[].id` required to be stable across edits (for tracking analytics, comments, etc.), or can they be regenerated on each save?

