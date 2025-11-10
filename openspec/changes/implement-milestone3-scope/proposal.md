# Change Proposal: Implement Milestone 3 Scope

**Change ID**: `implement-milestone3-scope`  
**Status**: DRAFT  
**Created**: 2025-11-10  
**Author**: cnowlin

## Summary
Deliver Milestone 3 by expanding ingestion (images, DOCX/Google Docs, web URLs), enabling chunk‑level citations with per‑lesson toggle, introducing cloud/local processing toggle (cloud‑first by default), supporting user‑provided standards, adding SSE streaming with live preview, and enabling multi‑document cross‑type search. Target OS remains macOS for M3.

## Problem
Teachers need to bring diverse source materials (images, docs, web pages) into lesson generation with traceable citations and responsive UX. M2 shipped the editor/export alpha; M3 must broaden inputs, provide live streaming, and support local/cloud modes while maintaining privacy guardrails.

## Solution
Introduce the following capabilities:
1) Ingestion – Images: generic OCR, diagrams/infographics structure, and essentials for sheet music text/labels.
2) Ingestion – DOCX/Google Docs: full‑fidelity text, tables, images, and hierarchy extraction.
3) Ingestion – Web URLs (vision): render to screenshots and extract structured content via vision AI.
4) Citation support: default chunk‑level; per‑lesson toggle for citation style (none, document‑level, chunk‑level).
5) Streaming: SSE token streaming with editor live preview; whole‑response fallback.
6) Standards: user‑provided standards (PDF/DOCX) normalized into canonical schema alongside NC.
7) Processing mode: cloud‑first by default; local‑only requires explicit opt‑in and preserves M2 offline‑with‑exceptions policy.
8) Retrieval: multi‑document, cross‑type search across PDF, image, DOCX, and URL sources.

## Capabilities (spec IDs)
- ingestion-images
- ingestion-docx
- ingestion-web-vision
- citation-support
- streaming-sse
- standards-user-upload
- processing-mode-toggle
- retrieval-multidoc-search

## User Journey
1. Teacher ingests sources (image, DOCX, URL) via the app.  
2. Sources are indexed (embeddings + metadata).  
3. Teacher selects standards (NC or uploaded).  
4. Starts generation; live preview streams via SSE.  
5. Result includes citations (chunk‑level by default).  
6. Export to Markdown/PDF; search across all sources within the session.

## Technical Approach
- Python FastAPI backend adds SSE endpoint for streaming.  
- Image OCR + diagram extraction with lightweight vision/OCR libs; sheet music: text/labels only in M3.  
- DOCX via python‑docx (and Google Docs export pathway) with table/image parsing; normalized chunks.  
- Web vision ingestion via headless render → screenshots → vision extractor; fallback to readability text if needed.  
- Embeddings + sqlite‑vec for semantic search; graph relations for source→citation mapping.  
- Cloud/local toggle: Chutes (cloud) default; Qwen3 8B as local option from M2; offline‑with‑exceptions preserved.  
- macOS only packaging for M3; Windows/Linux deferred to M4.

## Dependencies
- Existing M1/M2 components (PocketFlow, FastAPI base, editor/export).  
- Chutes LLM/embeddings (cloud) and optional local model (Qwen3 8B).  
- Headless browser for web rendering; OCR/vision runtime.

## Risks & Mitigations
- Vision extraction accuracy → Start with best‑effort + fallbacks; mark low‑confidence citations.  
- Streaming UX complexity → Begin with read‑only live preview; editing while streaming deferred.  
- Local model performance variance → Document baseline; provide clear CPU fallback guidance.  
- Privacy → Enforce offline‑with‑exceptions in local‑only mode.

## Success Criteria (from decision log)
- Ingest and successfully search across 3+ document types (PDF, image, DOCX, URL) in one session.  
- Toggle between cloud and local processing without errors; lesson quality difference acceptable.

## Related Changes
- `implement-milestone1-foundation`  
- `implement-milestone2-web-interface`
