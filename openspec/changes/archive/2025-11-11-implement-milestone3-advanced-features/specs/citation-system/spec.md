# Capability: Citation System

## ADDED Requirements

### Requirement: Source Tracking During Generation

The system SHALL track all source materials used during lesson generation and maintain provenance information for each content section.

#### Scenario: RAG retrieval with source tracking
- **WHEN** the system retrieves content chunks for lesson generation
- **THEN** each chunk SHALL include source metadata (document ID, page, excerpt)
- **AND** the PocketFlow nodes SHALL record which sources influenced each section
- **AND** source tracking SHALL not significantly slow generation (< 10% overhead)

#### Scenario: Multiple source attribution
- **WHEN** a lesson section draws from multiple sources
- **THEN** the system SHALL track all contributing sources
- **AND** the system SHALL maintain the relative contribution of each source
- **AND** citations SHALL list all sources in order of relevance

#### Scenario: Source metadata completeness
- **WHEN** recording a source for citation
- **THEN** the system SHALL capture title, type (standard/document/image), ID, and excerpt
- **AND** for documents: page number, section, publication date
- **AND** for images: filename, upload date, teacher name
- **AND** for standards: standard ID, objective ID, version

### Requirement: Citation Formatting

The system SHALL format citations in IEEE style with inline numeric references and a complete bibliography.

#### Scenario: Inline citation insertion
- **WHEN** generating lesson content
- **THEN** citations SHALL appear as inline numeric references [1], [2], etc.
- **AND** multiple citations SHALL be combined [1, 3, 5] or [1-3]
- **AND** inline citations SHALL not disrupt sentence readability

#### Scenario: Bibliography generation
- **WHEN** a lesson is complete
- **THEN** the system SHALL generate a References section
- **AND** each reference SHALL follow IEEE style formatting
- **AND** references SHALL be numbered matching inline citations
- **AND** references SHALL include all required fields per source type

#### Scenario: Citation formatting for standards
- **WHEN** citing an education standard
- **THEN** format SHALL be: "[#] North Carolina Standard Course of Study, "Grade.Strand.Standard: Title," Version Date, p. Page."
- **EXAMPLE**: "[1] North Carolina Standard Course of Study, "K.CR.1: Create rhythmic and melodic patterns," 2024, p. 12."

#### Scenario: Citation formatting for documents
- **WHEN** citing an uploaded document
- **THEN** format SHALL be: "[#] Author, "Document Title," Publication, Date, pp. Pages."
- **EXAMPLE**: "[2] J. Smith, "Movement-Based Music Education," Music Teachers Journal, vol. 45, no. 3, pp. 123-130, 2023."

#### Scenario: Citation formatting for images
- **WHEN** citing an uploaded image
- **THEN** format SHALL be: "[#] Title, Image Type, uploaded by Teacher Name, Upload Date."
- **EXAMPLE**: "[3] J.S. Bach Minuet in G, Sheet Music, uploaded by Jane Doe, Nov. 2025."

### Requirement: Citation Display in UI

The system SHALL display citations inline with rich tooltips and provide a formatted references section.

#### Scenario: Inline citation hover
- **WHEN** a teacher hovers over an inline citation [1]
- **THEN** a tooltip SHALL display the full reference
- **AND** the tooltip SHALL show a relevant excerpt from the source
- **AND** the tooltip SHALL include a "View Source" link

#### Scenario: References section display
- **WHEN** viewing a generated lesson
- **THEN** a "References" section SHALL appear at the end
- **AND** each reference SHALL be numbered and formatted
- **AND** references SHALL be clickable to view full source

#### Scenario: Citation highlighting
- **WHEN** a teacher clicks a citation in the references section
- **THEN** the system SHALL highlight all uses of that citation in the lesson
- **AND** the system SHALL scroll to the first occurrence
- **AND** the highlighting SHALL persist until dismissed

### Requirement: Source Verification

The system SHALL allow teachers to verify cited sources by viewing original content and context.

#### Scenario: View cited source document
- **WHEN** a teacher clicks "View Source" on a citation
- **THEN** the system SHALL open the original document
- **AND** the system SHALL navigate to the cited page or section
- **AND** the system SHALL highlight the cited excerpt

