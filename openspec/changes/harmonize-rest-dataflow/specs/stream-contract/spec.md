# Specification: Streaming & Job Contract

## ADDED Requirements

### Requirement: Standardized Streaming Events
SSE/chat endpoints SHALL emit events using a shared schema `{ "type": string, "payload": object, "meta": object | null }`.

#### Scenario: Delta event
Given the chat agent streams a response token
When the SSE event is sent
Then it has `type: "delta"` and `payload` contains the text chunk
And clients can append text without inspecting transport-specific framing.

#### Scenario: Status and completion events
Given the backend needs to notify clients about persistence or completion
When such events occur
Then SSE messages use `type: "status"`, `type: "persisted"`, or `type: "complete"` with structured payloads (e.g., `payload.message`, `payload.sessionUpdated`)
And the schema matches documentation for every streaming endpoint.

### Requirement: Shared Frontend Parser Utility
Clients MUST consume streaming events through a shared parser helper to reduce duplicate logic.

#### Scenario: Chat hook integration
Given `useChat` subscribes to SSE streams
When it processes data
Then it uses the shared parser to transform chunks into typed events and update UI state, instead of hand-parsing `\n\n` delimiters.

#### Scenario: Future streaming consumers
Given another feature (e.g., live ingestion progress) adopts SSE
When it hooks into the parser helper
Then it receives the same typed callbacks, guaranteeing consistent handling of completion/error semantics.

### Requirement: Job Status Envelope
Presentation job status and similar long-running tasks SHALL return a consistent JSON envelope.

#### Scenario: Polling response structure
Given `/api/presentations/jobs/{id}` is polled
When the backend returns status
Then the payload contains `{ status, progress (0-1), stepSummary, retryAfterSeconds?, error? }`
And the client can rely on these fields for retries or UI updates.

#### Scenario: Retry/backoff metadata
Given a job hits a transient failure
When the backend responds
Then the envelope includes `status: "retryable"` or an `error` block with `retryAfterSeconds`
So frontend utilities can schedule retries without custom heuristics per endpoint.

