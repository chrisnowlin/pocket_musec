## ADDED Requirements

### Requirement: Cloud Model Selection
The system SHALL allow users to select specific Chutes API models when using Cloud processing mode.

#### Scenario: Model selection in cloud mode
- **WHEN** a user is in Cloud processing mode
- **THEN** the system SHALL display a dropdown of available Chutes API models
- **AND** the system SHALL include moonshotai/Kimi-K2-Thinking as an option
- **AND** the system SHALL allow switching between models without restarting the application

#### Scenario: Model availability validation
- **WHEN** a user selects a model from the dropdown
- **THEN** the system SHALL validate the model is available via Chutes API
- **AND** if unavailable, the system SHALL display an error message
- **AND** the system SHALL revert to the last working model

#### Scenario: Model preference persistence
- **WHEN** a user selects a model for chat
- **THEN** the system SHALL save the model preference in the session
- **AND** the preference SHALL persist for the duration of the chat session
- **AND** new messages SHALL use the selected model until changed

## MODIFIED Requirements

### Requirement: Cloud and Local Processing Modes
The system SHALL support two processing modes: Cloud (using Chutes API with selectable models) and Local (using Ollama with local models), selectable by users.

#### Scenario: Cloud mode operation
- **WHEN** a teacher selects "Cloud" processing mode
- **THEN** the system SHALL use Chutes API for LLM generation with the selected model
- **AND** the system SHALL allow model selection within Cloud mode
- **AND** the system SHALL use Chutes Vision API for image processing
- **AND** lesson generation SHALL complete in approximately 30 seconds
- **AND** the system SHALL require active internet connection

#### Scenario: Mode availability checking
- **WHEN** displaying processing mode options
- **THEN** the system SHALL check if each mode is available
- **AND** for Cloud mode: verify API credentials are configured and list available models
- **AND** for Local mode: verify Ollama is installed and model is downloaded
- **AND** unavailable modes SHALL be disabled with explanation

### Requirement: Mode Indicator in UI
The system SHALL clearly display the current processing mode and selected model in the user interface during lesson generation.

#### Scenario: Mode indicator display
- **WHEN** viewing the lesson generation interface
- **THEN** the current processing mode SHALL be visible in the header or status bar
- **AND** the selected model name SHALL be displayed when in Cloud mode
- **AND** the indicator SHALL use distinct colors or icons (Cloud = blue, Local = green)
- **AND** the indicator SHALL be clickable to view mode details

#### Scenario: Generation mode confirmation
- **WHEN** starting a lesson generation
- **THEN** the system SHALL show a confirmation: "Generating using [Model] via [Mode] mode"
- **AND** the confirmation SHALL include expected time
- **AND** the confirmation SHALL be dismissible after 3 seconds

#### Scenario: Generated lesson mode badge
- **WHEN** viewing a completed lesson
- **THEN** the lesson SHALL display a badge indicating which mode and model was used
- **AND** the badge SHALL be visible in lesson metadata
- **AND** the badge SHALL persist in exports (e.g., "Generated using [Model] via Cloud" footer)