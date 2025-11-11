## ADDED Requirements
### Requirement: Variant 6 workspace shell as default interface
The system SHALL present the Variant 6 "Dashboard Chat Hybrid" workspace as the root web experience while keeping the legacy dashboard/images/settings flow isolated under `/classic`.

#### Scenario: Variant 6 workspace as default
- **WHEN** a user navigates to `/` in a fresh tab
- **THEN** the Variant 6 workspace shell loads immediately with the sidebar, chat canvas, and inspector panels
- **AND** the user can interact with all lesson planning controls without first visiting the legacy dashboard

#### Scenario: Legacy layout still accessible
- **WHEN** a user intentionally navigates to `/classic`
- **THEN** the previous dashboard/images/settings interface renders with its original nav/navigation
- **AND** the navigation links stay scoped to `/classic` so the legacy view does not redirect back to the workspace

#### Scenario: Easy switch between experiences
- **WHEN** a user is in either interface
- **THEN** a prominent control (link/button) is available to toggle between `/` and `/classic`
- **AND** toggling does not lose the user’s chat or standard selection state in the workspace shell
