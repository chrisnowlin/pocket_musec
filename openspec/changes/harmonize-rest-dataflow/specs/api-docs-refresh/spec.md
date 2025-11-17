# Specification: API Documentation Refresh

## ADDED Requirements

### Requirement: OpenAPI Accuracy
The FastAPI-generated OpenAPI document MUST describe the new/updated endpoints and schemas.

#### Scenario: Dashboard endpoint docs
Given `/api/workspace/dashboard` exists
When OpenAPI is rendered (e.g., `/api/docs`)
Then the path is documented with request parameters (`include` query) and response schema examples for each section (sessions, drafts, presentations, stats).

#### Scenario: Streaming + ingestion schemas
Given streaming events and ingestion envelopes now follow standardized structures
When reviewing OpenAPI schemas
Then the event and envelope models are defined once and referenced by every applicable route, preventing duplication or ambiguity.

### Requirement: Human-readable Documentation
A markdown guide SHALL summarize the refined API behavior for developers.

#### Scenario: REST dataflow guide
Given the repo includes `docs/api/`
When contributors read `docs/api/rest-dataflow.md`
Then it explains:
- Field normalization expectations (camelCase, arrays)
- Dashboard endpoint purpose and payload example
- Streaming event schema and job status envelope
- Ingestion response envelope usage
And links to the relevant OpenAPI sections/spec IDs.

#### Scenario: Error and retry guidance
Given developers need to understand retry semantics
When they consult the documentation
Then the guide outlines how streaming events signal completion/errors and how job polling communicates `retryAfterSeconds`, matching the implementation.

