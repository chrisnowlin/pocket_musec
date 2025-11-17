# Design Document: Complete camelCase Naming Conversion

## Context
PocketMusec currently follows language-specific naming conventions (Python snake_case, JavaScript camelCase) which creates friction at system boundaries. This design document outlines the technical approach for converting the entire codebase to camelCase naming with zero exceptions, a significant departure from Python community standards (PEP 8) but aligned with the goal of stack-wide consistency.

## Goals
- Establish camelCase as the single naming convention across all code, configuration, and data layers
- Eliminate conversion utilities (CamelModel, to_camel_case) and API boundary mapping
- Enable direct type generation from Python to TypeScript without transformation
- Reduce cognitive overhead when working across stack layers
- Maintain system stability during migration with minimal downtime

## Non-Goals
- Changing external API URLs (endpoints stay lowercase as industry standard: `/api/sessions`)
- Converting environment variables to camelCase (keep SCREAMING_SNAKE_CASE per OS convention)
- Modifying third-party library interfaces or dependencies
- Supporting dual naming conventions or backward compatibility after migration completes

## Architectural Decisions

### Decision 1: Atomic vs Phased Migration
**Choice**: Phased migration across 6 distinct phases

**Rationale**:
- Atomic migration carries too much risk given codebase size (~150+ Python files)
- Phased approach allows validation at each stage
- Enables rollback at phase boundaries if critical issues emerge
- Reduces blast radius of potential bugs

**Alternatives Considered**:
- **Atomic migration**: Single large commit changing everything at once
  - Pro: No interim hybrid state
  - Con: High risk, difficult to debug, large merge conflicts
- **Parallel branches**: Run old and new side-by-side
  - Pro: Can switch between versions
  - Con: Doubles maintenance burden, complicates deployment

**Trade-offs**:
- Phased approach extends migration timeline (days to weeks vs hours)
- Creates temporary inconsistency during transition
- Requires careful sequencing to avoid broken intermediate states

### Decision 2: Database Column Naming Strategy
**Choice**: Convert all database columns to camelCase

**Rationale**:
- Consistency with code layer eliminates ORM mapping overhead
- SQLite supports quoted identifiers for camelCase: `SELECT "userId" FROM sessions`
- Modern ORMs (SQLAlchemy) handle non-snake_case columns well
- Eliminates need for column aliasing in queries

**Alternatives Considered**:
- **Keep snake_case tables/columns**: Follow SQL standard conventions
  - Pro: Aligns with PostgreSQL/MySQL community norms
  - Con: Maintains conversion layer in ORM, inconsistent with goal
- **camelCase tables only**: Keep columns snake_case
  - Pro: Partial consistency
  - Con: Doesn't solve ORM mapping problem

**Migration Strategy**:
```sql
-- Use ALTER TABLE RENAME for each column
ALTER TABLE sessions RENAME COLUMN grade_level TO gradeLevel;
ALTER TABLE sessions RENAME COLUMN user_id TO userId;
-- Repeat for all tables and columns
```

**Trade-offs**:
- Requires database downtime during migration (estimate 5-10 minutes for full schema)
- Breaking change for any raw SQL queries
- May require additional quoting in queries: `"gradeLevel"` vs `grade_level`

### Decision 3: Python Module and File Naming
**Choice**: Convert all Python module files to camelCase (export_service.py → exportService.py)

**Rationale**:
- Aligns with full-stack consistency goal
- Python 3.x supports camelCase module names without issues
- Import statements become: `from backend.services.exportService import ExportService`

**Alternatives Considered**:
- **Keep snake_case modules**: Python standard, easier imports
  - Pro: Follows PEP 8, compatible with tooling
  - Con: Breaks stack consistency, maintains cognitive friction
- **Flat namespace**: Move everything to single directory
  - Pro: Simplifies imports
  - Con: Loses organizational structure

**Trade-offs**:
- Conflicts with Python community standards (PEP 8 recommends snake_case modules)
- May confuse developers expecting traditional Python structure
- Requires updating all import statements across codebase

### Decision 4: Test Function Naming
**Choice**: Keep test functions in snake_case (pytest convention)

**Rationale**:
- Pytest discovery relies on `test_` prefix which is snake_case
- Test readability benefits from descriptive snake_case: `test_user_can_create_lesson_with_multiple_standards`
- Tests are developer-facing, not runtime code
- Allows one exception that aligns with testing framework expectations

**Alternatives Considered**:
- **Convert tests to camelCase**: `testUserCanCreateLessonWithMultipleStandards()`
  - Pro: Full consistency with no exceptions
  - Con: Harder to read, may break pytest discovery
