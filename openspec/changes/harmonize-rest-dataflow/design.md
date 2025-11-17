# Design: Harmonize REST Data Flow

## Overview
We keep FastAPI + Axios as the transport stack and focus on aligning contracts so frontend hooks do less bookkeeping. The change spans three backend areas (core REST routers, ingestion endpoints, documentation) and two frontend layers (shared api client + feature-specific hooks). This document captures the architecture and trade-offs for each capability.

## 1. REST Field Normalization
- **Current state**: SQLite stores comma-delimited strings for `selected_standards` / `selected_objectives`, and routers echo those fields as-is. Frontend hooks (`useSession`, `useDrafts`) convert to arrays and rename to camelCase. Presentation status metadata mixes camelCase + snake_case depending on source.
- **Approach**: Introduce serialization helpers in each repository or response model so the DB representation stays internal. Pydantic models already define camelCase (e.g., `SessionResponse.selected_standards`); ensure routers pass structured data to them.
  - Add helper to `SessionRepository` that returns Python lists for `selected_standards/objectives` using `json.loads` or `split` at DB boundary. Ideally update DB schema later, but for now converting during retrieval is sufficient.
  - For metadata fields (lesson metadata JSON), ensure routers parse JSON once and send dictionaries to the Pydantic response so clients stop string-parsing.
  - Update presentation service/ repo to emit camelCase keys for status payloads.
- **Trade-offs**: We keep DB schema unchanged, avoiding migrations. CPU cost of string splitting per request is negligible and simpler than hot migrations. Ensuring every router uses the helper avoids duplicated parsing.

## 2. Dashboard Aggregation Endpoint
- **Current state**: UnifiedPage sequentially runs `listSessions`, `getDrafts`, `getPresentations`, plus stats hooks. Each call hits SQLite separately and handles its own errors.
- **Approach**: Add `WorkspaceDashboardService` that orchestrates repositories:
  - Sessions repo → latest N sessions (plus summary metadata) for the sidebar.
  - Drafts repo → counts + most recent draft summary.
  - Presentation service → latest jobs/status per lesson.
  - Stats util → quick numbers (lessons created, active drafts) already calculated in UI.
  - Compose into JSON envelope with metadata + timestamps to help caching dashboards later.
- **Trade-offs**: Aggregation adds backend work but drastically reduces client roundtrips. We'll keep the endpoint light (<1–2 queries per section, reuse same connection) and allow optional query params (e.g., `?include=presentations`).

## 3. Streaming / Job Contract
- **Current state**: `useChat` hand-parses SSE chunks with ad-hoc `persisted`, `delta`, `status` payloads. Presentation polling lives in `presentationApiClient` with manual retry/backoff.
- **Approach**:
  - Define `StreamingEvent` dataclass/enum in backend with `type`, `payload`, and optional `meta` fields. All SSE responses go through helper `emit_stream_event(event: StreamingEvent)`, ensuring consistent shape.
  - Document allowed event types: `delta`, `status`, `persisted`, `complete`, `error`.
  - On frontend, add `parseEventStream` helper in `frontend/src/lib/api.ts` returning typed callbacks so `useChat` and any other SSE consumers share logic.
  - Presentation polling returns `JobStatusEnvelope` with `status`, `progress`, `retryAfter`, matching the error handler’s expectations. Both SSE + polling rely on a single `ProgressUpdate` TS type.
- **Trade-offs**: Slight backend refactor but avoids copy/paste parsing across hooks. We maintain SSE transport (no GraphQL/subscriptions). Helper ensures future streaming endpoints align automatically.

## 4. Ingestion Response Envelope
- **Current state**: `/ingestion/*` routes respond with `{ success: bool, ... }` while others use HTTP status + data. `IngestionService` handles 404 as feature-disabled sentinel.
- **Approach**: Create `IngestionResponse` helper that wraps payloads as `{ status: "success" | "error", message, data }`. File metadata, duplicate detection, etc. live under `data`. Errors set `status: "error"` with HTTP status codes preserved. TypeScript interface mirrors this so ingestion UI simply checks `result.status`.
- **Trade-offs**: API consumers must adapt to new envelope; we’ll coordinate client + server updates in the same release. Implementation is mechanical but yields more predictable UX.

## 5. API Documentation Refresh
- **Approach**: Enrich FastAPI router metadata (tags, response_model examples) and add `docs/api/rest-dataflow.md` summarizing dashboard endpoint, streaming event schema, ingestion envelope, and normalization rules. Also ensure OpenAPI includes the new `/workspace/dashboard` path and updated schemas.
- **Trade-offs**: Minimal—documentation time but saves future confusion.

## Backward Compatibility Plan
1. Deploy backend changes behind branch/feature flag; keep frontend transformations temporarily but log warnings if casing/arrays already correct.
2. Once backend is verified, remove transformation code from hooks.
3. Dashboard endpoint can ship alongside existing calls; frontend toggles usage based on config until stable.
4. Streaming + ingestion schema updates require synchronized frontend release; we will include integration tests that hit SSE/polling endpoints.

