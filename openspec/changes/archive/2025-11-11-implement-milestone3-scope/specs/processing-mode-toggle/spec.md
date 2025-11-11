# Specification: Processing Mode Toggle

## ADDED Requirements

### Requirement: Cloud-First Default
The system SHALL default to cloud processing (Chutes LLM). Switching to local-only requires explicit user opt-in via Settings.

#### Scenario: Default is cloud
- WHEN the app is first launched after M3
- THEN processing mode is set to Cloud
- AND generation uses Chutes unless the user changes Settings

### Requirement: Local-Only Privacy Guardrails
The system MUST enforce offline-with-exceptions in local-only mode: block external I/O by default; prompt per action (e.g., model download/update, license check); no telemetry while offline.

#### Scenario: Local-only with exception prompt
- GIVEN the user enabled local-only
- WHEN a model download is required
- THEN the app prompts for explicit permission
- AND only proceeds on user approval; otherwise aborts the network action

