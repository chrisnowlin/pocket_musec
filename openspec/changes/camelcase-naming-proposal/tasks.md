# Implementation Tasks: Complete camelCase Naming Conversion

## Pre-Migration Preparation

### 0. Setup and Planning
- [ ] 0.1 Review and approve proposal, design, and spec deltas
- [ ] 0.2 Establish baseline metrics (error rates, performance, test coverage)
- [ ] 0.3 Create comprehensive test coverage report (target >80% coverage)
- [ ] 0.4 Set up staging environment with production data snapshot
- [ ] 0.5 Create dedicated migration branch: `feat/camelcase-migration`
- [ ] 0.6 Announce migration timeline to team and stakeholders
- [ ] 0.7 Schedule maintenance window for database migration
- [ ] 0.8 Prepare monitoring dashboards and alerting
- [ ] 0.9 Document rollback procedures for each phase
- [ ] 0.10 Create automated refactoring scripts (AST-based find/replace)

---

## Phase 1: Backend Functions and Variables (Non-API)

### 1.1 Backend Service Layer
- [ ] 1.1.1 Convert `backend/services/export_service.py` → `exportService.py`
- [ ] 1.1.2 Rename functions: `export_presentation()` → `exportPresentation()`
- [ ] 1.1.3 Convert `backend/services/presentation_service.py` → `presentationService.py`
- [ ] 1.1.4 Rename functions: `create_presentation()` → `createPresentation()`
- [ ] 1.1.5 Update all internal variables in service files to camelCase
- [ ] 1.1.6 Update all imports referencing renamed modules

### 1.2 Repository Layer
- [ ] 1.2.1 Convert `backend/repositories/lesson_repository.py` → `lessonRepository.py`
- [ ] 1.2.2 Rename: `create_lesson()` → `createLesson()`
- [ ] 1.2.3 Rename: `list_lessons_for_user()` → `listLessonsForUser()`
- [ ] 1.2.4 Rename: `list_lessons_for_session()` → `listLessonsForSession()`
- [ ] 1.2.5 Convert `backend/repositories/presentation_repository.py` → `presentationRepository.py`
- [ ] 1.2.6 Rename: `get_presentation_status()` → `getPresentationStatus()`
- [ ] 1.2.7 Convert `backend/repositories/session_repository.py` → `sessionRepository.py`
- [ ] 1.2.8 Update all repository method calls across codebase

### 1.3 Utility Modules
- [ ] 1.3.1 Convert `backend/utils/field_converter.py` → `fieldConverter.py`
- [ ] 1.3.2 Convert `backend/utils/database_field_mapper.py` → `databaseFieldMapper.py`
- [ ] 1.3.3 Rename utility functions to camelCase
- [ ] 1.3.4 Update all utility function calls across codebase

### 1.4 PocketFlow Core
- [ ] 1.4.1 Convert `backend/pocketflow/` module files to camelCase
- [ ] 1.4.2 Rename Node/Flow/Store class methods to camelCase
- [ ] 1.4.3 Update internal variables and parameters
- [ ] 1.4.4 Update all PocketFlow usage across backend

### 1.5 Background Jobs
- [ ] 1.5.1 Convert `backend/jobs/presentation_jobs.py` → `presentationJobs.py`
- [ ] 1.5.2 Rename job functions to camelCase
- [ ] 1.5.3 Update job scheduling and invocation code

### 1.6 Validation and Testing
- [ ] 1.6.1 Update all import statements for renamed modules
- [ ] 1.6.2 Run full backend unit test suite
- [ ] 1.6.3 Fix any failing tests due to renamed functions
- [ ] 1.6.4 Run integration tests
- [ ] 1.6.5 Validate no API contract changes yet (phase 1 is internal only)
- [ ] 1.6.6 Code review for phase 1 changes
- [ ] 1.6.7 Merge phase 1 to migration branch

---

## Phase 2: Database Schema Migration

