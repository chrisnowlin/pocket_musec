# Specification: Retrieval – Multi-Document Cross-Type Search

## ADDED Requirements

### Requirement: Cross-Type Search
The system SHALL support semantic + text search across at least three document types (PDF, image, DOCX, URL) within a single session and return unified results with source metadata.

#### Scenario: Mixed-type query
- GIVEN a session with PDF, image, and DOCX ingested
- WHEN searching for "rhythm warm-up"
- THEN results include relevant chunks across all types
- AND each result shows its type and source location (page, region, heading)

### Requirement: Fallback When Embeddings Missing
The system SHALL fall back to keyword/text search when embeddings are unavailable for a given type, preserving useful results.

#### Scenario: No embeddings for images
- GIVEN image embeddings are not yet generated
- WHEN searching
- THEN text-only OCR chunks are searched by keywords
- AND image results still appear when matching

