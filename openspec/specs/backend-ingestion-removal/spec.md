# Backend Ingestion Removal Specification

## Purpose
Remove the entire ingestion pipeline from the backend to eliminate complexity, maintenance overhead, and reliability issues while preserving all other functionality.

## Requirements

### Requirement: Remove ingestion directory completely
The system SHALL completely remove the ingestion directory and all its contents.

#### Scenario: Developer removes the ingestion pipeline
- **WHEN** the removal process is executed
- **THEN** the entire `/backend/ingestion/` directory is deleted
- **AND** all parser files are removed (nc_standards_unified_parser.py, complex_layout_parser.py, etc.)
- **AND** all utility files are removed (pdf_parser.py, document_classifier.py, etc.)

### Requirement: Remove PocketFlow ingestion components
The system SHALL remove all PocketFlow ingestion-specific components.

#### Scenario: Developer cleans up PocketFlow framework
- **WHEN** the removal process is executed
- **THEN** `ingestion_agent.py` is completely removed
- **AND** `ingestion_nodes.py` is completely removed
- **AND** no ingestion-related workflow components remain

### Requirement: Remove ingestion API routes
The system SHALL remove all ingestion HTTP endpoints from the FastAPI application.

#### Scenario: Developer removes ingestion HTTP endpoints
- **WHEN** the removal process is executed
- **THEN** `/api/routes/ingestion.py` is completely removed
- **AND** the ingestion router is excluded from main FastAPI app
- **AND** all ingestion endpoints become unavailable (/classify, /ingest, /document-types, etc.)

### Requirement: Clean up ingestion imports and dependencies
The system SHALL remove all ingestion-related imports and broken references.

#### Scenario: Developer ensures backend starts cleanly
- **WHEN** the removal process is executed
- **THEN** all ingestion imports are removed from other modules
- **AND** the backend starts without import errors
- **AND** no broken references remain in the codebase

### Requirement: Update main FastAPI application
The FastAPI application SHALL start successfully without ingestion routes.

#### Scenario: Main application starts without ingestion
- **WHEN** the ingestion router is removed
- **THEN** the main application imports are updated
- **AND** the application starts successfully without ingestion routes
- **AND** other API routes remain functional

### Requirement: Maintain existing database functionality
The system SHALL maintain all existing database operations after ingestion removal.

#### Scenario: Database operations continue after ingestion removal
- **WHEN** the ingestion pipeline is removed
- **THEN** all existing database tables remain intact
- **AND** standards retrieval continues to work
- **AND** lesson generation can access existing data