# Change Proposal: Implement Milestone 1 Foundation

**Change ID**: `implement-milestone1-foundation`  
**Status**: DRAFT  
**Created**: 2025-11-09  
**Author**: cnowlin  

## Summary

Implement the first milestone of the pocket_musec project to deliver an end-to-end CLI workflow for music teachers. This includes standards ingestion for North Carolina music standards and an interactive lesson generation system powered by PocketFlow agents.

## Problem

Music teachers need a streamlined way to:
1. Access and search North Carolina music education standards programmatically
2. Generate standards-aligned lesson plans through guided interaction
3. Edit and refine generated lessons before saving

Currently, teachers manually browse PDF documents and build lessons from scratch without AI assistance.

## Solution

Build the foundational components:
1. **Standards Ingestion Pipeline**: Parse NC music standards PDFs into structured SQLite database
2. **PocketFlow Agent System**: Minimalist RAG/agent framework for lesson generation
3. **Interactive CLI**: Chat-based interface for teachers to specify requirements and generate lessons
4. **Editor Integration**: Launch system editor for lesson refinement with draft history management

## Capabilities

This change introduces three core capabilities:

### 1. Standards Ingestion (`standards-ingestion`)
Parse and store North Carolina music standards in a queryable format.

### 2. Lesson Generation (`lesson-generation`)  
Generate standards-aligned lesson plans using PocketFlow agents and Chutes LLM.

### 3. CLI Workflow (`cli-workflow`)
Interactive chat interface for teachers to generate, edit, and save lesson plans.

## User Journey

1. Teacher runs `pocketflow ingest standards` to populate the standards database (one-time setup)
2. Teacher runs `pocketflow generate lesson` to start interactive session
3. PocketFlow agent guides through grade/strand/standard selection via chat
4. System generates lesson plan aligned to selected standards
5. Lesson opens in default text editor for refinement
6. Teacher saves final lesson or regenerates with modifications
7. Session summary shows all drafts and saved files

## Technical Approach

- Python backend using PocketFlow (100-line framework) for agent orchestration
- SQLite with defined schema for standards storage
- pdfplumber for PDF parsing with OCRmyPDF fallback
- Typer for CLI with interactive prompts
- Chutes API for LLM generation and embeddings
- Temporary workspace for draft management during session

## Dependencies

- No existing code to modify (greenfield implementation)
- External: Chutes API credentials required
- Standards PDFs already available in `NC Music Standards and Resources/`

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| PDF parsing complexity | High | Start with well-structured standards docs, add OCR fallback |
| LLM API reliability | Medium | Implement retry logic, cache successful generations |
| Cross-platform editor handling | Low | Use OS defaults (nano/notepad), defer config to later milestone |

## Open Questions

1. Should we implement local embeddings in Milestone 1 or defer to later milestone?
2. What's the minimum viable citation format for RAG-retrieved content?
3. Should draft history persist between CLI sessions or remain ephemeral?

## Success Criteria

- [ ] Standards ingestion processes all NC music standards PDFs
- [ ] CLI generates lesson plans aligned to selected standards
- [ ] Teachers can edit lessons in their default text editor
- [ ] Draft history allows reviewing up to 10 versions
- [ ] Session summary displays all generated/saved lessons

## Related Changes

None - this is the initial implementation.