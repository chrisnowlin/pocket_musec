# session-management Specification Deltas

## MODIFIED Requirements

### Requirement: Session Metadata
The system SHALL track comprehensive metadata for each session, storing standards and objectives as arrays.

#### Scenario: Metadata Collection
- **WHEN** a session is active  
- **THEN** the system tracks creation time, last modified, grade level, and strand
- **AND** stores an array of selected standard IDs (not a single "primary" standard)
- **AND** stores an array of selected objective IDs (not a single "primary" objective)
- **AND** stores user preferences and settings

#### Scenario: Metadata Display
- **WHEN** viewing session list
- **THEN** metadata is displayed for quick identification showing all selected standards
- **AND** sessions can be filtered and sorted by metadata

#### Scenario: API Contract
- **WHEN** creating a new session via API
- **THEN** the request SHALL accept `standard_ids: List[str]` instead of `standard_id: str`
- **AND** the request SHALL accept `selected_objectives: List[str]` as an array
- **AND** backward compatibility SHALL be maintained by converting legacy single values to arrays

#### Scenario: Session Response
- **WHEN** retrieving a session via API
- **THEN** the response SHALL return `selected_standards: List[Dict[str, Any]]` with full standard objects
- **AND** the response SHALL return `selected_objectives: List[str]` as an array of objective IDs
- **AND** legacy fields `additional_standards` and `additional_objectives` SHALL be removed (merged into primary arrays)

#### Scenario: Database Storage
- **WHEN** persisting session data
- **THEN** standards SHALL be stored as comma-separated IDs for efficiency
- **AND** objectives SHALL be stored as comma-separated IDs
- **AND** the API layer SHALL convert between storage format (CSV strings) and API format (arrays)