### 2.1 Migration Script Preparation
- [ ] 2.1.1 Generate Alembic migration script for column renames
- [ ] 2.1.2 Create reverse migration script (camelCase → snake_case)
- [ ] 2.1.3 Review migration script for correctness
- [ ] 2.1.4 Test migration on local development database
- [ ] 2.1.5 Test reverse migration (rollback) on local database

### 2.2 Sessions Table
- [ ] 2.2.1 Rename: `grade_level` → `gradeLevel`
- [ ] 2.2.2 Rename: `strand_code` → `strandCode`
- [ ] 2.2.3 Rename: `user_id` → `userId`
- [ ] 2.2.4 Rename: `selected_standards` → `selectedStandards`
- [ ] 2.2.5 Rename: `selected_objectives` → `selectedObjectives`
- [ ] 2.2.6 Rename: `additional_context` → `additionalContext`
- [ ] 2.2.7 Rename: `lesson_duration` → `lessonDuration`
- [ ] 2.2.8 Rename: `class_size` → `classSize`
- [ ] 2.2.9 Rename: `created_at` → `createdAt`
- [ ] 2.2.10 Rename: `updated_at` → `updatedAt`
- [ ] 2.2.11 Rename: `selected_model` → `selectedModel`
- [ ] 2.2.12 Update all indexes referencing renamed columns

### 2.3 Lessons Table
- [ ] 2.3.1 Rename: `session_id` → `sessionId`
- [ ] 2.3.2 Rename: `user_id` → `userId`
- [ ] 2.3.3 Rename: `processing_mode` → `processingMode`
- [ ] 2.3.4 Rename: `is_draft` → `isDraft`
- [ ] 2.3.5 Rename: `created_at` → `createdAt`
- [ ] 2.3.6 Rename: `updated_at` → `updatedAt`
- [ ] 2.3.7 Update all indexes and foreign keys

### 2.4 Presentations Table
- [ ] 2.4.1 Rename: `lesson_id` → `lessonId`
- [ ] 2.4.2 Rename: `lesson_revision` → `lessonRevision`
- [ ] 2.4.3 Rename: `export_assets` → `exportAssets`
- [ ] 2.4.4 Rename: `error_code` → `errorCode`
- [ ] 2.4.5 Rename: `error_message` → `errorMessage`
- [ ] 2.4.6 Rename: `created_at` → `createdAt`
- [ ] 2.4.7 Rename: `updated_at` → `updatedAt`
- [ ] 2.4.8 Update all indexes and constraints

### 2.5 Other Tables
- [ ] 2.5.1 Identify and list all other database tables
- [ ] 2.5.2 Rename columns in users table (if exists)
- [ ] 2.5.3 Rename columns in standards table
- [ ] 2.5.4 Rename columns in objectives table
- [ ] 2.5.5 Rename columns in images table
- [ ] 2.5.6 Rename columns in files table
- [ ] 2.5.7 Rename columns in any other tables
- [ ] 2.5.8 Update all foreign key constraints
- [ ] 2.5.9 Update all indexes

### 2.6 Query Updates
- [ ] 2.6.1 Update all raw SQL queries to use camelCase column names
- [ ] 2.6.2 Update SQLAlchemy model field mappings
- [ ] 2.6.3 Add column quoting where needed: `SELECT "userId" FROM sessions`
- [ ] 2.6.4 Update database seed scripts with camelCase columns

### 2.7 Staging Migration
- [ ] 2.7.1 Back up staging database
- [ ] 2.7.2 Run migration on staging environment
- [ ] 2.7.3 Validate data integrity (spot checks)
- [ ] 2.7.4 Run full test suite against staging database
- [ ] 2.7.5 Test rollback script on staging
- [ ] 2.7.6 Restore staging from backup
- [ ] 2.7.7 Re-run migration to confirm repeatability

