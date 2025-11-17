# Change Proposal: Complete camelCase Naming Conversion

**Change ID**: `camelcase-naming-proposal`
**Status**: DRAFT
**Created**: 2025-11-17
**Author**: AI Assistant

## Summary
PocketMusec currently uses mixed naming conventions: snake_case in Python backend following Python community standards (PEP 8), camelCase in TypeScript frontend following JavaScript conventions, and snake_case in database schema. While this follows established language-specific conventions, it creates friction at API boundaries, requires constant mental context switching, adds complexity through conversion layers (CamelModel), and makes the codebase harder to reason about holistically. This proposal standardizes the entire codebase on camelCase with zero exceptions—Python code, database schema, API contracts, configuration files, and all tests will use camelCase naming.

## Why
**Problem Statement:**
1. **Cognitive overhead** – Developers must remember which convention applies in each context (snake_case in backend, camelCase in frontend), leading to mistakes and slower development velocity.
2. **API boundary friction** – Current CamelModel conversion creates a lossy/error-prone bridge where request payloads use snake_case but responses use camelCase, requiring manual field mapping in frontend hooks.
3. **Inconsistent test data** – Tests mix snake_case mock data (created_at) with camelCase expectations (createdAt), masking real integration issues.
4. **Configuration complexity** – The to_camel_case utility and CamelModel alias_generator add maintenance burden and obscure the true API contract.
5. **Type system gaps** – Missing TypeScript definitions (./lib/types) stem from the conversion layer hiding schema truth.
6. **Tooling conflicts** – Ruff linting enforces snake_case while the project needs camelCase, requiring constant override pragmas or disabling checks.

**Opportunity:**
- Single, unified naming convention across full stack eliminates context switching
- Direct API contracts without lossy conversion layers
- Simpler type generation (Python → TypeScript)
- Cleaner, more maintainable codebase aligned with modern full-stack practices
- Better alignment with GraphQL, JSON-API, and modern REST conventions which favor camelCase

## What Changes
This change affects every layer of the application and requires coordinated updates across the entire codebase:

### Backend Python (BREAKING)
- **Functions**: `create_lesson()` → `createLesson()`, `list_lessons_for_user()` → `listLessonsForUser()`
- **Variables**: `grade_level` → `gradeLevel`, `user_id` → `userId`, `is_draft` → `isDraft`
- **Module names**: `export_service.py` → `exportService.py`, `lesson_repository.py` → `lessonRepository.py`
- **Private methods**: `_validate_step()` → `_validateStep()` (keep leading underscore convention)
- **Constants**: Convert `PROCESSING_MODE` → `PROCESSING_MODE` (keep SCREAMING_SNAKE_CASE for constants)
- **Remove CamelModel**: Eliminate conversion layer since Python fields will natively match JSON
- **Update imports**: All imports must reflect new module names

### Database Schema (BREAKING - Requires Migration)
- **Tables**: Keep as-is (lowercase with underscores is SQL standard) OR convert to camelCase if consistency demanded
- **Columns**: `grade_level` → `gradeLevel`, `created_at` → `createdAt`, `user_id` → `userId`
- **Indexes**: Update all index definitions to match new column names
- **Foreign keys**: Update constraint definitions

### API Layer (BREAKING)
- **Endpoints**: `/api/sessions` → `/api/sessions` (keep lowercase URLs as industry standard)
- **Request fields**: Already snake_case → will become camelCase natively
- **Response fields**: Already camelCase via CamelModel → will be camelCase natively (no conversion)
- **Path parameters**: `{session_id}` → `{sessionId}`
- **Query parameters**: `?grade_level=5` → `?gradeLevel=5`

### Configuration & Environment
- **Environment variables**: `DATABASE_URL` → keep SCREAMING_SNAKE_CASE (OS convention)
- **Config keys**: `processing_mode` → `processingMode` in JSON configs
- **pyproject.toml**: Update Ruff rules to disable snake_case enforcement (remove "N" selector)

### Frontend TypeScript
- **Minimal changes** – Already uses camelCase
- **Remove conversion code** – Delete manual field mapping in hooks (useSession, useDrafts)
- **Update API types** – Fix missing type definitions to match new backend contracts

### Tests
- **Test function names**: `test_create_lesson()` → `testCreateLesson()` OR keep snake_case (pytest convention)
- **Mock data**: Update all fixtures to use camelCase fields
- **Assertions**: Update field references in assertions

### Documentation
- **API docs**: Update all OpenAPI schemas to reflect camelCase
- **Code comments**: Update references to renamed functions/variables
- **README**: Document new naming convention as project standard

## Impact

### Breaking Changes
- **BREAKING**: All Python function calls must be updated
- **BREAKING**: All database queries must use new column names
- **BREAKING**: All API clients must update request/response field names
- **BREAKING**: All environment variable references in code must update
- **BREAKING**: All import statements must reflect new module names

