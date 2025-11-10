# Specification: Streaming (SSE)

## ADDED Requirements

### Requirement: SSE Token Streaming
The system SHALL stream model output tokens via Server-Sent Events (SSE) to the frontend, enabling a live preview panel that updates incrementally.

#### Scenario: Live preview during generation
- WHEN lesson generation starts
- THEN the backend opens an SSE stream emitting token chunks
- AND the frontend live preview updates as tokens arrive
- AND the stream closes cleanly on completion or cancel

### Requirement: Whole-Response Fallback
The system SHALL support a whole-response fallback when SSE is unavailable or disabled.

#### Scenario: SSE unavailable
- GIVEN SSE cannot be established
- WHEN generation runs
- THEN the system returns the complete response after completion
- AND the UI displays the final content without streaming

