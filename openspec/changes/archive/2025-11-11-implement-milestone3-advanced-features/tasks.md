# Implementation Tasks: Milestone 3 Advanced Features

**Change ID**: `implement-milestone3-advanced-features`

## Prerequisites

- [x] Milestone 1 foundation complete (standards ingestion, PocketFlow, CLI)
- [x] Milestone 2 web interface complete (React app, FastAPI, WebSocket)
- [ ] Tesseract OCR installed and accessible
- [ ] Ollama installed with Qwen3 8B model downloaded (for local mode)
- [ ] Vision API credentials configured (Chutes or alternative)

## 1. Image Ingestion Pipeline

### 1.1 Core Infrastructure
- [ ] 1.1.1 Install and configure Tesseract OCR dependencies
- [ ] 1.1.2 Add image preprocessing utilities (deskew, denoise, enhance)
- [ ] 1.1.3 Create `ImageParser` base class in `/backend/parsers/`
- [ ] 1.1.4 Implement `SheetMusicParser` for musical notation extraction
- [ ] 1.1.5 Implement `DiagramParser` for instructional images
- [ ] 1.1.6 Add image format support (PNG, JPG, TIFF, WebP)

### 1.2 Vision Integration
- [ ] 1.2.1 Integrate Chutes vision API for content understanding
- [ ] 1.2.2 Add fallback to local CLIP models for local mode
- [ ] 1.2.3 Implement image embedding generation (vision + text)
- [ ] 1.2.4 Store image embeddings in sqlite-vec with metadata
- [ ] 1.2.5 Create image similarity search functionality

### 1.3 Database & Storage
- [ ] 1.3.1 Add `images` table to SQLite schema
- [ ] 1.3.2 Add foreign keys linking images to standards/objectives
- [ ] 1.3.3 Implement image storage with compression
- [ ] 1.3.4 Add storage quota management (default 5GB, LRU eviction)
- [ ] 1.3.5 Create migration script for existing database

### 1.4 API Integration
- [ ] 1.4.1 Add `POST /api/ingest/image` endpoint for single images
- [ ] 1.4.2 Add `POST /api/ingest/images/batch` for multiple images
- [ ] 1.4.3 Add image upload progress tracking via WebSocket
- [ ] 1.4.4 Implement image validation and error handling
- [ ] 1.4.5 Add `GET /api/images/{id}` for retrieving processed images

### 1.5 UI Components
- [ ] 1.5.1 Create `ImageUpload` component with drag-and-drop
- [ ] 1.5.2 Add image preview and OCR result visualization
- [ ] 1.5.3 Create image verification interface for teachers
- [ ] 1.5.4 Add bulk image upload interface
- [ ] 1.5.5 Show image processing progress with status indicators

### 1.6 Testing
- [ ] 1.6.1 Unit tests for image preprocessing utilities
- [ ] 1.6.2 Integration tests for OCR pipeline with sample sheet music
- [ ] 1.6.3 Test vision API integration with various image types
- [ ] 1.6.4 Test storage quota management and eviction
- [ ] 1.6.5 End-to-end test: upload image → extract → search → generate lesson

## 2. Citation System

### 2.1 Backend Citation Tracking
- [ ] 2.1.1 Add `citations` table to SQLite schema
- [ ] 2.1.2 Extend PocketFlow Node base class with citation tracking
- [ ] 2.1.3 Modify RAG retrieval to capture source metadata
- [ ] 2.1.4 Implement citation deduplication logic
- [ ] 2.1.5 Create citation formatting utilities (IEEE style)

### 2.2 Lesson Generation Integration
- [ ] 2.2.1 Update lesson generation prompt to include citation markers
- [ ] 2.2.2 Parse LLM output to extract citation placeholders
- [ ] 2.2.3 Replace placeholders with formatted citations
- [ ] 2.2.4 Generate references section with full source details
- [ ] 2.2.5 Add citation validation (ensure all cited sources exist)

### 2.3 API Endpoints
- [ ] 2.3.1 Add `citations[]` field to lesson response schema
- [ ] 2.3.2 Add `GET /api/citations/{id}` for citation details
- [ ] 2.3.3 Add `GET /api/sources/{id}/context` for source excerpts
- [ ] 2.3.4 Include citation metadata in WebSocket streaming
- [ ] 2.3.5 Add citation search endpoint for verification

### 2.4 UI Components
- [ ] 2.4.1 Create `CitationInline` component for inline citations
- [ ] 2.4.2 Add citation hover tooltips with source excerpts
- [ ] 2.4.3 Create `ReferencesList` component for bibliography
- [ ] 2.4.4 Add "View Source" button to jump to original document
- [ ] 2.4.5 Highlight cited sections in lesson editor

### 2.5 Export Integration
- [ ] 2.5.1 Include citations in Markdown export
- [ ] 2.5.2 Format citations properly in PDF export
- [ ] 2.5.3 Add references page to PDF export
- [ ] 2.5.4 Support citation styles (IEEE, APA, MLA) - start with IEEE
- [ ] 2.5.5 Test export with complex multi-source lessons

