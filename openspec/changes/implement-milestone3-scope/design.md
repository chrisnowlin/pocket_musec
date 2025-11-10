## Context
Milestone 3 expands inputs (images, DOCX, web) and UX (SSE streaming, citations), while maintaining privacy (local-only offline-with-exceptions) and macOS-only packaging.

## Goals / Non-Goals
- Goals: High-signal ingestion for images/DOCX/URLs; chunk-level citations; SSE streaming; user-provided standards; cloud/local toggle; multi-doc search.
- Non-Goals: Full music notation recognition; Windows/Linux packages; collaborative editing; real-time coauthoring.

## Decisions
- Ingestion images: Tesseract/Apple Vision OCR baseline; diagram structure via heuristic block grouping; sheet music limited to lyrics/chord labels.
- Ingestion DOCX: python-docx for text/headings/tables/images; Google Docs via export (DOCX/PDF) path.
- Ingestion web: headless Chromium render to screenshots; vision extractor recovers headings, lists, tables; readability fallback.
- Citations: Default chunk-level; export renders footnotes/inline refs; per-lesson style toggle.
- Streaming: FastAPI SSE endpoint; FE EventSource client; whole-response fallback path.
- Standards: Upload PDF/DOCX; normalize to canonical schema; keep separate namespace from NC.
- Processing mode: Cloud-first default; local-only opt-in; retain M2 offline-with-exceptions prompts; no telemetry while offline.
- Retrieval: sqlite-vec embeddings + text search fallback; cross-type search unifies chunk schema.
- OS: macOS only for M3.

## Risks / Trade-offs
- Vision accuracy vs complexity → Start simple with fallbacks; mark low-confidence.
- Streaming UI complexity → Read-only live preview; defer live-edit-in-stream.
- Local model perf variance → Document baseline (M-series 16GB) + quantization guidance.

## Migration Plan
1) Land ingestion pipelines behind feature flags.  
2) Add SSE endpoint + FE preview.  
3) Enable citations and per-lesson toggle.  
4) Wire cloud/local toggle into generation path.  
5) Validate success metrics (multi-doc search; toggle switch).

## Open Questions
- Which OCR vendor/model to prefer on macOS by default (system frameworks vs Tesseract)?  
- Minimum confidence threshold for including a citation reference?  
- Exact Google Docs export flow (authless file import vs manual upload)?

