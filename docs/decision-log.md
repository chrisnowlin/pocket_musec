# Project Decision Log

Tracks the current agreement for key aspects of the project. Update entries when the team makes or revises a decision.

_Last updated: 2025-11-10_

| Area | Current Decision | Notes |
| --- | --- | --- |
| Vision & Goals | Offer a lean, teacher-first app that organizes scattered resources and produces clear, ready-to-use lesson plans for music teachers using RAG and AI agents. | |
| Target Audience | K-12 music teachers (priority: elementary) | |
| Platform & Tech Stack | Hybrid: Python core (PocketFlow) for local LLM runtime + ingestion/processing; TypeScript UI/API gateway. UI: Vite + React SPA. Desktop hosts: Electron (primary), Tauri (secondary). Local LLM: TBD; Cloud: Chutes. | |
| Repository Structure | Standard monorepo with Python backend and TypeScript frontend in single repository | Directory layout: /backend (Python), /frontend (TypeScript/React), /docs |
| Python Package Management | uv for dependency management and package tooling | |
| LLM Framework | PocketFlow (100-line minimalist framework) for agent/RAG implementation | Lightweight graph-based architecture with Node/Flow/Store pattern. Zero dependencies, supports Multi-Agents, Workflow, and RAG. |
| Embedding Model | Chutes embedding models for vector generation | Consistent with cloud LLM provider choice for v1. |
| PDF Parsing | pdfplumber for text extraction and structured data | Good for layout analysis and table extraction. OCRmyPDF as fallback for scanned documents. |
| CLI Framework | Typer for command-line interface | Modern, type-hint based, built on Click. Good for interactive flows. |
| Backend-Frontend Communication | WebSocket for real-time bidirectional communication; HTTP+SSE fallback | WebSocket primary for chat and streaming LLM responses. SSE fallback for compatibility. |
| Python Web Framework | FastAPI for HTTP and WebSocket server | Modern async framework with excellent WebSocket support and automatic API documentation. |
| React State Management | Zustand for client state management | Lightweight and simple state management for lesson state, chat history, and UI state. |
| UI Components & Styling | shadcn/ui + Tailwind CSS | Accessible, customizable copy-paste components built on Radix with utility-first styling. |
| Testing Frameworks | Python: pytest; Frontend: Vitest + React Testing Library | pytest for backend unit/integration tests. Vitest (Vite-native) with RTL for frontend component tests. |
| Data Sources & Formats | Broad ingestion: PDFs, Google Docs/DOCX, web pages/URLs, YouTube links/transcripts, images (e.g., sheet music), standards docs, CSVs. v1 priorities: PDFs, standards documents, images. | |
| Lesson Plan Output | Core fields: title, grade level, duration, objectives, materials, standards alignment, procedure/steps, assessment, differentiation/accommodations, extensions, references/sources. Output: Markdown. If RAG is used, include citations to source chunks. | CLI-generated Markdown should open in the configured editor for basic tweaks before save/export. |
| Privacy & Data Posture | v1: Cloud-first for speed/power with explicit toggle for local-only processing. Student/sensitive data should have a local path. Long-term: full local-first capability. | |
| Authentication & Access | No accounts (internal alpha only) | |

| Cloud LLM Provider | Chutes | |
| Vector Store & Graph | SQLite + sqlite-vec for vector embeddings; graph relations via nodes/edges tables and recursive CTEs (Graph RAG). | Start with sqlite-vec for simplicity. Vector search handles similarity, graph tables handle relationships. |



| Timeline & Milestones | Milestone 1: Foundations & RAG prototype delivering an end-to-end CLI that supports basic lesson tweaks via the configured editor.<br>Milestone 2: Teacher-facing alpha shell with editable lesson fields and export in the Electron app.<br>Milestone 3: Expanded ingestion (PDF + images) with citation support and cloud/local processing toggle. | Each milestone must yield a usable teacher workflow, even if minimal. |
| Milestone 2 Lesson Editor Fields | Full set: title; grade; strands/standards; objectives; materials; warm-up; activities (title, duration, steps/notes, per-activity standards alignment); total timing; differentiation; assessment; exit ticket; citations; teacher notes; prerequisites; accommodations; homework; reflection. | Include per-activity alignment mapping and citations in M2; lesson schema will be versioned. |
| Milestone 2 Export Formats | Markdown (.md) + PDF (.pdf) | Use Electron/Chromium print-to-PDF for reliable export; keep Markdown as canonical editable format; defer DOCX to a later milestone. |
| Milestone 2 Backend Orchestration | Electron launches local Python FastAPI on app start; UI communicates over local HTTP; add SSE/WS later as needed. | Detect free localhost port; restart if backend crashes; graceful shutdown with app quit. |
| Milestone 2 Generation Mode | Whole-response only (no streaming) | Simplest path for alpha; add SSE-based live preview in a later milestone. |
| Milestone 2 Drafts & Auto-save | Hybrid: continuous auto-save + explicit “Save revision” snapshots; keep last 10 snapshots per lesson. | Store snapshots in a per-lesson .revisions folder; show a simple revisions panel in the editor. |
| Open Questions | 1. Define the canonical standards metadata schema (fields, identifiers, relationships) to align ingestion outputs with CLI filtering/export flows.<br>2. Select target local LLM models and document the minimum viable hardware footprint to make the local-only option practical.<br>3. Clarify privacy safeguards and storage limits when users toggle between cloud-first and local processing, including handling of sensitive student inputs.<br>4. Outline the teacher feedback loop and success metrics needed to judge milestone usability. | |
| Milestone 2 Standards Search | Semantic search (sqlite-vec embeddings) | Combine grade/strand filters with natural-language query over embeddings; provide text-search fallback when embeddings unavailable. |