### 2.6 Testing
- [ ] 2.6.1 Unit tests for citation parsing and formatting
- [ ] 2.6.2 Test citation deduplication logic
- [ ] 2.6.3 Integration tests for RAG → citation → display pipeline
- [ ] 2.6.4 Test citation persistence across lesson regeneration
- [ ] 2.6.5 End-to-end test: generate with citations → verify sources → export

## 3. Processing Mode Toggle

### 3.1 Local Model Integration
- [ ] 3.1.1 Add Ollama Python client dependency
- [ ] 3.1.2 Create `LocalModelProvider` class implementing LLM interface
- [ ] 3.1.3 Add model availability checking and validation
- [ ] 3.1.4 Implement model download/update flow with user consent
- [ ] 3.1.5 Add performance monitoring (speed, quality metrics)

### 3.2 Mode Switching Logic
- [ ] 3.2.1 Add `processing_mode` field to user preferences
- [ ] 3.2.2 Create model router to select cloud vs. local provider
- [ ] 3.2.3 Implement network blocking for local mode
- [ ] 3.2.4 Add whitelist for essential domains (model downloads)
- [ ] 3.2.5 Create audit log for network requests in local mode

### 3.3 Configuration & Settings
- [ ] 3.3.1 Add processing mode config to backend settings
- [ ] 3.3.2 Store per-user processing mode preference
- [ ] 3.3.3 Add default mode configuration (cloud default)
- [ ] 3.3.4 Create mode validation logic (check local model available)
- [ ] 3.3.5 Add fallback behavior if mode unavailable

### 3.4 API Updates
- [ ] 3.4.1 Add `GET /api/settings/processing-modes` to list options
- [ ] 3.4.2 Add `PUT /api/settings/processing-mode` to update preference
- [ ] 3.4.3 Include processing mode in generation request
- [ ] 3.4.4 Add `GET /api/models/local/status` for local model health
- [ ] 3.4.5 Add `POST /api/models/local/download` for model management

### 3.5 UI Components
- [ ] 3.5.1 Create `ProcessingModeSelector` in Settings
- [ ] 3.5.2 Add clear privacy warnings for cloud vs. local
- [ ] 3.5.3 Show performance comparison table (speed, quality)
- [ ] 3.5.4 Display local model status (installed, version, health)
- [ ] 3.5.5 Add model download progress indicator
- [ ] 3.5.6 Show current mode indicator in header/status bar

### 3.6 Testing
- [ ] 3.6.1 Test mode switching without data loss
- [ ] 3.6.2 Verify network blocking in local mode
- [ ] 3.6.3 Test local model fallback scenarios
- [ ] 3.6.4 Compare lesson quality between cloud and local
- [ ] 3.6.5 End-to-end test: switch mode → generate → verify privacy

## 4. User Authentication

### 4.1 Database Schema
- [ ] 4.1.1 Create `users` table (id, email, password_hash, role, created_at)
- [ ] 4.1.2 Add `user_id` foreign key to `sessions` table
- [ ] 4.1.3 Add `user_id` foreign key to `lessons` table
- [ ] 4.1.4 Create indexes on user_id columns for performance
- [ ] 4.1.5 Create database migration script

### 4.2 Authentication Backend
- [ ] 4.2.1 Install bcrypt and PyJWT dependencies
- [ ] 4.2.2 Create `auth` module with password hashing utilities
- [ ] 4.2.3 Implement JWT token generation (access + refresh)
- [ ] 4.2.4 Create token validation middleware
- [ ] 4.2.5 Implement role-based authorization decorators

### 4.3 Auth API Endpoints
- [ ] 4.3.1 Add `POST /api/auth/register` (admin only)
- [ ] 4.3.2 Add `POST /api/auth/login` with rate limiting
- [ ] 4.3.3 Add `POST /api/auth/logout` to invalidate tokens
- [ ] 4.3.4 Add `POST /api/auth/refresh` for token refresh
- [ ] 4.3.5 Add `GET /api/auth/me` for current user info
- [ ] 4.3.6 Add `PUT /api/auth/password` for password changes

### 4.4 User Management
- [ ] 4.4.1 Add `GET /api/users` (admin only) to list users
- [ ] 4.4.2 Add `GET /api/users/{id}` (admin only) for user details
- [ ] 4.4.3 Add `PUT /api/users/{id}` (admin only) for user updates
- [ ] 4.4.4 Add `DELETE /api/users/{id}` (admin only) for user deletion
- [ ] 4.4.5 Implement session timeout (2 hours default)

### 4.5 Session Isolation
- [ ] 4.5.1 Update all session queries to filter by user_id
- [ ] 4.5.2 Update all lesson queries to filter by user_id
- [ ] 4.5.3 Add authorization checks to all protected endpoints
- [ ] 4.5.4 Test cross-user access prevention
- [ ] 4.5.5 Add admin override for user support scenarios