### 2.8 Production Migration
- [ ] 2.8.1 Announce maintenance window to users
- [ ] 2.8.2 Back up production database (full snapshot)
- [ ] 2.8.3 Enable maintenance mode (take app offline)
- [ ] 2.8.4 Run database migration script
- [ ] 2.8.5 Validate migration completed successfully
- [ ] 2.8.6 Run data integrity checks
- [ ] 2.8.7 Deploy updated backend code with camelCase queries
- [ ] 2.8.8 Disable maintenance mode (bring app online)
- [ ] 2.8.9 Monitor error rates and database performance
- [ ] 2.8.10 Keep rollback script ready for 24 hours

### 2.9 Post-Migration Validation
- [ ] 2.9.1 Verify all database queries execute successfully
- [ ] 2.9.2 Validate no data loss or corruption
- [ ] 2.9.3 Run integration tests against production database
- [ ] 2.9.4 Monitor logs for database-related errors
- [ ] 2.9.5 Code review for phase 2 changes
- [ ] 2.9.6 Merge phase 2 to migration branch

---

## Phase 3: API Contracts and Pydantic Models

### 3.1 Remove CamelModel Conversion Layer
- [ ] 3.1.1 Remove `CamelModel` base class from codebase
- [ ] 3.1.2 Remove `to_camel_case()` utility function
- [ ] 3.1.3 Remove `camelize()` utility function
- [ ] 3.1.4 Remove alias_generator references

### 3.2 Pydantic Models - Session Management
- [ ] 3.2.1 Rename `SessionCreateRequest` fields to camelCase
- [ ] 3.2.2 Update: `grade_level` → `gradeLevel`
- [ ] 3.2.3 Update: `strand_code` → `strandCode`
- [ ] 3.2.4 Update: `standard_id` → `standardId`
- [ ] 3.2.5 Update: `additional_context` → `additionalContext`
- [ ] 3.2.6 Update: `lesson_duration` → `lessonDuration`
- [ ] 3.2.7 Update: `class_size` → `classSize`
- [ ] 3.2.8 Update: `selected_objectives` → `selectedObjectives`
- [ ] 3.2.9 Update: `selected_model` → `selectedModel`
- [ ] 3.2.10 Update `SessionResponse` fields similarly

### 3.3 Pydantic Models - Lessons
- [ ] 3.3.1 Update `LessonCreateRequest` fields to camelCase
- [ ] 3.3.2 Update `LessonResponse` fields to camelCase
- [ ] 3.3.3 Update all lesson-related DTOs

### 3.4 Pydantic Models - Presentations
- [ ] 3.4.1 Update `PresentationCreateRequest` fields to camelCase
- [ ] 3.4.2 Update `PresentationResponse` fields to camelCase
- [ ] 3.4.3 Update `ExportOptions` fields to camelCase

### 3.5 Pydantic Models - Standards and Objectives
- [ ] 3.5.1 Update `Standard` model fields to camelCase
- [ ] 3.5.2 Update `Objective` model fields to camelCase
- [ ] 3.5.3 Update `StandardWithObjectives` fields to camelCase

### 3.6 Pydantic Models - Images and Files
- [ ] 3.6.1 Update `ImageData` model fields to camelCase
- [ ] 3.6.2 Update `ImageClassification` fields to camelCase
- [ ] 3.6.3 Update file-related models to camelCase

### 3.7 FastAPI Routers - Create v2 Endpoints
- [ ] 3.7.1 Create `/api/v2/sessions` router with camelCase contracts
- [ ] 3.7.2 Create `/api/v2/lessons` router with camelCase contracts
- [ ] 3.7.3 Create `/api/v2/presentations` router with camelCase contracts
- [ ] 3.7.4 Create `/api/v2/standards` router with camelCase contracts
- [ ] 3.7.5 Create `/api/v2/images` router with camelCase contracts
- [ ] 3.7.6 Create `/api/v2/workspace/dashboard` endpoint
- [ ] 3.7.7 Update route handlers to use camelCase internally