| Milestone 2 OS Targets | macOS only | Package with Electron Builder for macOS; internal alpha distribution (no App Store); ad-hoc signing for dev builds; revisit notarization if sharing beyond trusted testers. |
| Milestone 2 Default Save Location | ~/Documents/PocketMusec Lessons | Make configurable in Settings; create folder on first save if missing; allow change per-save with a default pointing here. |
| Milestone 2 Lesson JSON Schema | Version: m2.0; Meta: id (uuid), created_at, updated_at; title, grade, strands[], standards[] (code,title,summary), objectives[]; Content: materials, warmup, activities[] (id,title,duration_minutes,steps[],aligned_standards[],citations[]), assessment, differentiation, exit_ticket, notes, prerequisites, accommodations, homework, reflection, timing.total_minutes; Citations: citations[]; Revision: revision (int). | Contract between FE and FastAPI; validate via schema; per-activity alignment and citations included. |
### Milestone Notes
| Milestone 2 Settings Scope | Balanced: API key; default save folder; default export format; revision retention count; semantic search fallback toggle; + Theming (light/dark). | Keep UI minimal; store settings via Electron store; apply theme app-wide. |

#### Milestone 1 – Standards ingestion

- **Focus:** Ingest and parse the new North Carolina Standard Course of Study standards for elementary general music as the initial standards corpus.
- Extract structured metadata (grade level, strand, clarifying objectives, etc.) from standards documents so lesson plans can target specific requirements.
- Define the canonical metadata schema for standards (field names, data types, relationships) as part of Milestone 1.
- **Standards Schema**: JSON and SQLite representations with the following structure:
  - **Grade Levels**: K, 1-8, BE (Beginning HS), IN (Intermediate HS), AC (Accomplished HS), AD (Advanced HS)
  - **Strand Codes**: CN (Connect), CR (Create), PR (Present), RE (Respond)
  - **ID Format**: `{grade}.{strand}.{standard_number}` for standards, `{grade}.{strand}.{standard_number}.{objective_number}` for objectives
  - **JSON Example**:
    ```json
    {
      "standard_id": "K.CN.1",
      "grade_level": "K",
      "strand_code": "CN",
      "strand_name": "Connect",
      "strand_description": "Explore and relate artistic ideas and works to past, present, and future societies and cultures.",
      "standard_text": "Relate musical ideas and works with personal, societal, cultural, historical, and daily life contexts, including diverse and marginalized groups.",
      "objectives": [
        {
          "objective_id": "K.CN.1.1",
          "objective_text": "Identify the similarities and differences of music representing diverse global communities."
        },
        {
          "objective_id": "K.CN.1.2",
          "objective_text": "Identify how music is used in school and in daily life."
        }
      ],
      "source_document": "Final Music NCSCOS - Google Docs.pdf",
      "ingestion_date": "2024-11-09T20:57:00Z",
      "version": "2024-05-16"
    }
    ```
  - **SQLite Schema**:
    ```sql
    CREATE TABLE standards (
        standard_id TEXT PRIMARY KEY,
        grade_level TEXT NOT NULL,
        strand_code TEXT NOT NULL,
        strand_name TEXT NOT NULL,
        strand_description TEXT NOT NULL,
        standard_text TEXT NOT NULL,
        source_document TEXT,
        ingestion_date TEXT,
        version TEXT
    );

    CREATE TABLE objectives (
        objective_id TEXT PRIMARY KEY,
        standard_id TEXT NOT NULL,
        objective_text TEXT NOT NULL,
        FOREIGN KEY (standard_id) REFERENCES standards(standard_id)
    );

    CREATE INDEX idx_grade_level ON standards(grade_level);
    CREATE INDEX idx_strand_code ON standards(strand_code);
    CREATE INDEX idx_standard_objectives ON objectives(standard_id);
    ```
