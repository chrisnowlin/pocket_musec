# Session Management - camelCase Naming Delta

## MODIFIED Requirements

### Requirement: Session Data Model
Session objects SHALL use camelCase field naming in all contexts: API responses, database columns, and internal data structures.

#### Scenario: Session creation returns camelCase fields
- **WHEN** creating a session via POST /api/v2/sessions
- **THEN** response contains: `{ id, userId, gradeLevel, strandCode, selectedStandards, selectedObjectives, additionalContext, lessonDuration, classSize, createdAt, updatedAt, selectedModel }`

#### Scenario: Session database record uses camelCase columns
- **WHEN** querying sessions table
- **THEN** columns are: `id, userId, gradeLevel, strandCode, selectedStandards, selectedObjectives, additionalContext, lessonDuration, classSize, createdAt, updatedAt, selectedModel`

#### Scenario: Session repository methods use camelCase
- **WHEN** calling session repository methods
- **THEN** methods are named: `createSession()`, `listSessionsForUser()`, `updateSession()`, `deleteSession()`

### Requirement: Session API Endpoints
Session API endpoints SHALL accept and return camelCase payloads without conversion.

#### Scenario: Create session with camelCase request
- **WHEN** client sends POST /api/v2/sessions with body:
  ```json
  {
    "gradeLevel": "5",
    "strandCode": "CR",
    "standardId": "5.CR.1",
    "additionalContext": "Focus on rhythm",
    "lessonDuration": "45 min",
    "classSize": 25,
    "selectedObjectives": ["5.CR.1.1", "5.CR.1.2"],
    "selectedModel": "gpt-4"
  }
  ```
- **THEN** session is created successfully with fields stored as provided

#### Scenario: List sessions returns camelCase
- **WHEN** client requests GET /api/v2/sessions
- **THEN** response array contains session objects with camelCase fields

#### Scenario: Session path parameter uses camelCase
- **WHEN** accessing specific session via GET /api/v2/sessions/{sessionId}
- **THEN** route parameter name is `sessionId` not `session_id`

### Requirement: Session Repository Implementation
SessionRepository class methods SHALL use camelCase naming for all functions and internal variables.

#### Scenario: Repository method naming
- **WHEN** implementing session repository
- **THEN** methods are defined as:
  - `async def createSession(userId: str, gradeLevel: str, ...)`
  - `async def listSessionsForUser(userId: str)`
  - `async def getSessionById(sessionId: str)`
  - `async def updateSession(sessionId: str, updates: dict)`

#### Scenario: Repository internal variables use camelCase
- **WHEN** implementing repository methods
- **THEN** internal variables use camelCase: `gradeLevel = row["gradeLevel"]`, `createdAt = datetime.now()`

### Requirement: Session WebSocket Messages
WebSocket messages for session chat SHALL use camelCase field naming in all message types.

#### Scenario: Chat message event uses camelCase
- **WHEN** server sends chat message via WebSocket
- **THEN** message structure uses: `{ type: "message", sessionId, userId, content, createdAt, messageId }`

#### Scenario: Session status update uses camelCase
- **WHEN** server sends session status update
- **THEN** message uses: `{ type: "status", sessionId, status, updatedAt }`

## ADDED Requirements

### Requirement: Session Query Parameter Naming
Session list filtering query parameters SHALL use camelCase.

#### Scenario: Filter by grade level
- **WHEN** client requests GET /api/v2/sessions?gradeLevel=5
- **THEN** server filters sessions by grade level 5

#### Scenario: Filter by strand code
- **WHEN** client requests GET /api/v2/sessions?strandCode=CR
- **THEN** server filters sessions by strand code CR

#### Scenario: Combined filters use camelCase
- **WHEN** client requests GET /api/v2/sessions?gradeLevel=5&strandCode=CR&userId=user123
- **THEN** all filters are applied correctly

## REMOVED Requirements

None - no session-management requirements are being removed, only modified.

## RENAMED Requirements

None - no requirements are being renamed.
