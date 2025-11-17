# Specification: REST Field Normalization

## ADDED Requirements

### Requirement: CamelCase API Responses
The REST API SHALL return camelCase keys for session, lesson, draft, and presentation resources so clients no longer re-map snake_case payloads.

#### Scenario: Session response casing
Given an authenticated teacher
When they call `GET /api/sessions` or `GET /api/sessions/{id}`
Then each session object uses camelCase keys (e.g., `gradeLevel`, `strandCode`, `selectedStandards`, `selectedObjectives`, `additionalContext`, `conversationHistory`)
And no snake_case aliases appear in the JSON.

#### Scenario: Lesson metadata casing
Given a stored lesson with metadata JSON
When `GET /api/lessons/{id}` is requested
Then the metadata block is returned as a JSON object with camelCase keys (matching what was originally stored) without requiring the client to re-parse raw strings.

### Requirement: Structured Collections
Selected standards, objectives, and related metadata MUST be returned as JSON arrays/objects rather than comma-delimited strings.

#### Scenario: Standards arrays
Given a session that references multiple standards in the database
When the session is returned via the API
Then `selectedStandards` is a JSON array of standard objects (id, code, grade, etc.)
And `selectedObjectives` is a JSON array of objective identifiers or descriptors.

#### Scenario: Presentation status metadata
Given a lesson with presentation generation in progress
When the lessons endpoint returns `presentation_status`
Then that value is a JSON object containing camelCase keys (`status`, `lessonRevision`, `updatedAt`, etc.)
And values reflect up-to-date state without requiring further database lookups on the client.

### Requirement: Repository Serialization Helpers
Repositories MUST convert internal storage formats (comma-delimited strings, JSON text blobs) to structured Python types before responses are serialized.

#### Scenario: SessionRepository serialization
Given `SessionRepository` fetches a row that stores `selected_standards` as comma-delimited text
When the repository returns a Session model for API usage
Then it exposes the field as a list of strings (or nested objects) ready for response models, ensuring routers do not perform duplicate parsing.

#### Scenario: LessonRepository metadata reuse
Given lesson metadata is stored as JSON text
When multiple endpoints (lessons list, drafts promotion, presentations) return that metadata
Then each endpoint reuses the same helper to deserialize once, preventing drift between responses.