### 3.8 FastAPI Routers - Maintain v1 Compatibility
- [ ] 3.8.1 Keep `/api/v1/` endpoints with conversion layer
- [ ] 3.8.2 Create snake_case → camelCase converter for v1 requests
- [ ] 3.8.3 Create camelCase → snake_case converter for v1 responses
- [ ] 3.8.4 Add deprecation warnings to v1 responses
- [ ] 3.8.5 Document v1 deprecation timeline (6 months)

### 3.9 Request Parameter Updates
- [ ] 3.9.1 Update path parameters: `{session_id}` → `{sessionId}`
- [ ] 3.9.2 Update query parameters: `?grade_level=5` → `?gradeLevel=5`
- [ ] 3.9.3 Update request body validation

### 3.10 Response Serialization
- [ ] 3.10.1 Validate all v2 responses return camelCase fields
- [ ] 3.10.2 Remove response_model alias generators
- [ ] 3.10.3 Test serialization of nested objects

### 3.11 WebSocket and SSE Updates
- [ ] 3.11.1 Update WebSocket message payloads to camelCase
- [ ] 3.11.2 Update SSE event data to camelCase
- [ ] 3.11.3 Update streaming response formats

### 3.12 API Documentation
- [ ] 3.12.1 Update OpenAPI schema for v2 endpoints
- [ ] 3.12.2 Add request/response examples in camelCase
- [ ] 3.12.3 Update API documentation in `/docs/api/`
- [ ] 3.12.4 Create migration guide for v1 → v2
- [ ] 3.12.5 Document v1 deprecation timeline

### 3.13 Testing and Validation
- [ ] 3.13.1 Create Postman/API test collection for v2 endpoints
- [ ] 3.13.2 Test all v2 endpoints with camelCase payloads
- [ ] 3.13.3 Validate v1 endpoints still work with conversion
- [ ] 3.13.4 Test error responses are camelCase
- [ ] 3.13.5 Run full API integration test suite
- [ ] 3.13.6 Code review for phase 3 changes
- [ ] 3.13.7 Merge phase 3 to migration branch

---

## Phase 4: Frontend Type Definitions and Updates

### 4.1 Type Generation
- [ ] 4.1.1 Install pydantic-to-typescript or equivalent tool
- [ ] 4.1.2 Configure type generation pipeline
- [ ] 4.1.3 Generate TypeScript types from Pydantic v2 models
- [ ] 4.1.4 Create `frontend/src/types/api.ts` with generated types
- [ ] 4.1.5 Validate generated types match API contracts

### 4.2 Remove Conversion Code
- [ ] 4.2.1 Remove snake_case conversion in `useSession` hook
- [ ] 4.2.2 Remove field mapping in `useDrafts` hook
- [ ] 4.2.3 Remove conversion in `useChat` hook
- [ ] 4.2.4 Remove conversion in `useImages` hook
- [ ] 4.2.5 Remove any other manual field mapping code

### 4.3 Update API Client
- [ ] 4.3.1 Update `frontend/src/lib/apiClient.ts` to use v2 endpoints
- [ ] 4.3.2 Update all API URLs: `/api/sessions` → `/api/v2/sessions`
- [ ] 4.3.3 Remove request payload transformation code
- [ ] 4.3.4 Update error handling to expect camelCase errors

### 4.4 Update Type Definitions
- [ ] 4.4.1 Replace `SessionCreatePayload` with generated type
- [ ] 4.4.2 Replace `SessionResponsePayload` with generated type
- [ ] 4.4.3 Replace `DraftItem` interface with generated type
- [ ] 4.4.4 Replace `ImageData` interface with generated type
- [ ] 4.4.5 Update all component prop types
- [ ] 4.4.6 Update all hook return types

