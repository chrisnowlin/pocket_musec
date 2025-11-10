# Specification: CLI Workflow

## ADDED Requirements

### Requirement: Interactive Chat Interface
The system SHALL provide a conversational interface for lesson requirements.

#### Scenario: Grade selection flow
Given a teacher runs `pocketflow generate lesson`
When the session starts
Then the agent asks "What grade level are you planning for?"
And displays valid options: K, 1-8, BE, IN, AC, AD
When the teacher enters "K"
Then the selection is confirmed and stored
When the teacher enters an invalid grade
Then it shows available options and prompts again

#### Scenario: Strand selection with descriptions
Given grade level has been selected
When the agent prompts for strand
Then it displays all four strands with descriptions:
- CN (Connect): Explore and relate artistic ideas...
- CR (Create): Generate and conceptualize artistic ideas...
- PR (Present): Develop, refine, and share artistic work...
- RE (Respond): Understand and evaluate artistic work...
And accepts either code (CN) or name (Connect)

#### Scenario: Standard recommendation
Given grade "K" and strand "CN" are selected
When the system queries available standards
Then it displays matching standards (e.g., K.CN.1, K.CN.2)
And shows brief summaries of each standard
And asks "Which standard(s) should this lesson address?"
And accepts comma-separated list or "all"

#### Scenario: Navigation commands
Given any point in the conversation
When the teacher types "back"
Then it returns to the previous step with state preserved
When the teacher types "quit"
Then it confirms exit and cleans up session
When the teacher types "help"
Then it displays available commands and current options

### Requirement: Editor Integration
The system SHALL launch the system editor for lesson refinement.

#### Scenario: Open in default editor
Given a generated lesson plan
When ready for editing
Then the system detects OS default editor (nano on macOS/Linux, notepad on Windows)
And creates a temporary file with the lesson content
And launches the editor with the file
And waits for the editor to close

#### Scenario: Post-edit options
Given the editor has been closed
When returning to CLI
Then the system presents options:
- Save as-is
- Regenerate (creates new version)
- Duplicate for another strand
- Cancel without saving
And processes the selected action

### Requirement: Draft History Management
The system MUST maintain draft history during the session.

#### Scenario: Version tracking
Given a lesson generation session
When the initial lesson is created
Then it's stored as Draft #1 with timestamp
When the teacher requests regeneration
Then new versions are created as Draft #2, #3, etc.
And the original is always preserved

#### Scenario: History limit enforcement
Given 10 drafts exist (original + 9 regenerations)
When an 11th draft is requested
Then the oldest non-original draft is removed
And the new draft is added as #10
And the original remains accessible

#### Scenario: Draft selection
Given multiple drafts exist
When the teacher chooses to save
Then all drafts are listed with timestamps
And the teacher can select which version to save
And selection is made by draft number

### Requirement: File Saving
The system SHALL allow flexible saving of final lessons.

#### Scenario: Save dialog
Given a teacher selects "save as-is"
When prompted for location
Then they can specify filename (with .md default extension)
And choose destination directory (or use current)
And the system confirms successful save with full path

#### Scenario: Standards metadata in filename
Given a saved lesson for K.CN.1
When suggesting a default filename
Then it includes grade and standard (e.g., "K_CN1_lesson.md")
And the teacher can override with custom name

### Requirement: Session Summary
The system SHALL provide a comprehensive session summary.

#### Scenario: Summary table display
Given a session with multiple drafts and saves
When the session ends (quit or after final save)
Then it displays a formatted table with columns:
- Draft # (1, 2, 3...)
- Timestamp (YYYY-MM-DD HH:MM:SS local time)
- Status (Saved/Discarded/Regenerated)
- Standards (K.CN.1, etc.)
- File (path or "(temp only)")

#### Scenario: Session cleanup
Given session termination
When cleanup runs
Then all temporary draft files are deleted
And only saved files remain at user-specified locations
And the session workspace is removed

### Requirement: Error Recovery
The system MUST handle interruptions gracefully.

#### Scenario: Keyboard interrupt handling
Given an active session
When the user presses Ctrl+C
Then the system catches the interrupt
And asks "Save current work before exiting? (y/n)"
And performs cleanup based on response

#### Scenario: Editor crash recovery
Given the editor process terminates unexpectedly
When control returns to CLI
Then the system detects the abnormal exit
And offers to retry editing or proceed with original content
And maintains session state