### Affected Capabilities
This change touches virtually every capability in the system:
- `api-server` – All FastAPI routes and Pydantic models
- `session-management` – Session repository, API endpoints, frontend hooks
- `lesson-generation` – Lesson repository, PocketFlow nodes, generation logic
- `lesson-presentations` – Presentation service, repository, API endpoints
- `user-authentication` – User repository, auth endpoints (if exists)
- `standards-ingestion` – Ingestion pipeline, parser modules
- `citation-support` – Citation service and repository
- `web-interface` – All React components (minimal impact, mostly type updates)
- `cli-workflow` – CLI commands, Typer parameter names
- `workspace-shell` – Desktop/Electron integration

### Affected Code Areas
- **Backend**: ~150+ Python files
- **Database**: All schema files, migrations, and seed data
- **API**: All FastAPI routers and Pydantic models (~30+ files)
- **Frontend**: Type definitions and conversion utilities (~20+ files)
- **Tests**: All test files (~50+ files)
- **CLI**: Typer commands (~10+ files)
- **Docs**: All documentation and examples

### Migration Risks
1. **Database downtime** – Column renames require careful migration with potential service interruption
2. **API compatibility** – Breaking change for any external API consumers
3. **Development disruption** – Large-scale find/replace with high error risk
4. **Tooling compatibility** – May conflict with Python ecosystem tools expecting snake_case
5. **Team convention shift** – Requires retraining developers accustomed to PEP 8

### Benefits
- ✓ Single naming convention across entire stack
- ✓ No conversion layer overhead
- ✓ Simpler API contracts
- ✓ Direct type generation Python → TypeScript
- ✓ Reduced cognitive load during development
- ✓ Better alignment with JSON/REST industry conventions

### Drawbacks
- ✗ Violates PEP 8 and Python community standards
- ✗ Conflicts with Python standard library naming (snake_case)
- ✗ Reduces compatibility with Python ecosystem tools
- ✗ High migration risk and effort
- ✗ Potential confusion for Python developers joining project
- ✗ May require disabling linting rules that enforce Python conventions

## Alternatives Considered

### Alternative 1: Keep Current Hybrid (Status Quo)
- **Pro**: Respects language-specific conventions, no breaking changes
- **Con**: Maintains cognitive overhead, conversion complexity, and API boundary friction
- **Decision**: Rejected – User explicitly requested full camelCase conversion

### Alternative 2: Frontend-Only Standardization
- **Pro**: Minimal backend changes, respects Python conventions
- **Con**: Doesn't eliminate conversion layer or context switching
- **Decision**: Rejected – User requested "no exceptions"

### Alternative 3: Backend snake_case with Improved Conversion
- **Pro**: Keep Python conventions, improve CamelModel reliability
- **Con**: Still requires conversion layer and dual mental models
- **Decision**: Rejected – User requested complete camelCase adoption

### Alternative 4: GraphQL Layer
- **Pro**: Natural camelCase in schema, can map to backend snake_case
- **Con**: Major architecture change, doesn't address database or Python code
- **Decision**: Out of scope – Different proposal needed

## Open Questions
1. **Database table names** – Should table names also convert to camelCase or stay snake_case (SQL standard)?
2. **Test naming** – Should pytest test functions keep snake_case (pytest convention) or convert to camelCase?
3. **Environment variables** – Should ENV_VARS stay SCREAMING_SNAKE_CASE (OS convention) or convert?
4. **Constants** – Should global constants keep SCREAMING_SNAKE_CASE or switch to SCREAMING_CAMEL_CASE?
5. **External API consumers** – Do we need to version the API or maintain backward compatibility?
6. **Migration timeline** – Should this be done atomically or phased by subsystem?
7. **Rollback plan** – What's the rollback strategy if issues emerge post-deployment?
8. **Python tooling** – Which linters/formatters support camelCase Python, and do we need custom rules?

## Dependencies & Prerequisites
- Database migration toolkit ready (Alembic configured for column renames)
- Comprehensive test coverage to catch regressions
- API versioning strategy if backward compatibility required
- Team agreement on new conventions and documentation
- Updated linting configuration (Ruff, MyPy, Pylint)
- Type generation tooling (Pydantic → TypeScript)

## Success Criteria
- Zero snake_case usage in Python code except constants and test names (if retained)
- All database columns use camelCase
- All API contracts use camelCase in requests and responses
- No CamelModel or conversion utilities remain
- All tests pass with new naming
- Updated documentation reflects new standards
- Linting enforces camelCase conventions
- Type generation produces consistent TypeScript types
- No cognitive friction when moving between frontend and backend code

## Phasing Strategy (Recommended)
Given the scope, consider phased rollout:
1. **Phase 1**: Backend function/variable names (non-API)
2. **Phase 2**: Database schema migration
3. **Phase 3**: API contracts and Pydantic models
4. **Phase 4**: Frontend updates and type definitions
5. **Phase 5**: CLI and tooling
6. **Phase 6**: Documentation and examples

Each phase should be completed, tested, and validated before proceeding to the next.