### 4.6 Frontend Auth
- [ ] 4.6.1 Create `LoginPage` component
- [ ] 4.6.2 Create auth store in Zustand (user, token, logout)
- [ ] 4.6.3 Implement auth interceptor for API requests
- [ ] 4.6.4 Add token refresh logic for expired tokens
- [ ] 4.6.5 Create `ProtectedRoute` wrapper for authenticated pages
- [ ] 4.6.6 Add logout button in header

### 4.7 Admin Interface
- [ ] 4.7.1 Create `UserManagement` page (admin only)
- [ ] 4.7.2 Add user creation form for admins
- [ ] 4.7.3 Display user list with roles and status
- [ ] 4.7.4 Add user edit/delete actions
- [ ] 4.7.5 Show basic usage statistics per user

### 4.8 Security Hardening
- [ ] 4.8.1 Add HTTPS requirement check in production
- [ ] 4.8.2 Implement rate limiting on auth endpoints (5 attempts/minute)
- [ ] 4.8.3 Add password complexity validation
- [ ] 4.8.4 Implement CSRF protection for auth endpoints
- [ ] 4.8.5 Add security headers (HSTS, CSP, etc.)
- [ ] 4.8.6 Create security audit logging

### 4.9 Testing
- [ ] 4.9.1 Test registration, login, logout flows
- [ ] 4.9.2 Test token refresh mechanism
- [ ] 4.9.3 Test session isolation between users
- [ ] 4.9.4 Test role-based access control
- [ ] 4.9.5 Security tests: brute force, token manipulation, SQL injection
- [ ] 4.9.6 End-to-end test: multi-user concurrent sessions

## 5. Integration & Polish

### 5.1 Cross-Feature Integration
- [ ] 5.1.1 Test image ingestion with citations
- [ ] 5.1.2 Test local mode with image processing
- [ ] 5.1.3 Test auth with all other features
- [ ] 5.1.4 Verify session persistence across features
- [ ] 5.1.5 Test export with all new features enabled

### 5.2 Performance Optimization
- [ ] 5.2.1 Profile image processing pipeline, optimize bottlenecks
- [ ] 5.2.2 Profile citation resolution, add caching
- [ ] 5.2.3 Optimize local model inference speed
- [ ] 5.2.4 Add database indexes for new queries
- [ ] 5.2.5 Implement lazy loading for image galleries

### 5.3 Documentation
- [ ] 5.3.1 Update README with Milestone 3 features
- [ ] 5.3.2 Document image ingestion workflow
- [ ] 5.3.3 Document citation system for teachers
- [ ] 5.3.4 Create local model setup guide
- [ ] 5.3.5 Document user management for admins
- [ ] 5.3.6 Update API documentation

### 5.4 Error Handling & UX
- [ ] 5.4.1 Add comprehensive error messages for image failures
- [ ] 5.4.2 Add helpful errors for missing local models
- [ ] 5.4.3 Improve auth error messages (wrong password, etc.)
- [ ] 5.4.4 Add loading states for all long operations
- [ ] 5.4.5 Implement graceful degradation for missing features

### 5.5 Backward Compatibility
- [ ] 5.5.1 Verify Milestone 1 CLI still functional
- [ ] 5.5.2 Verify Milestone 2 web features still work
- [ ] 5.5.3 Test migration from M2 to M3 (existing data intact)
- [ ] 5.5.4 Ensure old lesson formats can be opened
- [ ] 5.5.5 Test unauthenticated mode for single-user deployments

### 5.6 Final Testing
- [ ] 5.6.1 Complete end-to-end testing of all four capabilities
- [ ] 5.6.2 Cross-browser testing (Chrome, Firefox, Safari)
- [ ] 5.6.3 Performance testing (load times, generation speed)
- [ ] 5.6.4 Security audit and penetration testing
- [ ] 5.6.5 User acceptance testing with teachers

## 6. Deployment & Release

### 6.1 Pre-Release
- [ ] 6.1.1 Update version numbers in package.json and pyproject.toml
- [ ] 6.1.2 Create database migration scripts
- [ ] 6.1.3 Update environment variable templates
- [ ] 6.1.4 Create deployment checklist
- [ ] 6.1.5 Write release notes

### 6.2 Deployment
- [ ] 6.2.1 Deploy backend with new auth system
- [ ] 6.2.2 Deploy frontend with new UI components
- [ ] 6.2.3 Run database migrations
- [ ] 6.2.4 Create initial admin account
- [ ] 6.2.5 Verify all services running correctly

### 6.3 Post-Release
- [ ] 6.3.1 Monitor error logs for new issues
- [ ] 6.3.2 Track performance metrics
- [ ] 6.3.3 Collect user feedback
- [ ] 6.3.4 Plan hotfixes if needed
- [ ] 6.3.5 Archive this change to OpenSpec archive/

## Notes

- **Sequential dependencies**: Complete sections 1-4 before integration (section 5)
- **Testing**: Run tests continuously, not just at the end
- **Local model**: Qwen3 8B requires 16GB RAM minimum
- **Image processing**: Can be resource-intensive, implement queue system
- **Security**: Auth implementation requires careful review before production
- **Rollback plan**: Keep Milestone 2 deployment available during M3 beta testing
