# Change Proposal: Implement Milestone 3 Advanced Features

**Change ID**: `implement-milestone3-advanced-features`
**Status**: DRAFT
**Created**: 2025-11-10
**Author**: cnowlin

## Summary

Extend PocketMusec with advanced ingestion capabilities, citation tracking, processing mode flexibility, and multi-user support. This milestone adds image ingestion (sheet music, diagrams), comprehensive citation support for RAG-sourced content, cloud/local processing toggle for privacy control, and user authentication for multi-teacher deployments.

## Problem

After Milestone 2's web interface, teachers need:
1. **Image ingestion**: Ability to extract content from sheet music images, music notation, and instructional diagrams
2. **Citation transparency**: Clear attribution of which source materials informed each lesson section
3. **Privacy control**: Explicit toggle between cloud LLM (fast) and local processing (private) for sensitive data
4. **Multi-user support**: Authentication and session isolation for shared deployments in schools

Currently, the system:
- Only processes text-based PDFs, missing rich visual content like sheet music
- Lacks citation tracking, making it hard to verify lesson sources
- Requires cloud connectivity without privacy-preserving local option
- Has no user authentication, limiting deployment to single-teacher scenarios

## Solution

Implement four interconnected capabilities:

1. **Image Ingestion Pipeline**: OCR and vision-based extraction for sheet music, notation, and diagrams
2. **Citation System**: Track and display source attributions throughout lesson generation
3. **Processing Mode Toggle**: User-selectable cloud vs. local LLM processing with clear privacy implications
4. **User Authentication**: Multi-user accounts with session isolation and role-based access

## Capabilities

This change introduces four core capabilities:

### 1. Image Ingestion (`image-ingestion`)
Process image-based content including sheet music, musical notation, and instructional diagrams.

### 2. Citation System (`citation-system`)
Track and display source attributions for all RAG-retrieved content in lessons.

### 3. Processing Mode Toggle (`processing-mode-toggle`)
Allow users to choose between cloud (Chutes) and local (Ollama/llama.cpp) LLM processing.

### 4. User Authentication (`user-authentication`)
Multi-user accounts with session isolation, role management, and access control.

## User Journey

### Image Ingestion Flow
1. Teacher uploads sheet music image or PDF with musical notation
2. System extracts text, musical elements, and metadata using vision models
3. Content indexed for semantic search and lesson generation
4. Teacher can verify extracted elements and correct if needed

### Citation Flow
1. During lesson generation, system tracks all source materials used
2. Generated lesson includes inline citations (e.g., "[1] NC Standards K.CN.1")
3. References section lists all sources with page numbers and excerpts
4. Teacher can click citations to view original source context

### Processing Mode Flow
1. Teacher accesses Settings and sees "Processing Mode" options
2. Default: "Cloud (Fast, requires internet)" using Chutes API
3. Alternative: "Local (Private, no data leaves device)" using local models
4. System shows clear warnings about data privacy and performance trade-offs
5. Local mode blocks external network calls except for model downloads
6. Mode persists per user account

### Authentication Flow
1. Admin creates user accounts with email and role (Teacher/Admin)
2. Teachers log in with email/password at app launch
3. Each teacher sees only their own lessons and sessions
4. Admin can view usage statistics and manage user accounts
5. Sessions persist per user with automatic logout after inactivity

## Technical Approach

### Image Ingestion
- **OCR**: Tesseract for text extraction from images
- **Vision Models**: Chutes vision API or local CLIP models for content understanding
- **Musical Notation**: Audiveris or OMR (Optical Music Recognition) libraries
- **Storage**: Image embeddings in sqlite-vec alongside text embeddings
- **Preprocessing**: Image enhancement, deskewing, noise reduction

### Citation System
- **Tracking**: Extend PocketFlow nodes to record source provenance
- **Format**: IEEE-style inline citations with numbered references
- **Storage**: Citation metadata in SQLite with foreign keys to source chunks
- **Display**: Rich tooltips showing source excerpts on hover
- **Export**: Include full bibliography in PDF/Word exports

### Processing Mode Toggle
- **Cloud Mode**: Chutes API (existing implementation)
- **Local Mode**:
  - Primary: Ollama with Qwen3 8B Instruct (GGUF Q4_K_M)
  - Fallback: llama.cpp direct integration
  - Min requirements: 16GB RAM, Apple Silicon or modern GPU
- **Network Control**: Firewall-style blocking of external requests in local mode
- **Model Management**: Download/update models only with explicit user consent
- **Performance Monitoring**: Display speed comparison and quality metrics

### User Authentication
- **Backend**: FastAPI with JWT tokens (access + refresh)
- **Storage**: User table in SQLite with bcrypt password hashing
- **Sessions**: Per-user session isolation with foreign keys
- **Authorization**: Role-based access control (Teacher, Admin)
- **Security**:
  - HTTPS required in production
  - Rate limiting on auth endpoints
  - Password complexity requirements
  - Session timeout after 2 hours of inactivity
  - Optional 2FA with TOTP (future enhancement)

