# Project Decision Log

Tracks the current agreement for key aspects of the project. Update entries when the team makes or revises a decision.

_Last updated: 2025-11-09_

| Area | Current Decision | Notes |
| --- | --- | --- |
| Vision & Goals | Offer a lean, teacher-first app that organizes scattered resources and produces clear, ready-to-use lesson plans for music teachers using RAG and AI agents. | |
| Target Audience | K-12 music teachers (priority: elementary) | |
| Platform & Tech Stack | Hybrid: Python core (PocketFlow) for local LLM runtime + ingestion/processing; TypeScript UI/API gateway. UI: Vite + React SPA. Desktop hosts: Electron (primary), Tauri (secondary). Local LLM: TBD; Cloud: Chutes. | |
| Repository Structure | Standard monorepo with Python backend and TypeScript frontend in single repository | |
| Python Package Management | uv for dependency management and package tooling | |
| LLM Framework | PocketFlow (100-line minimalist framework) for agent/RAG implementation | Lightweight graph-based architecture with Node/Flow/Store pattern. Zero dependencies, supports Multi-Agents, Workflow, and RAG. |
| Data Sources & Formats | Broad ingestion: PDFs, Google Docs/DOCX, web pages/URLs, YouTube links/transcripts, images (e.g., sheet music), standards docs, CSVs. v1 priorities: PDFs, standards documents, images. | |
| Lesson Plan Output | Core fields: title, grade level, duration, objectives, materials, standards alignment, procedure/steps, assessment, differentiation/accommodations, extensions, references/sources. Output: Markdown. If RAG is used, include citations to source chunks. | CLI-generated Markdown should open in the configured editor for basic tweaks before save/export. |
| Privacy & Data Posture | v1: Cloud-first for speed/power with explicit toggle for local-only processing. Student/sensitive data should have a local path. Long-term: full local-first capability. | |
| Authentication & Access | No accounts (internal alpha only) | |

| Cloud LLM Provider | Chutes | |
| Vector Store & Graph | SQLite + sqlite-vss (or sqlite-vec) for embeddings; graph relations via nodes/edges tables and recursive CTEs (Graph RAG). | |



| Monetization | _TBD_ | |
| Timeline & Milestones | Milestone 1: Foundations & RAG prototype delivering an end-to-end CLI that supports basic lesson tweaks via the configured editor.<br>Milestone 2: Teacher-facing alpha shell with editable lesson fields and export in the Electron app.<br>Milestone 3: Expanded ingestion (PDF + images) with citation support and cloud/local processing toggle. | Each milestone must yield a usable teacher workflow, even if minimal. |
| Open Questions | _TBD_ | |

### Milestone Notes

#### Milestone 1 – Standards ingestion

- **Focus:** Ingest and parse the new North Carolina Standard Course of Study standards for elementary general music as the initial standards corpus.
- Extract structured metadata (grade level, strand, clarifying objectives, etc.) from standards documents so lesson plans can target specific requirements.
- Define the canonical metadata schema for standards (field names, data types, relationships) as part of Milestone 1.
- Schema approach: Prefer flat fields with identifiers for strands/clarifying objectives to simplify querying.
- Identifier strategy: Reuse the existing codes/labels from the North Carolina standards corpus for fields and objectives.
- Preprocessing: Convert source standards PDFs into a cached JSON/SQLite representation during ingestion so CLI runs operate on prepared data.
- Ingestion command: Provide a dedicated CLI command (e.g., `pocketflow ingest standards`) for rerunning ingestion when new documents arrive.
- Parsing strategy: Implement source-specific parsers (PDF, DOCX/Google Docs, etc.) instead of normalizing via conversion.
- Parsing priority: Start with PDF standards parsing before expanding to other formats.
- OCR fallback: Integrate OCR (e.g., via OCRmyPDF) for scanned or partially scanned standards PDFs.
- Next parser target: After PDF support, prioritize syncing and parsing directly from Google Docs versions of the standards.
- Google Docs auth: Use an OAuth login flow when running the ingestion command.
- Cached data storage: Persist normalized JSON/SQLite outputs in a single `data/standards/` directory to keep retrieval straightforward.
- PDF parsing approach: Assume positional heuristics are required to identify strands/objectives rather than relying on consistent fonts/labels.
- Heuristic tuning: Infer positional rules dynamically across the corpus instead of hard-coding page-specific coordinates.

#### Milestone 1 – Lesson generation & CLI workflow

- Primary use case: Enable filtering of lesson suggestions by grade, strand, and clarifying objective alignment.
- Lesson generation goal: Provide broad strand coverage with at least one exemplar lesson per strand before deepening grade-level themes.
- Next focus: Define the CLI end-to-end flow (generate → open configured editor → confirm/save) for Milestone 1 usability.
- Teacher input: Collect lesson requirements through an interactive chat-style prompt sequence with the PocketFlow agent rather than CLI flags.
- Chat guidance: When teachers supply grade/context, PocketFlow proactively recommends relevant standards/strands before refinement.
- Chat transcripts: Keep PocketFlow conversations ephemeral for Milestone 1 (no transcript storage).
- Editor fallback: Respect a configured PocketFlow editor or $EDITOR/$VISUAL; otherwise fall back to nano on macOS/Linux and notepad on Windows.
- Post-edit options: After closing the editor, offer save-as-is, regenerate, duplicate for another strand, and cancel without saving.
- Saving: Prompt teachers to pick the filename and destination directory for each lesson export.
- Version history: Maintain a history of regenerated drafts so teachers can review and select their preferred version before saving.
- History selection: Present saved drafts as a timestamped list for selection without diffing.
- History scope: Limit stored drafts to the current CLI session for Milestone 1.
- Export recap: After saving, show the file path and aligned standard metadata for teacher confirmation.
- Session wrap-up: Provide a session summary listing generated drafts, their timestamps, aligned standards, and final status (saved, discarded, etc.) before exit.