- Schema approach: Prefer flat fields with identifiers for strands/clarifying objectives to simplify querying.
- Identifier strategy: Reuse the existing codes/labels from the North Carolina standards corpus for fields and objectives.
- Preprocessing: Convert source standards PDFs into a cached JSON/SQLite representation during ingestion so CLI runs operate on prepared data.
- Ingestion command: Provide a dedicated CLI command (e.g., `pocketflow ingest standards`) for rerunning ingestion when new documents arrive.
- Parsing strategy: Implement source-specific parsers (PDF, DOCX/Google Docs, etc.) instead of normalizing via conversion.
- Parsing priority: Start with PDF standards parsing before expanding to other formats.
- OCR fallback: Integrate OCR (e.g., via OCRmyPDF) for scanned or partially scanned standards PDFs.
- Next parser target: After PDF support, prioritize ingestion of standard Microsoft Office document types (e.g., DOCX) that districts already distribute.
- Office document handling: Add DOCX parsing via a direct file import flow—no external authentication required for v1.
- Cached data storage: Persist normalized JSON/SQLite outputs in a single `data/standards/` directory to keep retrieval straightforward.
- PDF parsing approach: Assume positional heuristics are required to identify strands/objectives rather than relying on consistent fonts/labels.
- Heuristic tuning: Infer positional rules dynamically across the corpus instead of hard-coding page-specific coordinates.

#### Milestone 1 – Lesson generation & CLI workflow

- Primary use case: Enable filtering of lesson suggestions by grade, strand, and clarifying objective alignment.
- Lesson generation goal: Provide broad strand coverage with at least one exemplar lesson per strand before deepening grade-level themes.
- Next focus: Define the CLI end-to-end flow (generate → open configured editor → confirm/save) for Milestone 1 usability.
- Teacher input: Collect lesson requirements through an interactive chat-style prompt sequence with the PocketFlow agent rather than CLI flags. PocketFlow leads the teacher through:
  1. **Grade selection** – Prompt: "What grade level are you planning for?" Validate against `K, 1-8, BE, IN, AC, AD`; show available options on invalid input.
  2. **Strand selection** – Prompt: "Which strand would you like to focus on?" Accept strand code (e.g., `CN`) or name (`Connect`) and display the four strands with descriptions.
  3. **Standard recommendations** – After grade+strand confirmation, display matching standards (e.g., `K.CN.1`, `K.CN.2`) with short summaries and ask: "Which standard(s) should this lesson address? (comma-separated or 'all')".
  4. **Objective refinement** – List objectives for the selected standard(s) and prompt: "Any specific objectives to emphasize? (comma-separated or 'all')". Default to all objectives if skipped.
  5. **Additional context** – Offer an optional free-form prompt: "Any additional context for this lesson?" (theme, materials, student needs). Allow skip on empty input.
  6. **Confirmation** – Summarize selections and ask "Generate lesson plan? (yes/no)" supporting `back` to revisit steps, `quit` to exit.
- Chat guidance: PocketFlow proactively surfaces relevant standards and objectives immediately after grade and strand selection, but waits for explicit teacher confirmation before locking selections.
- Chat transcripts: Keep PocketFlow conversations ephemeral for Milestone 1 (no transcript storage).
- Editor handling: For Milestone 1, launch OS defaults only (nano on macOS/Linux, notepad on Windows). Defer configurable editor discovery and environment variable overrides to a later milestone.
- Post-edit options: After closing the editor, offer save-as-is, regenerate, duplicate for another strand, and cancel without saving.
- Saving: Prompt teachers to pick the filename and destination directory for each lesson export.
- Version history: Maintain a history of regenerated drafts so teachers can review and select their preferred version before saving. Persist drafts in a temporary on-disk workspace preserved for the session.
- History selection: Present saved drafts (including the original plus up to nine subsequent revisions) as a timestamped list for selection without diffing. Always retain the original draft; when an 11th draft is created, prune the oldest non-original entry.
- History scope: Limit stored drafts to the current CLI session for Milestone 1 and delete the temporary workspace on session exit.
- Export recap: After saving, show the file path and aligned standard metadata for teacher confirmation.
- Session wrap-up: Provide a session summary table before exit with columns `Draft #`, `Timestamp` (local, ISO-like), `Status` (Saved/Discarded/Regenerated), `Standards` (IDs), and `File` (saved path or `(temp only)` if still in workspace). Example:
  ```
  Draft   Timestamp             Status      Standards         File
  -----   -------------------   ----------  ----------------  ----------------------------
  #1      2025-11-09 21:12:04   Saved       K.CN.1            ~/Lessons/kindergarten-cn1.md
  #2      2025-11-09 21:18:17   Discarded   K.CN.1            —
  #3      2025-11-09 21:25:52   Regenerated K.CN.1, K.CN.2    (temp only)
  ```