- **Use CamelCase with decorators**: `@pytest.mark.test` on camelCase functions
  - Pro: Consistent naming
  - Con: Requires custom pytest configuration

**Trade-offs**:
- Creates single exception to "no exceptions" rule
- Maintains Python testing community conventions
- Test code differs from production code style

### Decision 5: Constant Naming Convention
**Choice**: Keep global constants in SCREAMING_SNAKE_CASE

**Rationale**:
- Universal convention across most programming languages
- Immediately distinguishes constants from variables
- Python typing system (Final, Literal) expects this pattern
- Aligns with environment variable naming

**Examples**:
```python
DATABASE_URL = "sqlite:///data/db.sqlite"
MAX_UPLOAD_SIZE = 10_000_000
PROCESSING_MODE_LOCAL = "local"
PROCESSING_MODE_CLOUD = "cloud"
```

**Alternatives Considered**:
- **SCREAMING_CAMEL_CASE**: `DATABASEURL`, `MAXUPLOADSIZE`
  - Pro: Technically camelCase-derived
  - Con: Reduces readability, uncommon in any language
- **camelCase**: `databaseUrl`, `maxUploadSize`
  - Pro: Consistent with variables
  - Con: Loses visual distinction for constants

### Decision 6: Linting and Formatting Configuration
**Choice**: Disable PEP 8 naming checks in Ruff, create custom rules for camelCase enforcement

**Rationale**:
- Ruff "N" selector enforces snake_case (PEP 8), must be removed
- Custom rules can enforce camelCase patterns
- Black formatter doesn't care about naming, no changes needed

**Configuration Changes**:
```toml
# pyproject.toml
[tool.ruff]
select = ["E", "F", "W", "I", "B", "C90"]  # Remove "N"
ignore = ["E501", "B008", "N802", "N803", "N806"]  # Ignore all naming rules

[tool.ruff.per-file-ignores]
"test_*.py" = ["N802"]  # Allow snake_case in tests
```

**Alternatives Considered**:
- **Keep Ruff defaults with per-file ignores**: `# noqa: N802` on every function
  - Pro: Maintains standard linting
  - Con: Noisy, requires constant overrides
- **Switch to different linter**: Use Pylint with custom config
  - Pro: More configurable
  - Con: Adds tool complexity

### Decision 7: API Versioning Strategy
**Choice**: Introduce `/api/v2/` namespace for camelCase contracts, maintain `/api/v1/` with conversion layer for 6-month deprecation period

**Rationale**:
- Allows external API consumers time to migrate
- Avoids breaking existing integrations immediately
- Clear signal of breaking change via version bump

**Implementation**:
```python
# v1 routes (legacy, with conversion)
@router.get("/api/v1/sessions")
async def list_sessions_v1():
    data = await sessionRepository.listSessions()
    return snake_case_converter(data)  # Convert back for compatibility

# v2 routes (native camelCase)
@router.get("/api/v2/sessions")
async def listSessions():
    return await sessionRepository.listSessions()
```

**Alternatives Considered**:
- **Immediate breaking change**: Replace v1 with camelCase
  - Pro: Faster migration, no dual maintenance
  - Con: Breaks external consumers without notice
- **Content negotiation**: Use headers to select format
  - Pro: Same URL, format based on header
  - Con: Complex to implement and maintain

**Trade-offs**:
- Doubles API surface area during deprecation period
- Requires maintaining conversion layer for 6 months
- Adds complexity to routing and documentation

### Decision 8: Type Generation Pipeline
**Choice**: Eliminate CamelModel, use direct Pydantic → TypeScript generation with native camelCase

**Rationale**:
- Python models already in camelCase, no transformation needed
- Tools like `pydantic-to-typescript` or `datamodel-code-generator` can generate types directly
- Eliminates runtime conversion overhead

**Implementation**:
```python
# Before (with CamelModel)
class SessionResponse(CamelModel):
    grade_level: str  # Converted to gradeLevel in JSON

# After (native camelCase)
class SessionResponse(BaseModel):
    gradeLevel: str  # Native Python field

    model_config = ConfigDict(from_attributes=True)
```

**Type Generation**:
```bash
# Generate TypeScript types from Pydantic models
pydantic-to-typescript --module backend.models --output frontend/src/types/api.ts
```

**Alternatives Considered**:
- **Keep CamelModel, improve generation**: Enhance alias_generator
  - Pro: Less code change
  - Con: Still requires conversion layer
- **Manual type definitions**: Write TypeScript types by hand
  - Pro: Full control
  - Con: High maintenance burden, error-prone

## Migration Plan

