# workspace-shell Specification Deltas

## MODIFIED Requirements

### Requirement: Standard and Objective Selection
The workspace SHALL provide multi-select picker components for selecting standards and objectives, replacing traditional single-select dropdowns.

#### Scenario: Standards selection
- **WHEN** a user views the context panel
- **THEN** they SHALL see a "Standards" multi-select picker component
- **AND** clicking the picker SHALL open a searchable dropdown showing available standards
- **AND** selecting a standard SHALL add it as a chip with code and description
- **AND** each selected standard SHALL have a remove (×) button
- **AND** previously selected standards SHALL be filtered from the dropdown

#### Scenario: Objectives selection
- **WHEN** a user has selected one or more standards
- **THEN** they SHALL see an "Objectives" multi-select picker component
- **AND** the picker SHALL show objectives from all selected standards
- **AND** selecting an objective SHALL add it to the selection as a chip
- **AND** each selected objective SHALL have a remove (×) button
- **AND** previously selected objectives SHALL be filtered from the dropdown

#### Scenario: Empty state
- **WHEN** no standards are selected
- **THEN** the Standards picker SHALL display "Select standards..." as placeholder
- **WHEN** no objectives are selected
- **THEN** the Objectives picker SHALL display "Select objectives..." as placeholder

#### Scenario: Search functionality
- **WHEN** the dropdown is open
- **THEN** a search input SHALL be focused automatically
- **AND** typing SHALL filter standards/objectives by code or description
- **AND** the Cancel button SHALL close the dropdown without changes

## REMOVED Requirements

### Requirement: Primary vs Additional Selection
**Reason**: Unifying selection UX - no longer distinguishing between "primary" and "additional" standards/objectives  
**Migration**: Existing "primary" selections become first item in unified array
