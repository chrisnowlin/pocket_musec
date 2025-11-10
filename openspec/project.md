# Project Context

## Purpose
- Build a lean, teacher-first assistant that organizes scattered music-education resources and produces clear, ready-to-use lesson plans.
- Empower K-12 (priority: elementary) music teachers with rapid standards-aligned planning using local-first tooling backed by RAG + AI agents.
- Deliver milestone-driven increments where each release enables a usable teacher workflow (starting with CLI lesson generation).

## Tech Stack
- **Python backend / PocketFlow core**: Custom minimalist agent/RAG framework (Node/Flow/Store pattern) powering ingestion, retrieval, and lesson synthesis.
- **Web surface**: TypeScript + Vite + React SPA with Zustand for state management and shadcn/ui + Tailwind CSS for components/styling.
- **Desktop shell**: Electron (primary) with Tauri as a secondary packaging target.
- **CLI**: Typer-based interface for local workflows (generation, ingestion commands).
- **APIs**: FastAPI for HTTP + WebSocket server; SSE fallback for streaming compatibility.
- **Data layer**: SQLite + sqlite-vec for embeddings/graph relations; cached JSON/SQLite artifacts under `data/standards/`.
- **Document ingestion**: pdfplumber (PDF parsing), OCRmyPDF fallback, DOCX ingestion pipeline.
- **LLMs**: Chutes cloud LLM (primary) with future local-only option; Chutes embedding models for vectors.

## Project Conventions

### Code Style
- **Python**: Modern type hints (>=3.11), prefer dataclasses/pydantic-style models, formatted with Black-compatible spacing (88 cols) and linted with Ruff defaults; function/variable names in `snake_case`, classes in `PascalCase`.
- **TypeScript/React**: Strict TypeScript configuration, functional components with hooks, state slices in Zustand typed with interfaces; naming in `camelCase`, React components in `PascalCase`.
- **General**: Keep files focused (<300 lines when reasonable), include docstrings/JSDoc only when behavior is non-obvious, favor descriptive commit messages (imperative mood).

### Architecture Patterns
- **Monorepo layout**: `/backend` (PocketFlow + FastAPI), `/frontend` (Vite/React), `/cli` (Typer), `/docs` (decision logs/specs), shared assets under `/data`.
- **PocketFlow graph**: Workflows modeled as Nodes/Edges with Stores for context—supports multi-agent orchestration and RAG retrieval.
- **Ingestion pipeline**: Source-specific parsers (PDF, DOCX) normalize to canonical standards schema persisted in SQLite/JSON caches.
- **Runtime comms**: WebSocket primary channel for real-time lesson previews; HTTP/SSE fallback for environments lacking WS support.
- **Desktop packaging**: SPA served inside Electron/Tauri with shared API gateway; reuse backend via local runtime services.

### Testing Strategy
- **Backend**: pytest for unit/integration tests (focus on ingestion parsers, PocketFlow nodes, API endpoints); fixture data derived from cached standards samples.
- **Frontend**: Vitest + React Testing Library for component and hook coverage; verify Zustand stores and streaming UI states.
- **CLI**: Typer CLI tests leveraging Typer’s testing utilities + snapshot checks for session summaries.
- **Continuous validation**: Scenario-driven regression tests for lesson generation outputs tied to canonical standards schema.

### Git Workflow
- **Branching**: Feature branches named `feature/<short-desc>` or `fix/<short-desc>` off `main`; keep `main` deployable.
- **Commits**: Small, logical commits using imperative tense (`Add ingestion schema cache`); reference spec/change IDs when relevant.
- **Pull Requests**: Require review + passing tests before merge; squash merge preferred to keep history linear.
- **Change management**: Follow OpenSpec workflow—no implementation until proposal approved; update `openspec/changes` alongside code.

## Domain Context
- North Carolina K-12 General Music standards (May 2024) are the authoritative corpus; identifiers follow `{grade}.{strand}.{standard}.{objective}`.
- Strands: Connect (CN), Create (CR), Present (PR), Respond (RE); grade bands extend into high-school proficiency levels (BE/IN/AC/AD).
- Lesson plans must align with selected standards/objectives and include core fields (title, grade level, duration, objectives, materials, standards alignment, procedure, assessment, differentiation, extensions, references).
- Teachers interact via chat-style CLI prompts that recommend standards based on grade/strand selections; drafts iterate through local editing before export.

## Important Constraints
- **Privacy posture**: Cloud-first with Chutes for v1, but must offer explicit toggle to confine sensitive data to local processing; document safeguards before enabling toggle.
- **Teacher usability**: Each milestone must ship a usable workflow (Milestone 1 = CLI end-to-end with editor integration and draft history).
- **Resource limits**: Local-only mode must operate on typical teacher laptops—hardware profile TBD (open question).
- **Non-commercial**: No monetization for current roadmap; funding assumptions outside scope.
- **Session persistence**: Draft histories stored in temporary session workspace (original + 9 latest regenerations, auto-clean on exit).

## External Dependencies
- **Chutes LLM + embeddings**: Primary inference/embedding provider.
- **sqlite-vec**: Vector similarity search embedded within SQLite.
- **pdfplumber / OCRmyPDF**: PDF parsing and OCR fallback stack.
- **Typer / FastAPI / Vite / React / Zustand / shadcn/ui / Tailwind**: Core frameworks for CLI, backend, and frontend experience.
- **Electron / Tauri**: Desktop distribution targets.