### 4.5 Update Hooks
- [ ] 4.5.1 Update `useSession` to consume camelCase responses directly
- [ ] 4.5.2 Update `useDrafts` to consume camelCase responses directly
- [ ] 4.5.3 Update `useChat` to consume camelCase SSE events
- [ ] 4.5.4 Update `useLessons` to use camelCase
- [ ] 4.5.5 Update `usePresentations` to use camelCase
- [ ] 4.5.6 Update `useImages` to use camelCase

### 4.6 Update Zustand Stores
- [ ] 4.6.1 Update `useLessonStore` state to camelCase
- [ ] 4.6.2 Update `useImageStore` state to camelCase
- [ ] 4.6.3 Update `useConversationStore` state to camelCase
- [ ] 4.6.4 Update all store actions to use camelCase

### 4.7 Update React Components
- [ ] 4.7.1 Update `ChatPanel` to use camelCase props
- [ ] 4.7.2 Update `DraftsModal` to use camelCase
- [ ] 4.7.3 Update `LessonEditor` to use camelCase
- [ ] 4.7.4 Update `PresentationGenerator` to use camelCase
- [ ] 4.7.5 Update all other components with API data dependencies

### 4.8 Testing and Validation
- [ ] 4.8.1 Run TypeScript compilation (ensure zero errors)
- [ ] 4.8.2 Run frontend unit tests
- [ ] 4.8.3 Run frontend integration tests
- [ ] 4.8.4 Manual testing: Session creation and management
- [ ] 4.8.5 Manual testing: Lesson generation and editing
- [ ] 4.8.6 Manual testing: Presentation generation
- [ ] 4.8.7 Manual testing: Image upload and management
- [ ] 4.8.8 Validate no console errors in browser
- [ ] 4.8.9 Code review for phase 4 changes
- [ ] 4.8.10 Merge phase 4 to migration branch

---

## Phase 5: CLI and Configuration

### 5.1 CLI Commands
- [ ] 5.1.1 Convert `cli/commands/lesson_generator.py` → `lessonGenerator.py`
- [ ] 5.1.2 Rename CLI command parameters to camelCase in Typer decorators
- [ ] 5.1.3 Update CLI function implementations to use camelCase
- [ ] 5.1.4 Convert `cli/commands/ingestion.py` → `ingestion.py`
- [ ] 5.1.5 Update ingestion command parameters to camelCase

### 5.2 Configuration Files
- [ ] 5.2.1 Update JSON config files to use camelCase keys
- [ ] 5.2.2 Update YAML config files (if any) to use camelCase
- [ ] 5.2.3 Keep environment variables as SCREAMING_SNAKE_CASE
- [ ] 5.2.4 Update config loading code to expect camelCase

### 5.3 CLI Help and Examples
- [ ] 5.3.1 Update CLI help text to show camelCase parameters
- [ ] 5.3.2 Update CLI examples in documentation
- [ ] 5.3.3 Update shell completion scripts if applicable

### 5.4 Testing and Validation
- [ ] 5.4.1 Test CLI lesson generation command
- [ ] 5.4.2 Test CLI ingestion commands
- [ ] 5.4.3 Test config file loading
- [ ] 5.4.4 Validate CLI output formatting
- [ ] 5.4.5 Run CLI integration tests
- [ ] 5.4.6 Code review for phase 5 changes
- [ ] 5.4.7 Merge phase 5 to migration branch

---

## Phase 6: Documentation, Cleanup, and Finalization

### 6.1 OpenAPI Schema Updates
- [ ] 6.1.1 Regenerate OpenAPI schema for v2 endpoints
- [ ] 6.1.2 Add v2 endpoint tags and descriptions
- [ ] 6.1.3 Add request/response examples in camelCase
- [ ] 6.1.4 Mark v1 endpoints as deprecated in schema
- [ ] 6.1.5 Test `/api/docs` renders correctly

