# Project Conventions - camelCase Naming Delta

## MODIFIED Requirements

### Requirement: Code Style - Python Naming
Python code SHALL use camelCase for all functions, variables, methods, and module names. Classes SHALL use PascalCase. Constants SHALL use SCREAMING_SNAKE_CASE.

#### Scenario: Function naming
- **WHEN** defining a Python function
- **THEN** function name uses camelCase: `def createLesson()`, `def listSessionsForUser()`

#### Scenario: Variable naming
- **WHEN** declaring Python variables
- **THEN** variable names use camelCase: `gradeLevel = "5"`, `userId = session.userId`

#### Scenario: Module naming
- **WHEN** creating Python module files
- **THEN** module names use camelCase: `exportService.py`, `lessonRepository.py`, `presentationJobs.py`

#### Scenario: Class naming unchanged
- **WHEN** defining Python classes
- **THEN** class names use PascalCase: `class LessonRepository`, `class ExportService`

#### Scenario: Constant naming unchanged
- **WHEN** defining module-level constants
- **THEN** constants use SCREAMING_SNAKE_CASE: `DATABASE_URL`, `MAX_UPLOAD_SIZE`, `PROCESSING_MODE_LOCAL`

#### Scenario: Private method naming
- **WHEN** defining private methods
- **THEN** method names use leading underscore with camelCase: `def _validateStep()`, `def _parseResponse()`

### Requirement: Code Style - TypeScript Naming
TypeScript/React code SHALL continue using camelCase for functions and variables, PascalCase for components and types. No changes required as frontend already follows camelCase.

#### Scenario: TypeScript naming consistency maintained
- **WHEN** defining TypeScript functions, variables, or React components
- **THEN** existing naming conventions remain: `function useSession()`, `const sessionId`, `interface SessionData`, `class ChatPanel`

### Requirement: Architecture Patterns - Database Schema
Database column names SHALL use camelCase. Table names MAY remain lowercase with underscores per SQL conventions.

#### Scenario: Database column naming
- **WHEN** defining or querying database columns
- **THEN** column names use camelCase: `gradeLevel`, `userId`, `createdAt`, `isDraft`

#### Scenario: Database queries with camelCase
- **WHEN** writing SQL queries
- **THEN** columns are referenced in camelCase, optionally quoted: `SELECT "userId", "gradeLevel" FROM sessions`

#### Scenario: ORM mapping uses camelCase
- **WHEN** SQLAlchemy models define column mappings
- **THEN** column names match camelCase: `userId = Column("userId", String)`

## ADDED Requirements

### Requirement: Linting Configuration
Ruff linting SHALL disable PEP 8 snake_case enforcement and allow camelCase naming patterns in Python code.

#### Scenario: Ruff allows camelCase functions
- **WHEN** running Ruff linter on Python code with camelCase functions
- **THEN** no naming violations are reported

#### Scenario: Test function naming exception
- **WHEN** pytest test functions use snake_case (e.g., `def test_user_can_create_lesson()`)
- **THEN** Ruff allows snake_case in test files via per-file-ignores

#### Scenario: Constants still enforced
- **WHEN** defining constants in non-SCREAMING_SNAKE_CASE
- **THEN** Ruff reports violation (constants must be SCREAMING_SNAKE_CASE)

### Requirement: Testing Strategy - Test Naming
Test function names MAY retain snake_case naming to align with pytest conventions and readability, creating a single exception to the camelCase standard.

#### Scenario: Pytest test functions use snake_case
- **WHEN** defining pytest test functions
- **THEN** function names use `test_` prefix with snake_case: `def test_create_lesson_with_standards()`

#### Scenario: Test fixtures use camelCase
- **WHEN** defining pytest fixtures
- **THEN** fixture names use camelCase: `@pytest.fixture def sessionRepository()`

#### Scenario: Test assertions use camelCase
- **WHEN** accessing object properties in test assertions
- **THEN** properties use camelCase: `assert lesson.gradeLevel == "5"`

### Requirement: Git Workflow - Import Statement Updates
Import statements SHALL reflect camelCase module names across the codebase.

#### Scenario: Backend imports use camelCase modules
- **WHEN** importing Python modules
- **THEN** imports reference camelCase names: `from backend.services.exportService import ExportService`

#### Scenario: Relative imports use camelCase
- **WHEN** using relative imports
- **THEN** module names are camelCase: `from ..repositories.lessonRepository import LessonRepository`

## REMOVED Requirements

### Requirement: Code Style - Python snake_case Convention
**Reason**: Replaced with camelCase standard for stack-wide consistency
**Migration**: Convert all snake_case functions, variables, and modules to camelCase

#### Scenario: Previous snake_case functions
- **WHEN** functions were previously named `def create_lesson()`
- **THEN** this convention is removed, all functions now use camelCase: `def createLesson()`

### Requirement: Architecture Patterns - Conversion Layer
**Reason**: CamelModel and conversion utilities no longer needed with native camelCase
**Migration**: Remove CamelModel, to_camel_case, and camelize utilities

#### Scenario: Previous conversion utilities
- **WHEN** code previously used `to_camel_case()` or `camelize()` helpers
- **THEN** these utilities are removed from codebase

## RENAMED Requirements

None - no requirements are being renamed, only modified or added/removed.
