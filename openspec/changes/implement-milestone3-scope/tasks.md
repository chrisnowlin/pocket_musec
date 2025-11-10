## 1. Implementation
- [ ] 1.1 Scaffold backend SSE endpoint (FastAPI) for streaming generations
- [ ] 1.2 Frontend: integrate SSE client and live preview panel (read-only during stream)
- [ ] 1.3 Add image ingestion pipeline (OCR + diagram extraction; basic sheet-music text/labels)
- [ ] 1.4 Add DOCX/Google Docs ingestion (text, tables, images, headings/sections)
- [ ] 1.5 Add web URL vision ingestion (render  screenshots  vision extractor) with readability fallback
- [ ] 1.6 Normalize all ingested content to canonical chunk schema with source metadata
- [ ] 1.7 Enable chunk-level citations by default; implement per-lesson citation style toggle
- [ ] 1.8 Implement cloud/local processing toggle (cloud-first default), preserving offline-with-exceptions policy for local-only
- [ ] 1.9 Multi-document semantic search across PDF, image, DOCX, URL using sqlite-vec + text fallback
- [ ] 1.10 Standards upload (PDF/DOCX)  normalize to canonical standards schema; namespace separation from NC

## 2. Validation
- [ ] 2.1 Unit tests: ingestion (image/docx/url) produce expected chunk and metadata
- [ ] 2.2 Unit/integration tests: SSE endpoint streams tokens; FE renders live updates
- [ ] 2.3 Tests: citation rendering in Markdown and PDF (chunk-level default)
- [ ] 2.4 Tests: cloud/local toggle behavior; local-only enforces offline-with-exceptions
- [ ] 2.5 Tests: multi-document search returns relevant results across 3+ types

## 3. Tooling & Docs
- [ ] 3.1 Update docs/decision-log.md status as capabilities land
- [ ] 3.2 Add "Local model setup (Qwen3 8B)" appendix to docs with Ollama commands
- [ ] 3.3 Record privacy guardrails in settings/help panel copy

## 4. OpenSpec
- [ ] 4.1 Run `openspec validate implement-milestone3-scope --strict` and fix issues
- [ ] 4.2 Update spec deltas as feedback arises

