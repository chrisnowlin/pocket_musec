# Change Proposal: Harmonize REST Data Flow

**Change ID**: `harmonize-rest-dataflow`
**Status**: DRAFT  
**Created**: 2025-02-14  
**Author**: cnowlin

## Summary
Teachers rely on the PocketMusec workspace to juggle chat, lessons, drafts, files, and presentations. The current REST APIs already cover these flows, but the contract has drifted: frontend hooks reshape snake_case payloads, each panel fires separate fetches, streaming/chat protocols leak transport specifics into UI hooks, ingestion/file APIs return ad-hoc success flags, and the API surface lacks consolidated documentation. This proposal harmonizes the REST data flow so clients can stay simple while retaining the existing FastAPI foundation.

## Problem
1. **Field shape mismatches** – `/api/sessions` and `/api/lessons` ship comma-separated strings that the frontend converts to arrays and camelCase (`frontend/src/hooks/useSession.ts`, `useDrafts.ts`). This duplication increases bug risk and complicates future consumers.
2. **Fragmented dashboard hydration** – `UnifiedPage` independently loads sessions, drafts, presentation statuses, and stats. Each call repeats auth and error handling even though the UI needs the same bundle to render.
3. **Leaky streaming/progress flows** – `useChat` manually parses SSE chunks while presentation polling wraps bespoke retry logic in `presentationApiClient`. There is no shared schema to validate events.
4. **Inconsistent ingestion responses** – Document ingestion endpoints (classify/ingest/files) respond with mixed `{ success, error }` envelopes that `IngestionService` has to special-case per route.
5. **Doc drift** – API docs/OpenAPI do not explain the above contracts, leaving future contributors without authoritative guidance.

## Solution
Deliver a set of tightly scoped REST refinements instead of a GraphQL rewrite:
1. **REST Field Normalization** – Have FastAPI routers emit camelCase JSON with proper arrays/maps for sessions, lessons, drafts, and presentations so hooks can consume responses as-is.
2. **Dashboard Aggregation Endpoint** – Add a `/api/workspace/dashboard` route that bundles recent sessions, draft counts, latest presentation jobs, and quick stats in a single call for UnifiedPage hydration.
3. **Streaming/Job Contract** – Define a small streaming event schema (delta/status/persisted/error) and progress status envelope and offer helper utilities on the frontend so chat/presentation flows share parsing/retry logic.
4. **Ingestion Response Envelope** – Standardize document/file ingestion endpoints on a `status/message/data` pattern to remove guesswork in `IngestionService` and align with other apiClient helpers.
5. **API Documentation Refresh** – Extend OpenAPI tags + markdown docs so the above behavior is discoverable (request/response examples, error codes, retry semantics).

## Capabilities
This change proposes five capability deltas, each tracked under its own spec folder:
1. `rest-field-normalization` – enforce camelCase + structured arrays in REST responses.
2. `dashboard-aggregation` – expose consolidated workspace data endpoint.
3. `stream-contract` – define streaming/polling event schema + shared client utility expectations.
4. `ingestion-envelope` – unify ingestion/document/file API envelopes.
5. `api-docs-refresh` – document the refined API behavior and examples.

## User Journey Impact
- UnifiedPage hydrates once via `/workspace/dashboard`, reducing perceived latency on app load.
- Session and lesson hooks drop manual casing/objective parsing and simply trust API payloads.
- Chat/presentation UI benefits from clearer progress/error messaging thanks to shared event schemas.
- Document ingestion modals surface consistent success/error banners because backend responses share the same envelope.
- Future contributors consult updated docs/OpenAPI to extend endpoints without reverse-engineering payloads.

## Technical Approach
- Update FastAPI Pydantic models/repositories to emit arrays and camelCase fields, ensuring DB serialization happens during read/write instead of at the client.
- Implement a lightweight dashboard service that composes existing repositories (sessions, drafts, presentations, stats) behind one route guarded by the existing auth dependency.
- Introduce a streaming event dataclass/enum describing `delta`, `status`, `persisted`, and `error` messages plus a shared helper in `frontend/src/lib/api.ts` that parses SSE chunks and job polling responses.
- Wrap ingestion endpoints in a shared response helper returning `{ status: 'success'|'error', message, data }`, updating the TS service accordingly.
- Extend OpenAPI schema (tags, response models, examples) and add markdown docs under `docs/api/` explaining dashboard + streaming + ingestion envelopes; ensure `/api/docs` shows the new contracts.

## Dependencies & Risks
- Requires coordination across backend routers (`sessions`, `lessons`, `drafts`, `presentations`, `ingestion`) and frontend hooks/services. Changes must be staged carefully to avoid breaking existing UI – gated rollout plan captured in tasks.
- Dashboard aggregation must be efficient (reuse existing repos, limit DB hits) to avoid startup slowdown.
- Streaming contract updates must remain backward compatible for existing SSE consumers; plan includes feature flag or version guard if needed.

## Success Criteria
- Frontend hooks (`useSession`, `useDrafts`, `useChat`, `presentationStore`) no longer include ad-hoc casing/objective parsing code.
- UnifiedPage renders with a single dashboard fetch + targeted follow-up calls (e.g., selected session chat stream).
- SSE/chat log lines include the standardized `type`/`payload` schema and presentation polls reuse the shared helper.
- Ingestion modals display consistent messaging driven purely by the unified envelope.
- API docs show updated schemas/examples for all touched endpoints and `openspec validate harmonize-rest-dataflow --strict` passes.

## Open Questions
1. Do we need versioned response envelopes (e.g., `"version": "2025.02"`) for downstream integrations, or is implicit migration acceptable?
2. Should dashboard stats include heavy aggregates (e.g., usage charts) or remain lightweight counts to keep latency low?
3. Are there external consumers of the ingestion endpoints that need early notice about the new envelope structure?

