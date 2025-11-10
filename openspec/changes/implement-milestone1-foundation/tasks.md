# Implementation Tasks

## Phase 1: Project Setup & Infrastructure
- [ ] Initialize Python project structure with `/backend`, `/cli`, `/data` directories
- [ ] Set up Python environment with uv package manager
- [ ] Configure pytest testing framework
- [ ] Create base Typer CLI application structure
- [ ] Set up SQLite database initialization scripts

## Phase 2: PocketFlow Framework
- [ ] Implement core PocketFlow classes (Node, Flow, Store)
- [ ] Create base Agent class for conversation handling
- [ ] Implement message passing between nodes
- [ ] Add context store for maintaining conversation state
- [ ] Write unit tests for PocketFlow components

## Phase 3: Standards Schema & Database
- [ ] Create SQLite schema for standards and objectives tables
- [ ] Implement database connection manager
- [ ] Create data models for Standard and Objective entities
- [ ] Build database migration/initialization scripts
- [ ] Add indexes for efficient grade/strand queries

## Phase 4: PDF Standards Ingestion
- [ ] Implement PDF reader using pdfplumber
- [ ] Create NC standards-specific parser with positional heuristics
- [ ] Parse grade levels, strands, standards, and objectives
- [ ] Handle multi-column layouts and page breaks
- [ ] Map parsed data to canonical schema format
- [ ] Add OCRmyPDF fallback for scanned pages
- [ ] Create `pocketflow ingest standards` CLI command
- [ ] Write ingestion tests with sample PDFs

## Phase 5: Standards Query Layer
- [ ] Build standards repository class for database queries
- [ ] Implement filtering by grade, strand, and standard ID
- [ ] Create methods to retrieve objectives for standards
- [ ] Add full-text search for standard descriptions
- [ ] Cache frequently accessed standards in memory

## Phase 6: Chutes LLM Integration
- [ ] Set up Chutes API client with authentication
- [ ] Implement prompt templates for lesson generation
- [ ] Create embedding generation for standards
- [ ] Add retry logic and error handling
- [ ] Build response streaming for real-time updates

## Phase 7: Lesson Generation Agent
- [ ] Create LessonAgent extending PocketFlow Agent
- [ ] Implement conversation flow for requirements gathering
- [ ] Build grade selection with validation
- [ ] Add strand selection with descriptions
- [ ] Create standard recommendation based on grade/strand
- [ ] Implement objective refinement step
- [ ] Add optional context collection
- [ ] Generate lesson plan from collected requirements
- [ ] Include standards citations in output

## Phase 8: Interactive CLI Workflow
- [ ] Create `pocketflow generate lesson` command
- [ ] Implement chat-style interaction loop
- [ ] Add input validation for each conversation step
- [ ] Support navigation commands (back, quit, help)
- [ ] Display available options at each step
- [ ] Show confirmation before generation

## Phase 9: Editor Integration
- [ ] Detect system default editor (nano/notepad)
- [ ] Create temporary file for lesson draft
- [ ] Launch editor with generated lesson
- [ ] Wait for editor close and detect changes
- [ ] Implement post-edit menu (save/regenerate/cancel)
- [ ] Add filename/directory selection for saving

## Phase 10: Draft History Management
- [ ] Create session workspace in temp directory
- [ ] Implement draft versioning (original + 9 latest)
- [ ] Store drafts with timestamps and metadata
- [ ] Build draft selection interface
- [ ] Add pruning logic for 11th draft
- [ ] Clean workspace on session exit

## Phase 11: Session Summary
- [ ] Track all drafts during session
- [ ] Record save locations and standards alignment
- [ ] Generate summary table with columns
- [ ] Format timestamps in local timezone
- [ ] Display before session termination

## Phase 12: Testing & Documentation
- [ ] Write integration tests for full CLI workflow
- [ ] Create fixtures from real standards data
- [ ] Add regression tests for lesson quality
- [ ] Document CLI commands and options
- [ ] Write teacher-facing usage guide
- [ ] Create developer setup instructions

## Phase 13: Error Handling & Polish
- [ ] Add graceful degradation for API failures
- [ ] Implement progress indicators for long operations
- [ ] Improve error messages for common issues
- [ ] Add logging for debugging
- [ ] Handle keyboard interrupts cleanly
- [ ] Validate all file I/O operations

## Validation Checklist
- [ ] Ingest all NC standards PDFs successfully
- [ ] Generate lesson for each grade level
- [ ] Test all four strands (CN, CR, PR, RE)
- [ ] Verify editor launches on Windows/Mac/Linux
- [ ] Confirm draft history works correctly
- [ ] Validate session summary accuracy