## 1. Specification & Validation
- [x] 1.1 Review existing lesson-generation and lesson-editing specs
- [x] 1.2 Finalize m2.0 JSON schema requirements in spec deltas
- [x] 1.3 Run `openspec validate add-lesson-json-schema-m2 --strict` and address any issues

## 2. Backend Implementation
- [x] 2.1 Introduce m2.0 lesson document model (Pydantic or JSON Schema)
- [x] 2.2 Update lesson create/update/read endpoints to use the m2.0 model
- [x] 2.3 Enforce schema validation on lesson write operations
- [x] 2.4 Ensure lesson-generation pipeline exposes m2.0-conformant documents at the API boundary
- [x] 2.5 Add backend tests for schema validation and round-trip serialization

## 3. Frontend Implementation
- [x] 3.1 Add or update TypeScript types/interfaces for m2.0 lesson documents
- [x] 3.2 Ensure lesson editor and viewer operate on the m2.0 structure
- [x] 3.3 Adjust any lesson list/detail views to consume the new shape
- [x] 3.4 Add frontend tests for basic m2.0 lesson usage

## 4. Migration & Rollout
- [x] 4.1 Decide migration strategy for any pre-m2.0 lessons
- [x] 4.2 Implement data migration or on-the-fly adapters if needed
- [x] 4.3 Verify end-to-end flows (generate → edit → save → reopen) using m2.0
- [x] 4.4 Update documentation and developer notes to reference the m2.0 schema

