# ingestion-web-vision Specification

## Purpose
TBD - created by archiving change implement-milestone3-scope. Update Purpose after archive.
## Requirements
### Requirement: Vision-Based Web Extraction
The system SHALL ingest web URLs by rendering pages to screenshots and using vision AI to extract structured content (headings, paragraphs, lists, tables) into normalized chunks with `source.url` and region metadata.

#### Scenario: Render and extract
- GIVEN a URL to an article with headings and lists
- WHEN ingestion runs
- THEN the page is rendered to one or more screenshots
- AND vision extraction returns chunks with role tags (h1, h2, p, li)
- AND each chunk includes a reference to the screenshot region

### Requirement: Fallback to Readability Text
The system SHALL fall back to readability-based HTML text extraction when vision extraction fails or confidence is low.

#### Scenario: Vision failure fallback
- WHEN vision extraction returns empty or low-confidence results
- THEN the system uses readability extraction
- AND stores the resulting text as chunks with `source.method = readability`