### Phase 1: Backend Functions and Variables (Non-API)
**Scope**: Convert internal Python functions, variables, and private methods
**Duration**: 2-3 days
**Risk**: Medium (internal only, no API changes)

**Steps**:
1. Update backend service layer functions: `create_lesson` → `createLesson`
2. Update repository methods: `list_sessions_for_user` → `listSessionsForUser`
3. Update internal variables: `grade_level` → `gradeLevel`
4. Update imports and references
5. Run full test suite to catch regressions

**Validation**:
- All unit tests pass
- Integration tests pass
- No API contract changes yet

### Phase 2: Database Schema Migration
**Scope**: Rename all database columns to camelCase
**Duration**: 1 day (includes downtime)
**Risk**: High (requires careful migration, potential data issues)

**Steps**:
1. Generate migration script with column renames
2. Test migration on staging database with production data copy
3. Schedule maintenance window (estimate 10-15 minutes)
4. Run migration on production
5. Validate data integrity
6. Update all SQL queries to use new column names

**Rollback**:
- Keep reverse migration script ready: `gradeLevel → grade_level`
- Database backup before migration
- If issues detected within 1 hour, rollback immediately

**Validation**:
- All queries return expected data
- No data loss or corruption
- Application can read/write successfully

### Phase 3: API Contracts and Pydantic Models
**Scope**: Convert FastAPI routers, Pydantic models, API endpoints
**Duration**: 2-3 days
**Risk**: High (breaking change for API consumers)

**Steps**:
1. Remove CamelModel base class
2. Rename Pydantic model fields to camelCase
3. Update FastAPI route handlers
4. Update request/response serialization
5. Deploy v2 API namespace
6. Add v1 → v2 conversion layer for deprecation period

**Validation**:
- v2 endpoints return camelCase responses
- v1 endpoints still work with conversion
- Postman/API tests pass for both versions
- Frontend successfully consumes v2 endpoints

### Phase 4: Frontend Type Definitions
**Scope**: Remove conversion utilities, update TypeScript types
**Duration**: 1-2 days
**Risk**: Low (TypeScript will catch type errors)

**Steps**:
1. Generate TypeScript types from Pydantic models
2. Remove manual conversion code in hooks (useSession, useDrafts)
3. Update API client to use v2 endpoints
4. Remove snake_case type definitions
5. Update component prop types

**Validation**:
- TypeScript compilation succeeds with zero errors
- All frontend tests pass
- UI displays data correctly
- No runtime type errors in browser console

### Phase 5: CLI and Configuration
**Scope**: Update Typer CLI commands, configuration files
**Duration**: 1 day
**Risk**: Low (CLI is local-only)

**Steps**:
1. Rename CLI command parameters to camelCase
2. Update config file keys (JSON configs)
3. Update CLI help text and examples
4. Test CLI workflows end-to-end

**Validation**:
- CLI commands execute successfully
- Configuration loads correctly
- Help text is accurate

### Phase 6: Documentation and Cleanup
**Scope**: Update docs, remove old code, finalize migration
**Duration**: 1-2 days
**Risk**: Low (documentation only)

**Steps**:
1. Update OpenAPI schemas to reflect v2 contracts
2. Update README and contributor documentation
3. Remove v1 API endpoints (after 6-month deprecation)
4. Remove conversion utilities (CamelModel, to_camel_case)
5. Update code examples in documentation
6. Archive this OpenSpec change

**Validation**:
- Documentation is accurate and complete
- No dead code remains
- OpenSpec validation passes
- All examples execute successfully

## Risks and Mitigations

### Risk 1: High Error Rate During Migration
**Likelihood**: High
**Impact**: High

**Mitigation**:
- Comprehensive test coverage before starting (>80% coverage target)
- Phased rollout with validation gates
- Automated refactoring tools (AST-based search/replace)
- Code review requirements for all changes
- Staging environment testing with production data snapshots

### Risk 2: Database Migration Failure
**Likelihood**: Medium
**Impact**: Critical

**Mitigation**:
- Practice migration on staging with production data copy
- Database backup before migration
- Rollback script tested and ready
- Maintenance window scheduled during low-usage period
- Monitoring and alerting during migration

### Risk 3: Python Ecosystem Tool Incompatibility
**Likelihood**: Medium
**Impact**: Medium

**Mitigation**:
- Test all dev tools (pytest, mypy, black, ruff) with camelCase code
- Identify incompatible tools and find alternatives
- Document required linting configuration changes
- Create custom rules where needed

### Risk 4: External API Consumer Breakage
**Likelihood**: High (if external consumers exist)
**Impact**: High

