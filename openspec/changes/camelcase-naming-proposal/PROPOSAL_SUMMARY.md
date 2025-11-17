# OpenSpec Proposal Summary: Complete camelCase Naming Conversion

## Change ID
`camelcase-naming-proposal`

## Status
✅ DRAFT - Ready for Review

## Overview
This comprehensive proposal establishes camelCase as the single naming convention across the entire PocketMusec codebase, eliminating the mixed snake_case/camelCase conventions that create friction at API boundaries and require conversion layers.

## What Was Created

### Core Documents
1. **`proposal.md`** (4,800+ words)
   - Executive summary and rationale
   - Problem statement with 5 key friction points
   - Detailed impact analysis
   - Breaking changes documentation
   - Alternatives considered (3 options)
   - 8 open questions for stakeholder input
   - Phased rollout strategy

2. **`design.md`** (7,500+ words)
   - 8 major architectural decisions with rationales
   - Migration plan across 6 phases
   - Risk analysis and mitigation strategies
   - Testing strategy
   - Monitoring and observability plan
   - Rollback procedures
   - 10-15 day timeline estimate

3. **`tasks.md`** (200+ tasks)
   - Pre-migration preparation (10 tasks)
   - Phase 1: Backend functions and variables (30+ tasks)
   - Phase 2: Database schema migration (40+ tasks)
   - Phase 3: API contracts and Pydantic models (50+ tasks)
   - Phase 4: Frontend type definitions (20+ tasks)
   - Phase 5: CLI and configuration (10+ tasks)
   - Phase 6: Documentation and cleanup (20+ tasks)
   - Post-migration monitoring checklist

### Spec Deltas
Created delta specifications for 4 critical capabilities:

1. **`specs/api-server/spec.md`**
   - 5 MODIFIED requirements (API response format, request format, Pydantic naming, API versioning, WebSocket messages)
   - 2 ADDED requirements (route handler naming, OpenAPI conformance)
   - 2 REMOVED requirements (CamelModel, conversion layer)
   - 15+ scenarios covering all API contract changes

2. **`specs/project-conventions/spec.md`**
   - 3 MODIFIED requirements (Python naming, TypeScript naming, database schema)
   - 3 ADDED requirements (linting config, test naming, import statements)
   - 2 REMOVED requirements (snake_case convention, conversion utilities)
   - 17+ scenarios defining new coding standards

3. **`specs/session-management/spec.md`**
   - 4 MODIFIED requirements (data model, API endpoints, repository, WebSocket messages)
   - 1 ADDED requirement (query parameter naming)
   - 12+ scenarios showing concrete session API examples

4. **`specs/lesson-generation/spec.md`**
   - 5 MODIFIED requirements (data model, repository, PocketFlow nodes, API endpoints, service layer)
   - 1 ADDED requirement (JSON schema field naming)
   - 14+ scenarios covering lesson generation pipeline

## Scope and Impact

### Codebase Coverage
- **Backend**: ~150+ Python files affected
- **Database**: All tables and columns (requires migration)
- **API**: All endpoints (v1 deprecated, v2 introduced)
- **Frontend**: Type definitions and conversion code (~20+ files)
- **Tests**: All test files (~50+ files)
- **CLI**: All Typer commands (~10+ files)
- **Docs**: All API and code documentation

### Breaking Changes
- ✗ All Python function calls must be updated
- ✗ All database queries must use new column names
- ✗ All API clients must update to v2 endpoints
- ✗ All import statements must reflect new module names
- ✗ All third-party integrations may need updates

### Key Decisions
1. **Phased Migration**: 6 sequential phases over 10-15 days (not atomic)
2. **Database Columns**: Convert all to camelCase (requires migration)
3. **Module Names**: Python files use camelCase (breaks PEP 8)
4. **Test Functions**: Keep snake_case (single exception)
5. **Constants**: Keep SCREAMING_SNAKE_CASE (universal convention)
6. **API Versioning**: Introduce v2 with 6-month v1 deprecation
7. **Type Generation**: Eliminate CamelModel, use direct Pydantic → TypeScript

### Risk Profile
- **High Risk**: Database migration (Phase 2)
- **High Risk**: API contract changes (Phase 3)
- **Medium Risk**: Python ecosystem tool compatibility
- **Medium Risk**: External API consumer breakage
- **High Risk**: Developer resistance to non-PEP 8 conventions

## Benefits vs Drawbacks

### Benefits ✓
- Single naming convention eliminates context switching
- No conversion layer overhead
- Simpler API contracts (no transform required)
- Direct type generation Python → TypeScript
- Reduced cognitive load during development
- Better alignment with JSON/REST industry standards

