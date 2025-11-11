# standards-user-upload Specification

## Purpose
TBD - created by archiving change implement-milestone3-scope. Update Purpose after archive.
## Requirements
### Requirement: Upload and Normalize Standards
The system SHALL allow teachers to upload standards documents (PDF/DOCX) and normalize them into the canonical standards schema alongside NC, maintaining identifiers and relationships.

#### Scenario: Upload DOCX standards
- WHEN a teacher uploads a standards DOCX
- THEN the system parses grade/strand/standard/objective
- AND stores records with stable IDs following the `{grade}.{strand}.{n}[.{m}]` format when present (or a derived stable namespace)
- AND the new standards appear in selection and search flows

### Requirement: Namespace Separation
The system MUST namespace user-provided standards to avoid collision with NC standards and allow filtering by source.

#### Scenario: Filter by standards origin
- WHEN searching for standards
- THEN the UI/CLI can filter by `NC` vs `User Uploads:{name}`
- AND generation can target either or both sets explicitly