**Mitigation**:
- API versioning strategy (v1 with conversion, v2 native)
- 6-month deprecation period for v1
- Clear migration guide for consumers
- Announcement and communication plan
- Monitoring for v1 usage to track migration progress

### Risk 5: Developer Resistance and Confusion
**Likelihood**: High
**Impact**: Medium

**Mitigation**:
- Clear documentation of rationale and benefits
- Team training sessions on new conventions
- Updated linting to enforce new patterns
- Code examples and templates
- Gradual onboarding during phased rollout

### Risk 6: Merge Conflicts with Parallel Work
**Likelihood**: High
**Impact**: Medium

**Mitigation**:
- Feature freeze during migration phases
- Clear communication of migration timeline
- Coordinate with team on branch management
- Use dedicated migration branch
- Rebase/merge frequently during migration

## Testing Strategy

### Unit Tests
- All existing unit tests must pass after each phase
- Update test fixtures to use camelCase fields
- Validate conversion logic in v1 API compatibility layer

### Integration Tests
- End-to-end API tests covering all endpoints
- Database query tests validating new column names
- Frontend integration tests with real API calls

### Performance Tests
- Baseline performance metrics before migration
- Validate no performance regression after removing conversion layer
- Database query performance with camelCase columns

### Manual Testing
- Critical user workflows (lesson generation, session management)
- UI/UX validation in all supported browsers
- CLI command execution and output validation

## Monitoring and Observability

### Metrics to Track
- API error rate (v1 and v2 endpoints)
- Database query latency
- Frontend load time and error rate
- v1 vs v2 API usage percentages
- Type error rate in TypeScript compilation

### Alerts
- Spike in API 500 errors
- Database migration failure
- TypeScript compilation failures
- Significant increase in frontend console errors

### Dashboards
- Migration phase progress
- v1 deprecation timeline and adoption
- Error rate trends
- Performance comparison (before/after)

## Rollback Strategy

### Phase-Level Rollback
Each phase should be independently rollbackable:

**Phase 1 (Backend code)**: Git revert commits
**Phase 2 (Database)**: Run reverse migration script
**Phase 3 (API)**: Route traffic back to v1, disable v2
**Phase 4 (Frontend)**: Revert to previous deployment
**Phase 5 (CLI)**: Revert binary/package to previous version
**Phase 6 (Docs)**: Revert documentation changes

### Critical Rollback Triggers
- Error rate increase >10% in production
- Database migration failure or data corruption
- >50% of integration tests failing
- Critical user-facing bug discovered
- Performance regression >20%

## Open Technical Questions

1. **SQL Quoting**: Do we need to quote all column names in queries (`"userId"`) or can SQLite handle it unquoted?
2. **ORM Configuration**: Does SQLAlchemy need special configuration for camelCase columns?
3. **Migration Downtime**: Can we use online schema change tools to avoid downtime?
4. **Elasticsearch/Indexes**: Do search indexes need rebuilding with new field names?
5. **Cached Data**: Do we need to invalidate Redis/cache with old snake_case keys?
6. **Third-party Integrations**: Are there any external systems that depend on database structure?
7. **Backup Compatibility**: Will backups from pre-migration be restorable post-migration?
8. **Type Generation**: Which tool (pydantic-to-typescript vs datamodel-code-generator) produces better types?

## Success Metrics

### Objective Criteria
- ✓ Zero snake_case usage in Python code (except test names and constants)
- ✓ All database columns in camelCase
- ✓ All API v2 endpoints use camelCase contracts
- ✓ Zero CamelModel or conversion utility references
- ✓ 100% of tests passing
- ✓ TypeScript compilation with zero type errors
- ✓ API documentation updated and accurate
- ✓ <1% error rate increase in production
- ✓ No performance regression
- ✓ All OpenSpec specs updated and validated

### Subjective Criteria
- Developer feedback on reduced cognitive load
- Faster onboarding for new team members
- Reduced API-related bugs
- Improved code review efficiency
- Better IDE autocomplete experience

## Timeline Estimate

**Total Duration**: 10-15 working days

| Phase | Duration | Dependencies | Risk Level |
|-------|----------|--------------|------------|
| Phase 1: Backend Functions | 2-3 days | None | Medium |
| Phase 2: Database Schema | 1 day | Phase 1 | High |
| Phase 3: API Contracts | 2-3 days | Phase 1, 2 | High |
| Phase 4: Frontend Types | 1-2 days | Phase 3 | Low |
| Phase 5: CLI & Config | 1 day | Phase 1, 3 | Low |
| Phase 6: Documentation | 1-2 days | All phases | Low |

**Buffer**: Add 20-30% for unexpected issues, testing, and validation.

**v1 API Deprecation**: 6 months after Phase 3 completion
