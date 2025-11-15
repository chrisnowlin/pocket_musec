# session-management Delta Specification

## ADDED Requirements

### Requirement: Lesson Edit Mode Tracking
The system SHALL track edit mode state for lessons being modified.

#### Scenario: Enter edit mode
- **WHEN** a user begins editing a lesson
- **THEN** the session stores the edit state with lesson ID and timestamp
- **AND** prevents concurrent edits on the same lesson across tabs
- **AND** shows read-only indicator in other tabs

#### Scenario: Exit edit mode
- **WHEN** a user saves or cancels an edit
- **THEN** the edit mode state is cleared
- **AND** other tabs can now edit the lesson
- **AND** changes are synchronized if saved

#### Scenario: Edit mode persistence
- **WHEN** a user refreshes the browser while editing
- **THEN** the edit mode state recovers from IndexedDB
- **AND** unsaved changes are restored
- **AND** the user can continue editing or discard

### Requirement: Lesson Version Tracking
The system SHALL track modifications made to generated lessons.

#### Scenario: Track modification metadata
- **WHEN** a lesson is edited and saved
- **THEN** the system records modification timestamp
- **AND** stores original content separately
- **AND** marks the lesson as "modified" in the UI

#### Scenario: Version comparison
- **WHEN** viewing a modified lesson
- **THEN** users can see it was edited with timestamp
- **AND** can optionally view the original generated version
- **AND** understand what changes were made

#### Scenario: Modification history limit
- **WHEN** a lesson is edited multiple times
- **THEN** the system keeps the original and most recent version
- **AND** intermediate versions are not retained
- **AND** storage remains efficient

### Requirement: Export State Management
The system SHALL manage export operations and preferences.

#### Scenario: Export preferences persistence
- **WHEN** a user exports a lesson in a specific format
- **THEN** that format preference is stored in session
- **AND** becomes the default for subsequent exports
- **AND** can be changed at any time

#### Scenario: Export history tracking
- **WHEN** a lesson is exported
- **THEN** the export event is logged with timestamp and format
- **AND** users can see which lessons were exported
- **AND** can quickly re-export in the same format

## MODIFIED Requirements

### Requirement: Draft History Management
The system SHALL maintain a history of generated and edited lesson drafts within each session.

#### Scenario: Draft Storage
- **WHEN** a lesson is generated or edited
- **THEN** the draft is saved to the session history
- **AND** includes timestamp, version metadata, and modification status
- **AND** distinguishes between generated and manually edited drafts

#### Scenario: Draft Limit
- **WHEN** the draft history exceeds 20 items
- **THEN** the oldest drafts are pruned
- **AND** the most recent 20 are retained
- **AND** both generated and edited drafts count toward the limit

#### Scenario: Draft Browsing
- **WHEN** a user views draft history
- **THEN** all drafts are displayed with timestamps and modification badges
- **AND** the user can select any draft to view, edit, or export
- **AND** modified drafts show a visual indicator

### Requirement: Auto-Save Functionality
The system SHALL automatically save work in progress during lesson editing.

#### Scenario: Periodic Auto-Save
- **WHEN** a user is editing a lesson
- **THEN** changes are auto-saved every 30 seconds
- **AND** a save indicator shows the last save time
- **AND** does not interrupt the editing experience

#### Scenario: Navigation Auto-Save
- **WHEN** a user navigates away from the editor
- **THEN** unsaved changes are automatically saved as a draft
- **AND** the user can return to their work intact
- **AND** receives confirmation of auto-save

#### Scenario: Auto-save conflict resolution
- **WHEN** auto-save occurs while user is still typing
- **THEN** the save waits for a 2-second pause in typing
- **AND** does not disrupt cursor position or selection
- **AND** completes silently in the background