#### Scenario: View cited standard
- **WHEN** a teacher views a citation to a standard
- **THEN** the system SHALL display the full standard text
- **AND** the system SHALL show related objectives
- **AND** the system SHALL show the strand description for context

#### Scenario: View cited image
- **WHEN** a teacher views a citation to an image
- **THEN** the system SHALL display the image in a modal
- **AND** the system SHALL show OCR extracted text
- **AND** the system SHALL show vision AI description

### Requirement: Citation Deduplication

The system SHALL deduplicate citations when the same source is referenced multiple times.

#### Scenario: Same source multiple references
- **WHEN** a lesson references the same standard in multiple sections
- **THEN** the citation SHALL use the same number [1] for all references
- **AND** the bibliography SHALL list the source only once
- **AND** the system SHALL track all locations where the source is cited

#### Scenario: Similar but distinct sources
- **WHEN** citing related but different objectives from the same standard
- **THEN** each objective SHALL receive a unique citation number
- **AND** the bibliography SHALL list each objective separately
- **EXAMPLE**: [1] K.CR.1.1, [2] K.CR.1.2 (not combined)

#### Scenario: Citation reordering on edit
- **WHEN** a teacher edits a lesson and removes a section
- **THEN** citation numbers SHALL be recalculated
- **AND** unused sources SHALL be removed from bibliography
- **AND** remaining citations SHALL be renumbered sequentially

### Requirement: Citation Export

The system SHALL include citations in all export formats (Markdown, PDF, Word).

#### Scenario: Markdown export with citations
- **WHEN** exporting a lesson to Markdown
- **THEN** inline citations SHALL use markdown link syntax
- **THEN** the References section SHALL be included as formatted text
- **AND** citation links SHALL work when converted to other formats

#### Scenario: PDF export with citations
- **WHEN** exporting a lesson to PDF
- **THEN** inline citations SHALL be superscript numbers
- **AND** the References section SHALL appear on a separate page
- **AND** citations SHALL be formatted with proper spacing and indentation

#### Scenario: Word export with citations
- **WHEN** exporting a lesson to Word (.docx)
- **THEN** citations SHALL use Word's footnote or endnote feature
- **AND** the bibliography SHALL be styled consistently
- **AND** citations SHALL be editable in Word

### Requirement: Citation Quality Validation

The system SHALL validate that all citations are complete, accurate, and resolvable.

#### Scenario: Missing citation detection
- **WHEN** lesson text includes an inline citation [5]
- **AND** the bibliography does not include reference [5]
- **THEN** the system SHALL flag this as an error
- **AND** the system SHALL prevent export until resolved
- **AND** the system SHALL highlight the problematic citation

#### Scenario: Orphaned reference detection
- **WHEN** the bibliography includes a reference not cited inline
- **THEN** the system SHALL warn the teacher
- **AND** the system SHALL offer to remove the unused reference
- **OR** the system SHALL add a citation to the lesson

#### Scenario: Source availability check
- **WHEN** generating citations
- **THEN** the system SHALL verify each source still exists
- **AND** if a source was deleted, the system SHALL flag the citation
- **AND** the system SHALL offer to remove or replace the citation

### Requirement: Citation Privacy and Permissions

The system SHALL respect user privacy and permissions when generating citations for user-uploaded content.

#### Scenario: Teacher-uploaded content citation
- **WHEN** citing an image uploaded by a teacher
- **THEN** the citation SHALL attribute the teacher who uploaded it
- **AND** only if the teacher has granted permission for attribution
- **OR** use "Anonymous Teacher" if attribution declined

#### Scenario: Cross-user content access
- **WHEN** Teacher A generates a lesson
- **AND** the lesson might cite content uploaded by Teacher B
- **THEN** Teacher B's content SHALL only be cited if marked as "shareable"
- **AND** citations SHALL respect Teacher B's attribution preferences

#### Scenario: Public vs private sources
- **WHEN** generating citations
- **THEN** public sources (standards, published docs) SHALL always be cited
- **AND** private sources (personal notes) SHALL only be cited with permission
- **AND** the system SHALL distinguish public vs private in source metadata
