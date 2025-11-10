## ADDED Requirements

### Requirement: FastAPI Server
The system SHALL provide a FastAPI server exposing REST and WebSocket endpoints for the PocketFlow backend.

#### Scenario: Server Startup
- **WHEN** the server starts with `pocketflow serve`
- **THEN** it binds to http://localhost:8000
- **AND** serves API documentation at /docs

#### Scenario: Health Check
- **WHEN** a GET request is made to /health
- **THEN** the server returns status 200
- **AND** includes backend version information

### Requirement: REST API Endpoints
The system SHALL expose RESTful endpoints for standards browsing and lesson management.

#### Scenario: Get Standards
- **WHEN** a GET request is made to /api/standards
- **THEN** the server returns a list of standards
- **AND** supports query parameters for grade and strand filtering

#### Scenario: Get Standard Details
- **WHEN** a GET request is made to /api/standards/{id}
- **THEN** the server returns detailed standard information
- **AND** includes associated objectives

#### Scenario: Create Lesson Session
- **WHEN** a POST request is made to /api/sessions
- **THEN** a new lesson generation session is created
- **AND** returns a unique session ID

#### Scenario: Get Session History
- **WHEN** a GET request is made to /api/sessions/{id}/history
- **THEN** the server returns all drafts for that session
- **AND** includes timestamps and metadata

### Requirement: WebSocket Communication
The system SHALL provide WebSocket endpoints for real-time lesson generation.

#### Scenario: WebSocket Connection
- **WHEN** a client connects to /ws/generate/{session_id}
- **THEN** a WebSocket connection is established
- **AND** the server maintains the connection for streaming

#### Scenario: Streaming Generation
- **WHEN** lesson generation is initiated via WebSocket
- **THEN** the server streams partial results as they're generated
- **AND** sends completion notification when finished

#### Scenario: Error Handling
- **WHEN** an error occurs during generation
- **THEN** the server sends an error message via WebSocket
- **AND** maintains the connection for retry

### Requirement: SSE Fallback
The system SHALL provide Server-Sent Events as a fallback for environments without WebSocket support.

#### Scenario: SSE Stream
- **WHEN** a client requests /api/generate/stream with SSE headers
- **THEN** the server establishes an SSE connection
- **AND** streams generation updates as events

#### Scenario: SSE Reconnection
- **WHEN** an SSE connection is interrupted
- **THEN** the client can reconnect with Last-Event-ID
- **AND** resume from the last received event

### Requirement: CORS Configuration
The system SHALL properly configure CORS to allow frontend communication.

#### Scenario: Cross-Origin Requests
- **WHEN** the frontend makes requests from http://localhost:3000
- **THEN** the server includes appropriate CORS headers
- **AND** allows credentials for session management

#### Scenario: Preflight Requests
- **WHEN** the browser sends OPTIONS preflight requests
- **THEN** the server responds with allowed methods and headers
- **AND** caches the preflight response appropriately

### Requirement: Request Validation
The system SHALL validate all incoming requests using Pydantic models.

#### Scenario: Valid Request
- **WHEN** a request contains valid data matching the schema
- **THEN** the request is processed successfully
- **AND** returns the expected response

#### Scenario: Invalid Request
- **WHEN** a request contains invalid or missing data
- **THEN** the server returns status 422
- **AND** provides detailed validation errors

### Requirement: Session Management
The system SHALL manage lesson generation sessions with proper lifecycle.

#### Scenario: Session Creation
- **WHEN** a new session is requested
- **THEN** a unique session ID is generated
- **AND** session state is initialized in memory

#### Scenario: Session Persistence
- **WHEN** a session is active
- **THEN** all drafts and selections are stored
- **AND** can be retrieved by session ID

#### Scenario: Session Cleanup
- **WHEN** a session exceeds the timeout period (2 hours)
- **THEN** the session data is cleaned up
- **AND** resources are released

### Requirement: Export API
The system SHALL provide endpoints for exporting lessons in various formats.

#### Scenario: PDF Export
- **WHEN** a POST request is made to /api/export/pdf
- **THEN** the server generates a PDF file
- **AND** returns it with appropriate content-type

#### Scenario: Word Export
- **WHEN** a POST request is made to /api/export/docx
- **THEN** the server generates a Word document
- **AND** returns it as application/vnd.openxmlformats

#### Scenario: Text Export
- **WHEN** a POST request is made to /api/export/text
- **THEN** the server returns plain text with markdown
- **AND** preserves lesson structure