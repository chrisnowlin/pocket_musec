# Capability: Processing Mode Toggle

## ADDED Requirements

### Requirement: Cloud and Local Processing Modes

The system SHALL support two processing modes: Cloud (using Chutes API) and Local (using Ollama with local models), selectable by users.

#### Scenario: Cloud mode operation
- **WHEN** a teacher selects "Cloud" processing mode
- **THEN** the system SHALL use Chutes API for LLM generation
- **AND** the system SHALL use Chutes Vision API for image processing
- **AND** lesson generation SHALL complete in approximately 30 seconds
- **AND** the system SHALL require active internet connection

#### Scenario: Local mode operation
- **WHEN** a teacher selects "Local" processing mode
- **THEN** the system SHALL use Ollama with Qwen3 8B Instruct model
- **AND** the system SHALL use local CLIP models for image embeddings
- **AND** the system SHALL not send any lesson data to external services
- **AND** lesson generation SHALL complete in approximately 90 seconds

#### Scenario: Mode availability checking
- **WHEN** displaying processing mode options
- **THEN** the system SHALL check if each mode is available
- **AND** for Cloud mode: verify API credentials are configured
- **AND** for Local mode: verify Ollama is installed and model is downloaded
- **AND** unavailable modes SHALL be disabled with explanation

### Requirement: Local Model Integration

The system SHALL integrate with Ollama runtime and support Qwen3 8B Instruct model with Q4_K_M quantization.

#### Scenario: Ollama availability detection
- **WHEN** the application starts
- **THEN** the system SHALL check if Ollama is running (default port 11434)
- **AND** the system SHALL query available models
- **AND** the system SHALL verify Qwen3 8B model is installed

#### Scenario: Model download prompt
- **WHEN** a teacher enables Local mode
- **AND** Qwen3 8B model is not installed
- **THEN** the system SHALL prompt to download the model
- **AND** the system SHALL display model size (approximately 4.8GB)
- **AND** the system SHALL show download progress
- **AND** the download SHALL require explicit user consent

#### Scenario: Model health monitoring
- **WHEN** using Local mode
- **THEN** the system SHALL periodically check model health
- **AND** the system SHALL monitor inference latency
- **AND** if the model becomes unresponsive, the system SHALL notify the teacher
- **AND** the system SHALL offer to switch to Cloud mode

### Requirement: Network Isolation in Local Mode

The system SHALL block external network requests when operating in Local mode, except for explicitly whitelisted domains.

#### Scenario: External API blocking
- **WHEN** operating in Local mode
- **AND** the system attempts to call Chutes API or other external LLM services
- **THEN** the request SHALL be blocked before network transmission
- **AND** an error SHALL be logged with details
- **AND** the user SHALL not be notified unless generation fails

#### Scenario: Whitelisted domains
- **WHEN** in Local mode
- **THEN** requests to Ollama domains (ollama.ai) SHALL be allowed
- **AND** requests for model downloads SHALL be allowed
- **AND** all other external requests SHALL be blocked
- **AND** the whitelist SHALL be configurable by administrators

#### Scenario: Network audit logging
- **WHEN** in Local mode
- **THEN** the system SHALL log all blocked network requests
- **AND** the audit log SHALL include timestamp, URL, and reason
- **AND** administrators SHALL be able to review audit logs
- **AND** the log SHALL not contain sensitive data

### Requirement: Mode Switching

The system SHALL allow teachers to switch between Cloud and Local modes with proper validation and state management.

#### Scenario: Mode switch with validation
- **WHEN** a teacher switches from Cloud to Local mode
- **THEN** the system SHALL verify Ollama and model availability
- **AND** if not available, the system SHALL display setup instructions
- **AND** if available, the system SHALL save the preference
- **AND** the new mode SHALL apply to future lesson generations

#### Scenario: Mode switch during generation
- **WHEN** a lesson generation is in progress
- **AND** the teacher attempts to change processing mode
- **THEN** the system SHALL prevent the mode change
- **AND** the system SHALL display a message: "Cannot change mode during generation"
- **AND** the mode change SHALL be available after generation completes

#### Scenario: Mode persistence
- **WHEN** a teacher sets their processing mode
- **THEN** the preference SHALL be saved per-user
- **AND** the preference SHALL persist across sessions
- **AND** the mode SHALL remain set until explicitly changed

### Requirement: Performance Comparison

The system SHALL display performance and quality comparisons between Cloud and Local modes to help teachers make informed decisions.

#### Scenario: Performance metrics display
- **WHEN** viewing processing mode settings
- **THEN** the system SHALL show estimated generation time for each mode
- **AND** the system SHALL show actual performance based on recent generations
- **AND** metrics SHALL be updated after each generation

