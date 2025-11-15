## ADDED Requirements

### Requirement: Chat Model Selection Interface
The web interface SHALL provide a model selection component in the chat view for Cloud processing mode.

#### Scenario: Model selector dropdown
- **WHEN** the user is in Cloud processing mode and viewing the chat interface
- **THEN** a model selector dropdown SHALL be visible near the chat input
- **AND** the dropdown SHALL list all available Chutes API models
- **AND** the dropdown SHALL include moonshotai/Kimi-K2-Thinking as an option
- **AND** the current selection SHALL be clearly displayed

#### Scenario: Model switching during chat
- **WHEN** a user selects a different model from the dropdown
- **THEN** the system SHALL update the active model for the session
- **AND** subsequent messages SHALL use the newly selected model
- **AND** the interface SHALL provide visual confirmation of the change
- **AND** model switching SHALL be disabled during message generation

#### Scenario: Model availability indicators
- **WHEN** displaying the model selector
- **THEN** available models SHALL be shown as selectable options
- **AND** unavailable models SHALL be grayed out with tooltip explanation
- **AND** the system SHALL check model availability before enabling selection
- **AND** loading states SHALL be shown during availability checks

### Requirement: Model Selection State Management
The web interface SHALL manage model selection state and synchronize with the backend.

#### Scenario: Model preference persistence
- **WHEN** a user selects a model in the chat interface
- **THEN** the preference SHALL be saved to the current session
- **AND** the preference SHALL be restored when returning to the chat
- **AND** the preference SHALL be reset when starting a new chat session

#### Scenario: Model selection validation
- **WHEN** a user attempts to select a model
- **THEN** the frontend SHALL validate the selection with the backend
- **AND** invalid selections SHALL be rejected with user feedback
- **AND** the interface SHALL revert to the last valid model on error

#### Scenario: Real-time model status updates
- **WHEN** model availability changes during a session
- **THEN** the interface SHALL update the model selector accordingly
- **AND** users SHALL be notified if their selected model becomes unavailable
- **AND** the system SHALL suggest alternative models when appropriate

## MODIFIED Requirements

### Requirement: Chat Input Interface
The chat interface SHALL integrate model selection controls with the message input area.

#### Scenario: Enhanced chat input layout
- **WHEN** viewing the chat interface in Cloud mode
- **THEN** the model selector SHALL be positioned above or beside the chat input
- **AND** the layout SHALL remain responsive on different screen sizes
- **AND** the model selector SHALL not interfere with message composition
- **AND** keyboard navigation SHALL include model selection shortcuts

#### Scenario: Contextual model information
- **WHEN** hovering over model options in the selector
- **THEN** tooltips SHALL display model characteristics (speed, cost, capabilities)
- **AND** the system SHALL highlight recommended models for lesson generation
- **AND** model-specific limitations SHALL be clearly communicated
- **AND** help links SHALL be available for detailed model information