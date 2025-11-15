# lesson-generation Delta Specification

## ADDED Requirements

### Requirement: Lesson Modification Metadata Preservation
The system SHALL preserve standards alignment and generation metadata when lessons are edited.

#### Scenario: Edit preserves metadata
- **WHEN** a user edits a generated lesson
- **THEN** the original standard IDs, grade, and strand are preserved
- **AND** modification timestamp is added to metadata
- **AND** original generation parameters remain accessible

#### Scenario: Modified lesson regeneration
- **WHEN** a user requests regeneration of a modified lesson
- **THEN** the system uses the original parameters as a base
- **AND** incorporates the user's edits as additional context
- **AND** produces a new version while preserving edit history

#### Scenario: Export includes generation context
- **WHEN** an edited lesson is exported
- **THEN** the export includes original standards alignment
- **AND** notes that the lesson was modified from AI-generated base
- **AND** includes both generation and modification timestamps