### Drawbacks ✗
- Violates PEP 8 and Python community standards
- High migration risk and effort (10-15 days)
- Breaks Python ecosystem tool compatibility
- Large-scale refactoring with high error potential
- May cause confusion for Python developers
- Requires disabling standard linting rules

## Timeline

```
Phase 1: Backend Functions      [2-3 days]
Phase 2: Database Migration     [1 day + maintenance window]
Phase 3: API Contracts          [2-3 days]
Phase 4: Frontend Types         [1-2 days]
Phase 5: CLI & Config           [1 day]
Phase 6: Documentation          [1-2 days]
─────────────────────────────────────────
Total:                          [10-15 days]

v1 API Deprecation:             [+6 months]
```

## Open Questions for Review

1. **Database table names**: camelCase or keep snake_case (SQL standard)?
2. **Test naming**: Keep snake_case or convert to camelCase?
3. **Environment variables**: Keep SCREAMING_SNAKE_CASE or convert?
4. **Constants**: Keep SCREAMING_SNAKE_CASE or switch to SCREAMING_CAMEL_CASE?
5. **External APIs**: Do we have consumers that need early notice?
6. **Migration approach**: Atomic or phased? (Proposal recommends phased)
7. **Rollback strategy**: At what error threshold do we rollback?
8. **Python tooling**: Which tools support camelCase, which need alternatives?

## Validation Status

### Manual Validation Performed ✓
- ✓ All spec deltas have MODIFIED/ADDED/REMOVED sections
- ✓ All requirements have at least one Scenario
- ✓ All scenarios use `#### Scenario:` format (4 hashtags)
- ✓ Proposal has Why/What Changes/Impact sections
- ✓ Design document has Context/Goals/Decisions/Migration Plan
- ✓ Tasks are organized by phase with clear dependencies
- ✓ No duplicate change IDs found

### Automated Validation
- ⚠️ `openspec validate --strict` not run (tool not available in environment)
- Recommend running validation once openspec CLI is available

## Next Steps

1. **Review & Discussion**
   - Present proposal to team and stakeholders
   - Address open questions
   - Gather feedback on phasing strategy
   - Assess appetite for PEP 8 deviation

2. **Decision Gate**
   - Approve/reject proposal
   - If approved: Confirm migration timeline
   - If rejected: Consider Alternative 1 (Frontend-only) or Alternative 2 (Enhanced conversion)

3. **Pre-Implementation**
   - Establish baseline metrics
   - Create comprehensive test coverage (target >80%)
   - Set up staging environment
   - Schedule database maintenance window

4. **Implementation**
   - Execute phases 1-6 sequentially
   - Validate at each phase gate
   - Monitor metrics throughout

## Affected Capabilities (Spec Deltas Created)

- ✓ `api-server` - Core API contract changes
- ✓ `project-conventions` - New coding standards
- ✓ `session-management` - Example feature impact
- ✓ `lesson-generation` - Example feature impact

### Additional Capabilities Affected (Specs Not Yet Created)
- `lesson-presentations` - Presentation API and service
- `standards-ingestion` - Ingestion pipeline modules
- `citation-support` - Citation service naming
- `web-interface` - Frontend components (minimal)
- `cli-workflow` - CLI command parameters
- `user-authentication` - Auth endpoints (if exists)
- `workspace-shell` - Desktop integration

These additional capabilities should have spec deltas created during implementation.

## Documentation

All documentation is complete and comprehensive:
- ✓ Clear rationale and problem statement
- ✓ Detailed technical design with 8 decisions
- ✓ Phased implementation plan
- ✓ Risk analysis and mitigation
- ✓ Rollback procedures
- ✓ Success criteria defined
- ✓ Timeline estimated
- ✓ Monitoring plan documented

## Recommendation

This proposal represents a **significant architectural change** that trades Python community standards for full-stack consistency. The team should carefully consider:

1. Whether the benefits (unified naming, no conversion layer) outweigh the costs (PEP 8 violation, high migration effort)
2. Whether the 10-15 day migration effort is acceptable
3. Whether the 6-month API deprecation period is sufficient
4. Whether alternative approaches (frontend-only, enhanced conversion) might be preferable

The proposal is **technically sound and well-documented**, but the decision to proceed should be based on team priorities, risk tolerance, and long-term maintenance philosophy.

---

**Created**: 2025-11-17
**Change ID**: `camelcase-naming-proposal`
**Status**: Ready for stakeholder review
