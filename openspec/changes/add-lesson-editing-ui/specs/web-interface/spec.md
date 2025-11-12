# web-interface Delta Specification

## ADDED Requirements

### Requirement: Inline Lesson Editing
The system SHALL provide inline editing capabilities for AI-generated lesson content within the chat interface.

#### Scenario: Enter edit mode
- **WHEN** a user hovers over an AI-generated lesson message
- **THEN** edit, save, and export action buttons appear
- **AND** clicking "Edit" switches the message to edit mode

#### Scenario: Edit lesson content
- **WHEN** a lesson is in edit mode
- **THEN** the content displays in a markdown editor with syntax highlighting
- **AND** users can modify any part of the lesson text
- **AND** a preview toggle allows viewing formatted output

#### Scenario: Save edited lesson
- **WHEN** a user clicks "Save" on an edited lesson
- **THEN** the changes are persisted as a draft via the API
- **AND** the message returns to view mode with updated content
- **AND** a visual indicator shows the lesson was modified

#### Scenario: Cancel editing
- **WHEN** a user clicks "Cancel" while editing
- **THEN** all changes are discarded
- **AND** the lesson returns to its original state
- **AND** no API call is made

#### Scenario: Auto-save during editing
- **WHEN** a user is editing a lesson for more than 30 seconds
- **THEN** changes are automatically saved as a draft
- **AND** a subtle indicator shows the last auto-save time
- **AND** editing continues uninterrupted

### Requirement: Lesson Editor Component
The system SHALL provide a dedicated LessonEditor component for rich text editing with markdown support.

#### Scenario: Editor initialization
- **WHEN** the editor loads with lesson content
- **THEN** it displays the content in a resizable textarea
- **AND** provides markdown formatting toolbar (bold, italic, headers, lists)
- **AND** supports keyboard shortcuts (Ctrl+S to save, Esc to cancel)

#### Scenario: Split view mode
- **WHEN** a user toggles preview mode
- **THEN** the editor shows split view with markdown source and formatted preview
- **AND** both panes scroll synchronously
- **AND** users can adjust the split ratio

#### Scenario: Character count display
- **WHEN** editing a lesson
- **THEN** a character and word count displays at the bottom
- **AND** updates in real-time as the user types

### Requirement: Lesson Export Functionality
The system SHALL provide export capabilities in multiple formats for generated and edited lessons.

#### Scenario: Export as Markdown
- **WHEN** a user selects "Export as Markdown"
- **THEN** the lesson content downloads as a .md file
- **AND** the filename includes the lesson title and timestamp
- **AND** preserves all markdown formatting

#### Scenario: Export as PDF
- **WHEN** a user selects "Export as PDF"
- **THEN** the formatted lesson generates as a PDF in the browser
- **AND** includes proper headers, sections, and formatting
- **AND** downloads with appropriate filename

#### Scenario: Export as Word Document
- **WHEN** a user selects "Export as DOCX"
- **THEN** a Microsoft Word-compatible .docx file is generated
- **AND** preserves formatting (headers, bold, italic, lists)
- **AND** can be opened in Word or compatible editors

#### Scenario: Export with metadata
- **WHEN** any export format is generated
- **THEN** it includes lesson metadata (grade, strand, standards, date)
- **AND** standards alignment is clearly noted
- **AND** generated-by information is included

### Requirement: Enhanced Draft Management UI
The system SHALL extend the DraftsModal with editing and export capabilities.

#### Scenario: Edit draft from modal
- **WHEN** a user clicks "Edit" on a draft in the DraftsModal
- **THEN** the modal closes and the draft loads into chat in edit mode
- **AND** the lesson editor displays with the draft content
- **AND** editing changes update the original draft

#### Scenario: Export draft from modal
- **WHEN** a user clicks "Export" on a draft in the DraftsModal
- **THEN** an export format selector appears
- **AND** selecting a format downloads the draft immediately
- **AND** the modal remains open for further actions

#### Scenario: Preview draft
- **WHEN** a user hovers over a draft in the DraftsModal
- **THEN** a preview pane shows the first 200 characters
- **AND** displays metadata (grade, strand, last modified)
- **AND** clicking the draft shows full content

#### Scenario: Search and filter drafts
- **WHEN** a user types in the draft search box
- **THEN** drafts filter by title and content match
- **AND** can filter by grade level or strand using dropdowns
- **AND** results update in real-time

## MODIFIED Requirements

### Requirement: Lesson Display and Editing
The system SHALL provide a rich lesson viewer with formatting and inline editing capabilities.

#### Scenario: Formatted Display
- **WHEN** a lesson is generated
- **THEN** it displays with proper formatting (headings, lists, sections)
- **AND** standards alignment is clearly highlighted

#### Scenario: Inline Editing
- **WHEN** a user clicks "Edit" on a lesson message
- **THEN** the LessonEditor component replaces the read-only view
- **AND** changes can be saved or discarded
- **AND** modified lessons show a visual indicator

#### Scenario: Regeneration Options
- **WHEN** viewing a generated lesson
- **THEN** users can regenerate specific sections
- **OR** regenerate the entire lesson with modified parameters
- **AND** previous versions are preserved in draft history

### Requirement: Export Functionality
The system SHALL provide export options for generated lessons in multiple formats.

#### Scenario: PDF Export
- **WHEN** a user selects "Export as PDF"
- **THEN** a formatted PDF is generated in the browser using print API
- **AND** downloads with proper filename (title-grade-date.pdf)
- **AND** includes metadata and standards alignment

#### Scenario: Word Export
- **WHEN** a user selects "Export as Word"
- **THEN** a .docx file is generated using docx.js library
- **AND** preserves all formatting (headers, lists, emphasis)
- **AND** can be opened in Microsoft Word or compatible editors

#### Scenario: Markdown Export
- **WHEN** a user selects "Export as Markdown"
- **THEN** a .md file is generated with the lesson content
- **AND** preserves all markdown syntax and structure
- **AND** includes frontmatter with metadata (grade, strand, standards, date)
