# Specification: Ingestion – Images

## ADDED Requirements

### Requirement: Generic Image OCR
The system SHALL ingest image files (PNG/JPG) and extract readable text into normalized chunks with source metadata (file path, page/index, bounding boxes when available).

#### Scenario: OCR basic image
- WHEN a teacher ingests "diagram.png"
- THEN the system extracts visible text
- AND stores it as chunks with `source.type = image` and `source.path = diagram.png`
- AND records bounding boxes if provided by the OCR runtime

### Requirement: Diagram/Infographic Structure
The system SHALL detect headings, lists, and table-like regions from diagrams/infographics and annotate chunks with lightweight structure (e.g., `h2`, `ul`, `table.row=...`).

#### Scenario: Structured diagram
- GIVEN an infographic with heading and bullet points
- WHEN ingestion runs
- THEN chunks include role tags (heading, list-item)
- AND order is preserved by reading direction

### Requirement: Sheet Music Essentials (M3 scope)
The system SHALL extract text-like elements from sheet music (lyrics, chord symbols, tempo markings) and ignore full notation decoding in M3.

#### Scenario: Sheet music labels
- WHEN ingesting "chorus.jpg" containing chord labels and lyrics
- THEN chunks include detected text (e.g., "G", "D", lyric words)
- AND `source.tags` include `sheet-music`
- AND no attempt is made to reconstruct staff notation in M3