#### Scenario: Quality comparison
- **WHEN** viewing processing mode settings
- **THEN** the system SHALL display quality ratings for each mode
- **AND** the system SHALL base ratings on teacher feedback and automated metrics
- **AND** the system SHALL explain trade-offs (speed vs privacy vs quality)

#### Scenario: Hardware requirements display
- **WHEN** a teacher views Local mode option
- **THEN** the system SHALL display minimum hardware requirements
- **AND** the system SHALL detect current system specs
- **AND** the system SHALL warn if system does not meet requirements

### Requirement: Privacy Warnings and Compliance

The system SHALL display clear privacy implications for each processing mode and ensure compliance with data protection policies.

#### Scenario: Cloud mode privacy warning
- **WHEN** a teacher selects Cloud mode
- **THEN** the system SHALL display a warning: "Lesson content will be sent to Chutes API"
- **AND** the warning SHALL appear on first use and be dismissible
- **AND** the warning SHALL include a link to Chutes privacy policy

#### Scenario: Local mode privacy assurance
- **WHEN** a teacher selects Local mode
- **THEN** the system SHALL display: "Lesson content stays on your device"
- **AND** the system SHALL explain no data is sent to external services
- **AND** the system SHALL show network blocking is active

#### Scenario: Sensitive data handling
- **WHEN** a teacher includes student names or sensitive data in lesson context
- **THEN** the system SHALL warn if using Cloud mode
- **AND** the system SHALL recommend switching to Local mode
- **AND** the warning SHALL not block generation but require acknowledgment

### Requirement: Fallback and Error Handling

The system SHALL gracefully handle mode failures and provide fallback options when a mode becomes unavailable.

#### Scenario: Cloud mode API failure
- **WHEN** using Cloud mode
- **AND** Chutes API returns an error or times out
- **THEN** the system SHALL display the error to the teacher
- **AND** the system SHALL offer to retry
- **OR** the system SHALL offer to switch to Local mode if available

#### Scenario: Local mode model unavailable
- **WHEN** using Local mode
- **AND** Ollama service stops or model becomes unavailable
- **THEN** the system SHALL detect the failure
- **AND** the system SHALL offer to switch to Cloud mode
- **AND** the system SHALL provide troubleshooting steps for Ollama

#### Scenario: No mode available
- **WHEN** both Cloud and Local modes are unavailable
- **THEN** the system SHALL display a clear error message
- **AND** the system SHALL provide setup instructions for both modes
- **AND** the system SHALL disable lesson generation until a mode is configured

### Requirement: Mode Indicator in UI

The system SHALL clearly display the current processing mode in the user interface during lesson generation.

#### Scenario: Mode indicator display
- **WHEN** viewing the lesson generation interface
- **THEN** the current processing mode SHALL be visible in the header or status bar
- **AND** the indicator SHALL use distinct colors or icons (Cloud = blue, Local = green)
- **AND** the indicator SHALL be clickable to view mode details

#### Scenario: Generation mode confirmation
- **WHEN** starting a lesson generation
- **THEN** the system SHALL show a confirmation: "Generating using [Mode] mode"
- **AND** the confirmation SHALL include expected time
- **AND** the confirmation SHALL be dismissible after 3 seconds

#### Scenario: Generated lesson mode badge
- **WHEN** viewing a completed lesson
- **THEN** the lesson SHALL display a badge indicating which mode was used
- **AND** the badge SHALL be visible in lesson metadata
- **AND** the badge SHALL persist in exports (e.g., "Generated locally" footer)

### Requirement: Administrator Mode Controls

The system SHALL allow administrators to configure default processing modes and restrict mode availability per deployment.

#### Scenario: Default mode configuration
- **WHEN** an administrator configures deployment settings
- **THEN** the admin SHALL be able to set the default mode for new users
- **AND** the admin SHALL be able to enforce a specific mode (disable alternatives)
- **AND** these settings SHALL apply organization-wide

#### Scenario: Mode restrictions
- **WHEN** an administrator wants to enforce privacy compliance
- **THEN** the admin SHALL be able to disable Cloud mode entirely
- **AND** the admin SHALL be able to require Local mode for all users
- **AND** users SHALL not be able to override admin restrictions

#### Scenario: Usage reporting
- **WHEN** an administrator views usage statistics
- **THEN** the report SHALL show mode usage breakdown (% Cloud vs % Local)
- **AND** the report SHALL show generation counts per mode
- **AND** the report SHALL show average performance per mode
