# API Server - camelCase Naming Delta

## MODIFIED Requirements

### Requirement: API Response Format
The API server SHALL return all JSON responses with camelCase field naming. Pydantic models SHALL define fields in camelCase without requiring alias_generator conversion.

#### Scenario: Session creation response uses camelCase
- **WHEN** client creates a session via `POST /api/v2/sessions`
- **THEN** response contains fields like `gradeLevel`, `strandCode`, `userId`, `createdAt` natively

#### Scenario: Lesson list response uses camelCase
- **WHEN** client requests lessons via `GET /api/v2/lessons`
- **THEN** each lesson object contains `sessionId`, `userId`, `isDraft`, `createdAt` fields

#### Scenario: Error responses use camelCase
- **WHEN** API returns error response
- **THEN** error object contains camelCase fields like `errorCode`, `errorMessage`, `requestId`

### Requirement: API Request Format
The API server SHALL accept request payloads with camelCase field naming. Path parameters and query parameters SHALL use camelCase.

#### Scenario: Session creation with camelCase payload
- **WHEN** client sends `POST /api/v2/sessions` with body containing `gradeLevel`, `strandCode`, `lessonDuration`
- **THEN** server successfully parses and processes the request

#### Scenario: Path parameters use camelCase
- **WHEN** client requests `GET /api/v2/sessions/{sessionId}/messages`
- **THEN** server correctly routes to session by ID

#### Scenario: Query parameters use camelCase
- **WHEN** client requests `GET /api/v2/standards?gradeLevel=5&strandCode=CR`
- **THEN** server filters standards correctly

### Requirement: Pydantic Model Naming
All Pydantic model fields SHALL be defined in camelCase. The CamelModel base class SHALL be removed as conversion is no longer needed.

#### Scenario: Session model defines camelCase fields
- **WHEN** defining SessionCreateRequest Pydantic model
- **THEN** fields are declared as `gradeLevel: str`, `userId: str`, `selectedObjectives: List[str]`

#### Scenario: No alias_generator required
- **WHEN** Pydantic models inherit from BaseModel
- **THEN** no alias_generator configuration is needed, fields serialize to JSON as-is

### Requirement: API Versioning
The API server SHALL provide v2 endpoints with camelCase contracts and maintain v1 endpoints with backward compatibility during a 6-month deprecation period.

#### Scenario: v2 endpoint serves camelCase
- **WHEN** client requests `GET /api/v2/sessions`
- **THEN** response uses camelCase field names natively

#### Scenario: v1 endpoint maintains compatibility
- **WHEN** client requests `GET /api/v1/sessions` (deprecated)
- **THEN** response uses snake_case via conversion layer for backward compatibility

#### Scenario: v1 deprecation warning
- **WHEN** client uses any v1 endpoint
- **THEN** response includes deprecation header: `X-API-Deprecated: true` and `X-Deprecation-Date: 2025-05-17`

## ADDED Requirements

### Requirement: FastAPI Route Handler Naming
All FastAPI route handler functions SHALL use camelCase naming.

#### Scenario: Route handlers defined in camelCase
- **WHEN** defining route handler for sessions endpoint
- **THEN** function is named `async def listSessions()` not `async def list_sessions()`

#### Scenario: Dependency injection uses camelCase
- **WHEN** injecting repository dependencies
- **THEN** parameter is named `sessionRepository: SessionRepository = Depends(getSessionRepository)`

### Requirement: OpenAPI Schema Conformance
The OpenAPI schema SHALL reflect camelCase field names in all request/response models for v2 endpoints.

#### Scenario: OpenAPI shows camelCase fields
- **WHEN** accessing `/api/docs` or `/api/openapi.json`
- **THEN** v2 endpoint schemas show `gradeLevel`, `userId`, `createdAt` in model definitions

#### Scenario: Request examples use camelCase
- **WHEN** viewing API documentation examples
- **THEN** sample requests show camelCase payloads

## REMOVED Requirements

### Requirement: CamelModel Base Class
**Reason**: No longer needed as all fields are natively camelCase
**Migration**: Replace `CamelModel` inheritance with `BaseModel`, ensure field names are camelCase

#### Scenario: Previous CamelModel usage
- **WHEN** models previously inherited from `CamelModel`
- **THEN** this base class and its alias_generator are removed

### Requirement: Response Field Conversion
**Reason**: Eliminated by native camelCase field definitions
**Migration**: Remove alias_generator and populate_by_name config from Pydantic models

#### Scenario: Previous automatic conversion
- **WHEN** snake_case Python fields were automatically converted to camelCase JSON
- **THEN** this conversion layer is removed, fields are defined in camelCase from the start
