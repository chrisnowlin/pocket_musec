# Capability: Demo Mode Workspace Shell

## ADDED Requirements

### Requirement: Unrestricted Demo Access
The SPA SHALL assume a demo user and render the main workspace without requiring authentication flows.

#### Scenario: Direct access
- **WHEN** a visitor opens the SPA in demo mode
- **THEN** the app SHALL immediately render the workspace shell (Dashboard, Workspace, Images, Settings) with no login screen
- **AND** no route SHALL redirect to `/login` or reference credentials
- **AND** the UI SHALL communicate that the environment is a single-user demo build

#### Scenario: No auth controls
- **WHEN** a user interacts with global navigation
- **THEN** the header/sidebar SHALL omit login/logout buttons or user-account menus
- **AND** there SHALL be no “Users” or “Admin” links implying account management

### Requirement: Navigation Clarity
The layout SHALL present only the pages that function without authentication.

#### Scenario: Navigation items
- **WHEN** the layout is rendered
- **THEN** it SHALL include links for Dashboard, Workspace, Images, and Settings only
- **AND** selecting any link SHALL transition within the SPA without mentioning authentication state

### Requirement: Codebase Hygiene
Auth-specific utilities SHALL be removed or clearly disabled to avoid confusion.

#### Scenario: API client
- **WHEN** reviewing the frontend API client module
- **THEN** there SHALL be no exported methods for login, logout, refresh tokens, or user CRUD
- **AND** only endpoints that operate with the default demo user SHALL remain

#### Scenario: Documentation
- **WHEN** reading the README/onboarding docs
- **THEN** they SHALL state that authentication is disabled in this milestone and that the demo user is used automatically
- **AND** they SHALL not instruct contributors to set auth-related environment variables for the UI workflow
