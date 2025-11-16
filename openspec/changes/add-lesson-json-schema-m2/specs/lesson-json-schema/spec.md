# Spec: Milestone 2 Lesson JSON Schema (Version m2.0)

## ADDED Requirements

### Requirement: Versioned Lesson JSON Contract
The system SHALL represent all **Milestone 2 lessons** using a versioned JSON schema identified as `m2.0`.

#### Scenario: Versioned lesson document
- **GIVEN** a lesson is created or updated after the Milestone 2 rollout
- **WHEN** the backend returns that lesson via any lesson read endpoint
- **THEN** the JSON response SHALL include `version: "m2.0"`
- **AND** the document SHALL conform to the `m2.0` structure defined in this spec

#### Scenario: Schema validation on write
- **GIVEN** a client sends a JSON payload to create or update a lesson
- **WHEN** the backend processes the request
- **THEN** the payload SHALL be validated against the `m2.0` schema
- **AND** invalid payloads SHALL be rejected with `400 Bad Request` and a validation error description

---

### Requirement: Top-Level Lesson Metadata
Every `m2.0` lesson JSON document SHALL include top-level metadata fields for identity, timestamps, and revision.

A conforming lesson document MUST have:

```json
{
  "id": "uuid-string",
  "created_at": "ISO-8601 timestamp",
  "updated_at": "ISO-8601 timestamp",
  "version": "m2.0",
  "title": "string",
  "grade": "string",
  "strands": ["CN", "CR", "PR", "RE"],
  "standards": [
    {
      "code": "K.CN.1",
      "title": "string",
      "summary": "string"
    }
  ],
  "objectives": ["string"],
  "content": { /* see Content structure below */ },
  "citations": ["string"],
  "revision": 1
}
```

#### Scenario: Lesson metadata completeness
- **GIVEN** a lesson is generated or edited through the application
- **WHEN** it is saved successfully
- **THEN** the stored lesson SHALL include non-null `id`, `created_at`, `updated_at`, `title`, `grade`, `strands`, `standards`, `objectives`, `content`, `citations`, and `revision`

#### Scenario: Revision increment on update
- **GIVEN** an existing lesson with `revision = N`
- **WHEN** the user modifies and saves the lesson
- **THEN** the backend SHALL increment `revision` to `N+1`
- **AND** update `updated_at` to the current timestamp
- **AND** preserve `created_at` unchanged

---

### Requirement: Content Structure
The `content` field SHALL encapsulate the instructional structure of the lesson as a nested object.

The `content` object MUST include:

```json
"content": {
  "materials": ["string"],
  "warmup": "string",
  "activities": [
    {
      "id": "string",
      "title": "string",
      "duration_minutes": 0,
      "steps": ["string"],
      "aligned_standards": ["K.CN.1"],
      "citations": ["string"]
    }
  ],
  "assessment": "string",
  "differentiation": "string",
  "exit_ticket": "string",
  "notes": "string",
  "prerequisites": "string",
  "accommodations": "string",
  "homework": "string",
  "reflection": "string",
  "timing": {
    "total_minutes": 45
  }
}
```

#### Scenario: Activity structure and alignment
- **GIVEN** a lesson contains one or more instructional activities
- **WHEN** the lesson is saved as `m2.0`
- **THEN** each activity in `content.activities` SHALL include `id`, `title`, `duration_minutes`, and `steps`
- **AND** `aligned_standards` SHALL list one or more standard codes (e.g., `"K.CN.1"`) or be an empty array when not applicable
- **AND** `citations` SHALL be used to reference any external or RAG-derived sources used in that activity

#### Scenario: Timing consistency
- **GIVEN** `content.timing.total_minutes` is present
- **WHEN** the backend validates a lesson
- **THEN** it SHOULD ensure that the sum of `activities[].duration_minutes` is consistent with `total_minutes` within an acceptable tolerance (implementation detail)

---

### Requirement: Citations Handling
The schema SHALL support both per-activity and global citations.

#### Scenario: Per-activity citations
- **GIVEN** an activity uses RAG or web sources
- **WHEN** the lesson is saved
- **THEN** that activity's `citations` array SHALL include references (IDs, URLs, or formatted strings) to the sources used

#### Scenario: Global citations list
- **GIVEN** a lesson includes any per-activity citations
- **WHEN** the lesson is saved
- **THEN** the top-level `citations` array SHALL include a de-duplicated list of all citations used anywhere in `content`

---

### Requirement: Backward Compatibility and Evolution
The `m2.0` schema SHALL be forward-compatible with future schema versions via explicit versioning.

#### Scenario: Reading m2.0 lessons after future upgrades
- **GIVEN** lessons stored with `version: "m2.0"`
- **WHEN** the application is upgraded to support later schema versions
- **THEN** existing `m2.0` lessons SHALL remain readable without data loss

#### Scenario: Schema version discrimination
- **GIVEN** a lesson document is loaded from storage
- **WHEN** the backend inspects the document
- **THEN** it SHALL use the `version` field to choose the correct validation and mapping logic (e.g., `m2.0` vs `m3.0`)