### 6.2 API Documentation
- [ ] 6.2.1 Create v1 → v2 migration guide
- [ ] 6.2.2 Document breaking changes and migration steps
- [ ] 6.2.3 Update API endpoint documentation
- [ ] 6.2.4 Add code examples in camelCase
- [ ] 6.2.5 Document deprecation timeline

### 6.3 Code Documentation
- [ ] 6.3.1 Update README with new naming conventions
- [ ] 6.3.2 Update CONTRIBUTING.md with camelCase guidelines
- [ ] 6.3.3 Update code comments referencing renamed functions
- [ ] 6.3.4 Update docstrings with camelCase parameter names

### 6.4 Project Configuration
- [ ] 6.4.1 Update Ruff configuration (remove "N" selector)
- [ ] 6.4.2 Add custom linting rules for camelCase enforcement
- [ ] 6.4.3 Update pre-commit hooks if applicable
- [ ] 6.4.4 Update EditorConfig for naming conventions

### 6.5 OpenSpec Updates
- [ ] 6.5.1 Update `openspec/project.md` with new conventions
- [ ] 6.5.2 Update all affected capability specs
- [ ] 6.5.3 Archive this change proposal
- [ ] 6.5.4 Run `openspec validate --strict`

### 6.6 Remove Old Code (After v1 Deprecation Period)
- [ ] 6.6.1 [6 months later] Remove v1 API endpoints
- [ ] 6.6.2 [6 months later] Remove CamelModel class completely
- [ ] 6.6.3 [6 months later] Remove to_camel_case utility
- [ ] 6.6.4 [6 months later] Remove conversion layer code
- [ ] 6.6.5 [6 months later] Clean up deprecated documentation

### 6.7 Final Validation
- [ ] 6.7.1 Run full test suite (unit + integration + e2e)
- [ ] 6.7.2 Validate all OpenSpec specs pass validation
- [ ] 6.7.3 Check test coverage meets >80% threshold
- [ ] 6.7.4 Run performance benchmarks (compare to baseline)
- [ ] 6.7.5 Validate error rate within acceptable range (<1% increase)
- [ ] 6.7.6 Code review for phase 6 changes

### 6.8 Deployment and Communication
- [ ] 6.8.1 Merge migration branch to main
- [ ] 6.8.2 Tag release with migration notes
- [ ] 6.8.3 Deploy to production
- [ ] 6.8.4 Announce completion to team and stakeholders
- [ ] 6.8.5 Monitor production for 48 hours post-deployment
- [ ] 6.8.6 Gather developer feedback on new conventions

---

## Post-Migration Monitoring (First 2 Weeks)

### Monitoring Checklist
- [ ] Monitor API error rates daily (compare to baseline)
- [ ] Monitor database query performance
- [ ] Monitor frontend error logs
- [ ] Track v1 vs v2 API usage percentages
- [ ] Monitor user-reported issues
- [ ] Track developer feedback on new conventions

### Success Criteria Validation
- [ ] Validate zero snake_case usage in Python code (automated scan)
- [ ] Validate all database columns in camelCase
- [ ] Validate all API v2 endpoints use camelCase
- [ ] Validate zero CamelModel references
- [ ] Validate 100% test pass rate maintained
- [ ] Validate no performance regression
- [ ] Validate error rate increase <1%

---

## Notes

**Estimation**: Total effort: 10-15 working days across 6 phases

**Dependencies**:
- Phases must be completed sequentially (1 → 2 → 3 → 4 → 5 → 6)
- Database migration (Phase 2) requires maintenance window
- API versioning (Phase 3) enables frontend updates (Phase 4)

**Risk Mitigation**:
- Each phase includes validation gate before proceeding
- Rollback procedures documented for each phase
- Code review required for all phases
- Staging environment testing before production deployment

**Critical Path**:
- Phase 2 (Database) is highest risk due to potential downtime
- Phase 3 (API) is blocking for Phase 4 (Frontend)
- Phase 6 should not begin until Phases 1-5 are fully validated