## Dependencies

- **Existing**: Milestone 2 web interface, PocketFlow backend, standards database
- **New External**:
  - Tesseract OCR engine
  - Ollama or llama.cpp for local models
  - Qwen3 8B Instruct model (GGUF format)
  - Vision model APIs or local CLIP
  - bcrypt for password hashing
  - PyJWT for token management
- **No Breaking Changes**: All Milestone 1 & 2 features remain functional

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| OCR accuracy for music notation | High | Use specialized OMR libraries, manual verification step |
| Local model performance on older hardware | Medium | Show clear hardware requirements, degrade gracefully |
| Image storage size growth | Medium | Implement compression, quota limits, LRU eviction |
| Authentication complexity | Medium | Start with simple email/password, defer OAuth to M4 |
| Citation overhead slowing generation | Low | Async citation resolution, cache source lookups |
| Local mode firewall bypass | Medium | Whitelist only essential domains, user audit logs |

## Open Questions

1. **Should we support multiple local model options or standardize on one?**
   - Option A: Single model (Qwen3 8B) for consistency
   - Option B: Multiple options (Qwen, Llama, Mistral) for flexibility
   - Recommendation: Start with single model, add options based on feedback

2. **How to handle image ingestion failures?**
   - Option A: Fail entire ingestion, require manual fix
   - Option B: Skip failed images, log errors for later review
   - Recommendation: Option B with clear error reporting

3. **Citation granularity - sentence or paragraph level?**
   - Option A: Paragraph-level citations (simpler)
   - Option B: Sentence-level citations (more precise)
   - Recommendation: Paragraph-level initially, refine based on teacher feedback

4. **Should local mode support embeddings generation?**
   - Option A: Use cloud embeddings even in local mode (hybrid)
   - Option B: Fully local with local embedding models
   - Recommendation: Option B for true privacy, accept performance hit

## Success Criteria

- [ ] Image ingestion processes sheet music and diagrams with >80% OCR accuracy
- [ ] Citations appear inline in all RAG-sourced lesson sections
- [ ] Processing mode toggle works, local mode blocks external calls
- [ ] Local model generates lessons with comparable quality to cloud
- [ ] User authentication supports multiple concurrent teachers
- [ ] Sessions are properly isolated per user account
- [ ] Performance: Image processing < 30s per page, local generation < 2min per lesson
- [ ] All Milestone 1 & 2 functionality remains operational

## Related Changes

- `implement-milestone1-foundation` - Extends standards ingestion
- `implement-milestone2-web-interface` - Adds authentication UI, processing mode settings

## Why

Teachers need to:
- **Ingest visual content**: Much music education material is image-based (sheet music, diagrams)
- **Trust lesson sources**: Citations provide transparency and verification for administrators
- **Control data privacy**: Schools require options to keep student data local
- **Share deployments**: Multi-user support enables school-wide adoption

## What Changes

### NEW Capabilities
- **Image Ingestion**: OCR and vision-based content extraction
- **Citation System**: Source tracking and attribution throughout lessons
- **Processing Mode Toggle**: Cloud vs. local LLM selection with privacy controls
- **User Authentication**: Multi-user accounts with session isolation

### ENHANCED Capabilities
- **Standards Ingestion**: Now processes image-based standards documents
- **Lesson Generation**: Includes inline citations and references section
- **Settings UI**: New privacy and processing mode configuration
- **Session Management**: Per-user isolation and history

### MAINTAINED
- All existing CLI functionality
- All Milestone 2 web interface features
- Backward compatibility with existing lesson formats

## Impact

- **Affected specs**:
  - `standards-ingestion` - MODIFIED to support images
  - `lesson-generation` - MODIFIED to include citations
  - `web-interface` - MODIFIED for auth UI and settings
  - `api-server` - MODIFIED for auth endpoints
  - `session-management` - MODIFIED for user isolation
  - NEW: `image-ingestion`, `citation-system`, `processing-mode-toggle`, `user-authentication`

- **Affected code**:
  - `/backend/ingestion` - Add image processing pipeline
  - `/backend/pocketflow` - Add citation tracking to nodes
  - `/backend/api` - Add auth endpoints, processing mode routing
  - `/backend/models` - Add local model integration (Ollama/llama.cpp)
  - `/frontend/components` - Add login, settings UI for processing mode
  - `/frontend/store` - Add auth state management
  - Database schema: Add `users` table, `user_id` foreign keys

- **User impact**:
  - Teachers can now ingest and reference visual materials
  - Lessons include verifiable source citations
  - Schools can deploy locally for privacy compliance
  - Multiple teachers can share a single deployment
