# Specification: Citation Support

## ADDED Requirements

### Requirement: Chunk-Level Citations (Default)
The system SHALL attach chunk-level citations by default to generated lesson content, linking sentences/paragraphs to source chunks (PDF page, image region, URL segment, DOCX cell) and render them in Markdown and PDF exports.

#### Scenario: Default chunk citations
- GIVEN a generated paragraph sourced from image + docx chunks
- WHEN exporting to Markdown and PDF
- THEN each sentence/paragraph includes references (footnotes or inline)
- AND references resolve to source chunk metadata (type, location)

### Requirement: Per-Lesson Citation Style Toggle
The system SHALL allow choosing citation style per lesson: none, document-level, or chunk-level (default).

#### Scenario: Change citation style
- WHEN a teacher sets citation style = document-level
- THEN export lists source documents at the end
- AND per-sentence chunk references are omitted

