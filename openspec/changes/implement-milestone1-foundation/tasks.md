# Implementation Tasks

## Phase 1: Project Setup & Infrastructure
- [x] Initialize Python project structure with `/backend`, `/cli`, `/data` directories
- [x] Set up Python environment with uv package manager
- [x] Configure pytest testing framework
- [x] Create base Typer CLI application structure
- [x] Set up SQLite database initialization scripts

## Phase 2: PocketFlow Framework
- [x] Implement core PocketFlow classes (Node, Flow, Store)
- [x] Create base Agent class for conversation handling
- [x] Implement message passing between nodes
- [x] Add context store for maintaining conversation state
- [x] Write unit tests for PocketFlow components

## Phase 3: Standards Schema & Database
- [x] Create SQLite schema for standards and objectives tables
- [x] Implement database connection manager
- [x] Create data models for Standard and Objective entities
- [x] Build database migration/initialization scripts
- [x] Add indexes for efficient grade/strand queries

## Phase 4: PDF Standards Ingestion
- [x] Implement PDF reader using pdfplumber
- [x] Create NC standards-specific parser with positional heuristics
- [x] Parse grade levels, strands, standards, and objectives
- [x] Handle multi-column layouts and page breaks
- [x] Map parsed data to canonical schema format
- [x] Add OCRmyPDF fallback for scanned pages
- [x] Create `pocketflow ingest standards` CLI command
- [x] Write ingestion tests with sample PDFs

## Phase 5: Standards Query Layer
- [x] Build standards repository class for database queries
- [x] Implement filtering by grade, strand, and standard ID
- [x] Create methods to retrieve objectives for standards
- [x] Add full-text search for standard descriptions
- [x] Cache frequently accessed standards in memory

## Phase 6: Chutes LLM Integration
- [x] Set up Chutes API client with authentication
- [x] Implement prompt templates for lesson generation
- [x] Create embedding generation for standards
- [x] Add retry logic and error handling
- [x] Build response streaming for real-time updates

## Phase 7: Lesson Generation Agent
- [x] Create LessonAgent extending PocketFlow Agent
- [x] Implement conversation flow for requirements gathering
- [x] Build grade selection with validation
- [x] Add strand selection with descriptions
- [x] Create standard recommendation based on grade/strand
- [x] Implement objective refinement step
- [x] Add optional context collection
- [x] Generate lesson plan from collected requirements
- [x] Include standards citations in output

## Phase 8: Interactive CLI Workflow
- [x] Create `pocketflow generate lesson` command
- [x] Implement chat-style interaction loop
- [x] Add input validation for each conversation step
- [x] Support navigation commands (back, quit, help)
- [x] Display available options at each step
- [x] Show confirmation before generation

## Phase 9: Editor Integration
- [x] Detect system default editor (nano/notepad/vim/code)
- [x] Create temporary file for lesson draft
- [x] Launch editor with generated lesson
- [x] Wait for editor close and detect changes
- [x] Implement post-edit menu (save/regenerate/cancel)
- [x] Add filename/directory selection for saving

## Phase 10: Draft History Management
- [x] Create session workspace in temp directory
- [x] Implement draft versioning (original + 9 latest)
- [x] Store drafts with timestamps and metadata
- [x] Build draft selection interface
- [x] Add pruning logic for 11th draft
- [x] Clean workspace on session exit

## Phase 11: Session Summary
- [x] Track all drafts during session
- [x] Record save locations and standards alignment
- [x] Generate summary table with columns
- [x] Format timestamps in local timezone
- [x] Display before session termination

## Phase 12: Testing & Documentation
- [x] Write integration tests for full CLI workflow
- [x] Create fixtures from real standards data
- [x] Add regression tests for lesson quality
- [x] Document CLI commands and options
- [x] Write teacher-facing usage guide
- [x] Create developer setup instructions

## Phase 13: Error Handling & Polish
- [x] Add graceful degradation for API failures
- [x] Implement progress indicators for long operations
- [x] Improve error messages for common issues
- [x] Add logging for debugging
- [x] Handle keyboard interrupts cleanly
- [x] Validate all file I/O operations

## Validation Checklist
- [x] Ingest all NC standards PDFs successfully
- [x] Generate lesson for each grade level
- [x] Test all four strands (CN, CR, PR, RE)
- [x] Verify editor launches on Windows/Mac/Linux
- [x] Confirm draft history works correctly
- [x] Validate session summary accuracy