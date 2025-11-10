# Specification: Standards Ingestion

## ADDED Requirements

### Requirement: Parse NC Music Standards PDFs
The system SHALL extract structured data from North Carolina music education standards PDF documents.

#### Scenario: Successful PDF parsing
Given a PDF file "Final Music NCSCOS - Google Docs.pdf" containing NC music standards
When the ingestion command `pocketflow ingest standards` is executed
Then the system extracts grade levels, strands, standards, and objectives
And stores them in the SQLite database with proper relationships
And reports the count of standards and objectives processed

#### Scenario: Handle multi-column layouts
Given a PDF with 2-column layout containing standards text
When the parser processes the document
Then it correctly associates text across columns
And maintains the relationship between standards and their objectives

#### Scenario: OCR fallback for scanned pages
Given a PDF containing scanned images of standards documents
When pdfplumber fails to extract text
Then the system automatically attempts OCR using OCRmyPDF
And processes the extracted text through the standard pipeline

### Requirement: Canonical Standards Schema
The system MUST store standards using the defined canonical schema format.

#### Scenario: Store standard with objectives
Given a standard "K.CN.1" with text "Relate musical ideas and works with contexts"
And objectives "K.CN.1.1" and "K.CN.1.2" with their descriptions
When the standard is persisted
Then it is stored with standard_id, grade_level "K", strand_code "CN"
And the objectives are linked via foreign key relationship
And all required fields are populated (strand_name, strand_description, etc.)

#### Scenario: Grade level validation
Given an input with grade level data
When the grade is one of: K, 1, 2, 3, 4, 5, 6, 7, 8, BE, IN, AC, AD
Then it is accepted and stored
When the grade is not in the valid set
Then the parser logs a warning and skips the entry

### Requirement: Database Initialization
The system SHALL create and manage the standards database schema.

#### Scenario: First-time setup
Given no existing database at `data/standards/standards.db`
When the ingestion command runs
Then it creates the database with standards and objectives tables
And applies all indexes for query optimization
And initializes metadata tables for tracking ingestion

#### Scenario: Re-ingestion handling
Given an existing database with standards data
When the ingestion command runs again
Then it prompts whether to append or replace existing data
And maintains data integrity during the operation

### Requirement: Ingestion Reporting
The system MUST provide clear feedback on ingestion progress and results.

#### Scenario: Progress indicators
Given a folder with 10 PDF files to process
When ingestion begins
Then it shows a progress bar or counter (1/10, 2/10, etc.)
And displays the current file being processed
And estimates time remaining based on files processed

#### Scenario: Summary report
Given completed ingestion of standards documents
When the process finishes
Then it displays total standards imported by grade level
And shows objective count per strand
And reports any parsing failures or warnings
And logs detailed results to `data/standards/ingestion.log`