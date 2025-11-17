# Specification: Ingestion Response Envelope

## ADDED Requirements

### Requirement: Unified Envelope Structure
All `/api/ingestion/*` routes MUST return a `{ status: "success" | "error", message: string, data: object | null }` envelope regardless of specific payload contents.

#### Scenario: Successful document ingestion
Given a file is processed without duplicates
When `/ingestion/ingest` responds
Then it returns `status: "success"`, a human-readable `message`, and `data` containing the previous `classification`, `results`, and `fileMetadata` fields.

#### Scenario: Duplicate detection
Given the uploaded file already exists
When the endpoint responds
Then it sets `status: "success"` (operation completed) with `data.duplicate = true` and `data.existingFile` describing the prior upload, ensuring the UI can inform the teacher.

### Requirement: Error Signaling
Failures SHALL set `status: "error"` and include error context while still using HTTP status codes.

#### Scenario: Parser failure
Given ingestion cannot parse the file
When the endpoint responds
Then HTTP status is 422 (or relevant code) and the body sets `status: "error"`, `message` describing the issue, and `data` MAY include structured error details for diagnostics.

#### Scenario: Feature disabled
Given ingestion is disabled in the current build
When a route is called
Then it responds with HTTP 404 or 503, sets `status: "error"`, and `message` explains the feature toggle so the frontend can show a friendly notice.

### Requirement: Client Consumption
Frontend services SHALL rely on the envelope instead of custom success flags.

#### Scenario: IngestionService updates
Given the TypeScript `IngestionService` fetches ingestion routes
When it receives a response
Then it inspects `status` and `message` rather than checking for arbitrary `success` booleans, and surfaces standardized toasts/errors accordingly.

#### Scenario: Tests for envelope adherence
Given regression tests cover ingestion flows
When the backend or frontend changes are validated
Then tests assert that responses follow the `{ status, message, data }` pattern for both success and failure cases.

