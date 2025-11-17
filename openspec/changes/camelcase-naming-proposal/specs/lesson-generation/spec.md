# Lesson Generation - camelCase Naming Delta

## MODIFIED Requirements

### Requirement: Lesson Data Model
Lesson objects SHALL use camelCase field naming in all contexts: API responses, database columns, PocketFlow nodes, and internal data structures.

#### Scenario: Lesson API response uses camelCase
- **WHEN** requesting lesson via GET /api/v2/lessons/{lessonId}
- **THEN** response contains: `{ id, sessionId, userId, title, content, metadata, processingMode, isDraft, createdAt, updatedAt }`

#### Scenario: Lesson database record uses camelCase columns
- **WHEN** querying lessons table
- **THEN** columns are: `id, sessionId, userId, title, content, metadata, processingMode, isDraft, createdAt, updatedAt`

#### Scenario: Lesson metadata uses camelCase
- **WHEN** accessing lesson metadata JSON
- **THEN** fields include: `lessonDocument, gradeLevel, standardIds, objectiveIds, lessonDuration, classSize`

### Requirement: Lesson Repository Methods
LessonRepository class methods SHALL use camelCase naming for all functions, parameters, and internal variables.

#### Scenario: Repository method naming
- **WHEN** implementing lesson repository
- **THEN** methods are defined as:
  - `async def createLesson(sessionId: str, userId: str, ...)`
  - `async def listLessonsForUser(userId: str)`
  - `async def listLessonsForSession(sessionId: str)`
  - `async def updateLesson(lessonId: str, updates: dict)`
  - `async def deleteLesson(lessonId: str)`

#### Scenario: Repository parameters use camelCase
- **WHEN** calling repository methods
- **THEN** parameters are named: `sessionId`, `userId`, `lessonId`, `isDraft`, `processingMode`

### Requirement: PocketFlow Lesson Node Naming
PocketFlow lesson generation nodes SHALL use camelCase for node functions, flow variables, and store keys.

#### Scenario: Lesson generation node function naming
- **WHEN** defining PocketFlow nodes for lesson generation
- **THEN** node functions are named: `generateLessonNode()`, `validateStandardsNode()`, `formatOutputNode()`

#### Scenario: Flow context uses camelCase
- **WHEN** passing data between PocketFlow nodes
- **THEN** context keys use camelCase: `context.gradeLevel`, `context.selectedObjectives`, `context.lessonDuration`

#### Scenario: Store keys use camelCase
- **WHEN** storing lesson generation state
- **THEN** store keys are camelCase: `store.set("currentDraft", draft)`, `store.get("generationStatus")`

### Requirement: Lesson API Endpoints
Lesson API endpoints SHALL accept and return camelCase payloads for all operations.

#### Scenario: Create lesson with camelCase request
- **WHEN** client sends POST /api/v2/lessons with body:
  ```json
  {
    "sessionId": "sess123",
    "userId": "user456",
    "title": "Rhythm and Tempo",
    "content": "...",
    "metadata": {
      "gradeLevel": "5",
      "standardIds": ["5.CR.1"],
      "lessonDuration": "45 min"
    },
    "processingMode": "cloud",
    "isDraft": true
  }
  ```
- **THEN** lesson is created successfully with fields stored as provided

#### Scenario: Update lesson with camelCase
- **WHEN** client sends PATCH /api/v2/lessons/{lessonId} with `{ isDraft: false }`
- **THEN** lesson draft status is updated to published

#### Scenario: List lessons query parameters use camelCase
- **WHEN** client requests GET /api/v2/lessons?sessionId=sess123&isDraft=true
- **THEN** server filters lessons correctly

### Requirement: Lesson Service Layer Naming
Lesson service functions SHALL use camelCase naming for all methods and variables.

#### Scenario: Service method naming
- **WHEN** implementing lesson service
- **THEN** methods are named: `generateLesson()`, `regenerateLesson()`, `promoteDraftToLesson()`, `exportLesson()`

#### Scenario: Service internal variables use camelCase
- **WHEN** implementing service methods
- **THEN** variables use camelCase: `lessonContent = generateContent()`, `metadataDict = parseMetadata()`

## ADDED Requirements

### Requirement: Lesson JSON Schema Field Naming
LessonDocumentM2 JSON schema fields SHALL use camelCase naming.

#### Scenario: Lesson document schema uses camelCase
- **WHEN** generating lesson document following m2.0 schema
- **THEN** fields are camelCase: `lessonTitle, gradeLevel, standardsAlignment, learningObjectives, lessonDuration, materialsNeeded, assessmentStrategies`

#### Scenario: Procedure steps use camelCase
- **WHEN** defining lesson procedure steps
- **THEN** step fields are: `stepNumber, stepTitle, timeAllocation, teacherActions, studentActions`

#### Scenario: Differentiation strategies use camelCase
- **WHEN** defining differentiation in lesson document
- **THEN** fields are: `approachType, targetGroup, strategyDescription, implementationNotes`

## REMOVED Requirements

None - no lesson-generation requirements are being removed, only modified and added.

## RENAMED Requirements

None - no requirements are being renamed.
