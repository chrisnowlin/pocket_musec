# Archive Directory

This directory contains historical debug scripts, test files, and reports from the development process.

## Directory Structure

### `debug_scripts/`
One-off debug and analysis scripts used during development. These were useful for troubleshooting specific issues but are not part of the main application.

**Key scripts:**
- `debug_*.py` - Various debugging utilities for parsers, APIs, and data extraction
- `compare_parsers.py` - Parser comparison and validation tools
- `verify_data_quality.py` - Data quality verification scripts
- `run_vision_parser.py`, `simple_vision_parser.py` - Vision API testing scripts

### `test_scripts/`
Standalone test scripts used during development before formal test suite was established.

**Categories:**
- `test_*.py` - Various test scripts for specific components
- Parser testing and validation scripts
- API integration tests
- Workflow validation tests

### `reports/`
Documentation and analysis reports from different development phases.

**Key reports:**
- `DEBUG_SUMMARY.md` - Comprehensive debug summary
- `PHASE*.md` - Phase completion reports (6, 7, 8, 10, 11, 13)
- `VISION_PARSER_*.md` - Vision parser analysis and results
- `PARSER_VALIDATION_REPORT.md` - Parser validation findings
- `E2E_WORKFLOW_TEST_RESULTS.md` - End-to-end testing results
- `UNPACKING_DOCUMENTS_ANALYSIS.md` - Document type analysis

## Usage

These files are kept for historical reference and debugging purposes. For current development, use:

- Main application code: `/backend/`, `/cli/`, `/tests/`
- Current documentation: `/docs/`
- Active test suite: `/tests/`

## Maintenance

New debug scripts should be moved here once their immediate purpose is complete. Active development scripts should remain in the main project directories.
