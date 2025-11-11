# ingestion-docx Specification

## Purpose
TBD - created by archiving change implement-milestone3-scope. Update Purpose after archive.
## Requirements
### Requirement: Full-Fidelity DOCX Extraction
The system SHALL extract text, headings/sections, lists, images, and tables from DOCX files and normalize into chunk records while preserving hierarchy (e.g., `h1>h2>p`) and table structure (rows, columns, cell order).

#### Scenario: DOCX with headings and tables
- GIVEN a DOCX file with H1/H2 sections and a 3x2 table
- WHEN ingestion runs
- THEN chunks include section tags for headings and paragraphs
- AND table chunks include row/column coordinates and cell text
- AND images are referenced via `source.assets` with positions

### Requirement: Google Docs Import
The system SHALL support Google Docs by accepting exported DOCX or PDF uploads without requiring OAuth (manual export flow), processed through the same pipeline as DOCX/PDF.

#### Scenario: Google Doc export
- WHEN a teacher uploads a Google Doc via exported DOCX
- THEN it is processed with the DOCX extraction pipeline
- AND hierarchy and tables are preserved in chunks

