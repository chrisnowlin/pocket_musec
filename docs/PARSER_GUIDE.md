# Parser System Guide

## Overview

The Pocket Musec parser system has been completely refactored to support multiple document types with specialized parsers. The system includes automatic document classification and routing to the appropriate parser.

## Document Types Supported

### 1. **Formal Standards Documents**
- **Parser**: `nc_standards_formal_parser.py`
- **Examples**: "Final Music NCSCOS", "Final VIM NCSCOS"
- **Features**:
  - Vision-first parsing with AI (optional)
  - Automatic fallback to table-based and structured parsers
  - Extracts standards with IDs (e.g., K.CN.1) and objectives
  - Validates completeness (checks for all grades and strands)

### 2. **Unpacking Documents**
- **Parser**: `unpacking_narrative_parser.py`
- **Examples**: "Kindergarten GM Unpacking", "Advanced VIM Unpacking"
- **Features**:
  - Extracts narrative sections with titles
  - Identifies teaching strategies
  - Captures assessment guidance
  - Auto-detects grade level from content

### 3. **Reference & Resource Documents**
- **Parser**: `reference_resource_parser.py`
- **Examples**: "Arts Education Standards Glossary", "VIM and TT FAQ"
- **Features**:
  - Auto-detects document type (glossary/FAQ/catalog)
  - Extracts term-definition pairs
  - Parses Q&A format
  - Links definitions to related standards

### 4. **Alignment Documents**
- **Parser**: `alignment_matrix_parser.py`
- **Examples**: "Horizontal Alignment", "Vertical Alignment"
- **Features**:
  - Extracts relationships between standards
  - Handles both table-based and text-based formats
  - Maps skill progressions across grades
  - 850+ relationships from vertical alignment docs

### 5. **Quick Reference Guides**
- **Classifies as**: GUIDE type
- **Examples**: "1 PAGE QUICK GUIDES"
- **Recommended Parser**: `simple_layout_parser.py`

## Parser Architecture

### Core Parsers

```
backend/ingestion/
├── nc_standards_formal_parser.py      # Production standards parser
├── nc_standards_table_parser.py       # Table-based extraction
├── nc_standards_structured_parser.py  # Text-based comprehensive
├── nc_standards_precise_parser.py     # High-precision pattern matching
├── nc_standards_positional_parser.py  # Positional heuristics
├── nc_standards_backup_parser.py      # Emergency fallback
├── complex_layout_parser.py           # Vision for complex layouts
├── simple_layout_parser.py            # Vision for simple layouts
├── unpacking_narrative_parser.py      # Narrative content extraction
├── reference_resource_parser.py       # Reference materials
├── alignment_matrix_parser.py         # Relationship extraction
└── pdf_parser.py                      # Base PDF utilities
```

### Document Classifier

The `document_classifier.py` provides automatic detection of document types:

- **Filename-based**: Matches patterns in filenames
- **Content-based**: Analyzes first 5 pages for content markers
- **Confidence scoring**: Returns classification confidence percentage

## Usage

### CLI Usage

#### Auto-Classification (Recommended)
```bash
# Automatically detect document type and use appropriate parser
python -m cli.main ingest auto "path/to/document.pdf"

# With options
python -m cli.main ingest auto "path/to/document.pdf" --force --use-vision
```

#### Manual Standards Ingestion
```bash
# Use standards parser explicitly
python -m cli.main ingest standards "path/to/standards.pdf"

# Fast mode (no vision)
python -m cli.main ingest standards "path/to/standards.pdf" --no-vision
```

### Programmatic Usage

#### Using the Formal Standards Parser
```python
from backend.ingestion.nc_standards_formal_parser import NCStandardsParser

# Initialize parser (vision mode for best accuracy)
parser = NCStandardsParser(use_vision=True)

# Parse document
standards = parser.parse_standards_document("path/to/standards.pdf")

# Get statistics
stats = parser.get_statistics()
print(f"Found {stats['total_standards']} standards")
print(f"Found {stats['total_objectives']} objectives")

# Convert to database models
db_standards, db_objectives = parser.normalize_to_models("source.pdf")
```

#### Using the Unpacking Parser
```python
from backend.ingestion.unpacking_narrative_parser import UnpackingNarrativeParser

parser = UnpackingNarrativeParser()
sections = parser.parse_unpacking_document("path/to/unpacking.pdf")

for section in sections:
    print(f"Section: {section.section_title}")
    print(f"Grade: {section.grade_level}")
    print(f"Teaching strategies: {len(section.teaching_strategies)}")
```

#### Using the Reference Parser
```python
from backend.ingestion.reference_resource_parser import ReferenceResourceParser

parser = ReferenceResourceParser()

# Auto-detect document type
entries = parser.parse_reference_document("path/to/glossary.pdf", doc_type="auto")

# Or specify type explicitly
entries = parser.parse_reference_document("path/to/faq.pdf", doc_type="faq")

for entry in entries:
    print(f"{entry.title}: {entry.description[:100]}...")
```

#### Using the Alignment Parser
```python
from backend.ingestion.alignment_matrix_parser import AlignmentMatrixParser

parser = AlignmentMatrixParser()
relationships = parser.parse_alignment_document("path/to/alignment.pdf", alignment_type="vertical")

for rel in relationships[:5]:
    print(f"{rel.standard_id} relates to {rel.related_standard_ids}")
    print(f"  Type: {rel.relationship_type}")
    print(f"  Grade: {rel.grade_level}, Strand: {rel.strand_code}")
```

#### Using the Document Classifier
```python
from backend.ingestion.document_classifier import DocumentClassifier, DocumentType

classifier = DocumentClassifier()
doc_type, confidence = classifier.classify("path/to/document.pdf")

print(f"Document type: {doc_type.value}")
print(f"Confidence: {confidence:.0%}")

if doc_type == DocumentType.STANDARDS:
    # Use standards parser
    pass
elif doc_type == DocumentType.UNPACKING:
    # Use unpacking parser
    pass
```

## Parser Selection Guide

### Which Parser Should I Use?

| Document Type | Primary Parser | Fallback Parser | Notes |
|--------------|----------------|-----------------|-------|
| NC Music Standards | `nc_standards_formal_parser` | Auto-fallback | Uses vision → table → structured |
| Grade Unpacking Docs | `unpacking_narrative_parser` | - | Handles narrative content |
| Glossaries/FAQs | `reference_resource_parser` | - | Auto-detects format |
| Alignment Matrices | `alignment_matrix_parser` | - | Handles tables & text |
| Quick Guides | `simple_layout_parser` | - | Lightweight vision |
| Complex Multi-column | `complex_layout_parser` | - | Full vision processing |

### Performance Comparison

| Parser | Speed | Accuracy | Best For |
|--------|-------|----------|----------|
| Vision (formal) | Slow (~10 min) | 95%+ | High-stakes standards |
| Table-based | Fast (~30 sec) | 90%+ | Well-structured PDFs |
| Structured text | Fast (~30 sec) | 85%+ | General standards |
| Alignment text | Medium (~2 min) | 80%+ | Text-heavy alignment |

## Validation & Testing

### Running Validation Tests
```bash
# Run comprehensive validation suite
python validate_parsers.py

# Expected output:
# ✓ Formal Standards Parser: 80 standards, 200 objectives
# ✓ Unpacking Parser: 7+ sections
# ✓ Reference Parser: 312 glossary entries  
# ✓ Alignment Parser: 850 relationships
# ✓ Document Classifier: 100% accuracy
```

### Test Results (Current)
- **Formal Standards Parser**: ✓ 80 standards, 200 objectives extracted
- **Unpacking Narrative Parser**: ✓ 7 sections with teaching content
- **Reference Resource Parser**: ✓ 312 glossary entries
- **Alignment Matrix Parser**: ✓ 850 relationships (vertical)
- **Document Classifier**: ✓ 100% accuracy on core types

## Configuration

### Vision Processing
Vision processing is optional but provides the highest accuracy:

```python
# Enable vision (slow but accurate)
parser = NCStandardsParser(use_vision=True)

# Disable vision (fast hybrid mode)
parser = NCStandardsParser(use_vision=False)
```

### Parser Fallback Chain
The formal standards parser uses this fallback chain:
1. **Vision AI** (if enabled and available)
2. **Table Parser** (if vision fails or disabled)
3. **Structured Parser** (final fallback)

## Common Patterns

### Standard ID Format
All parsers recognize this pattern:
- Format: `{grade}.{strand}.{number}[.{objective}]`
- Examples: `K.CN.1`, `5.CR.2.3`, `AC.PR.1`
- Grades: K, 1-8, BE, IN, AD, AC
- Strands: CN (Connect), CR (Create), PR (Present), RE (Respond)

### Parsed Data Structures

#### Standard
```python
@dataclass
class ParsedStandard:
    grade_level: str          # "K", "1", "2", ..., "AC"
    strand_code: str          # "CN", "CR", "PR", "RE"
    strand_name: str          # "Connect", "Create", etc.
    strand_description: str   # Full description
    standard_id: str          # "K.CN.1"
    standard_text: str        # Full text of standard
    objectives: List[str]     # List of objective texts
    source_document: str      # Source filename
    page_number: int          # Page in PDF
```

## Troubleshooting

### Parser Not Finding Content

**Problem**: Parser returns empty results

**Solutions**:
1. Check if document has extractable text (not scanned image)
2. Try different parser (formal → table → structured)
3. Enable vision processing for complex layouts
4. Check validation logs for specific errors

### Incorrect Classification

**Problem**: Document classified as wrong type

**Solutions**:
1. Use explicit parser instead of auto-classification
2. Check filename patterns match expected format
3. Verify content markers in first 5 pages
4. Report misclassification for improvement

### Missing Objectives

**Problem**: Standards found but objectives missing

**Solutions**:
1. Check if document has objectives (some don't)
2. Verify objective format matches pattern
3. Try vision parser for better accuracy
4. Check page range (some parsers limit pages)

## Best Practices

1. **Use Auto-Classification**: Let the system choose the right parser
2. **Enable Vision for Critical Docs**: Use `--use-vision` for standards
3. **Validate Results**: Check statistics after parsing
4. **Handle Errors Gracefully**: Use try-except blocks
5. **Log Extraction Details**: Enable debug logging for troubleshooting

## Examples

### Complete Ingestion Workflow
```python
from backend.ingestion.document_classifier import DocumentClassifier
from backend.ingestion.nc_standards_formal_parser import NCStandardsParser
from backend.ingestion.unpacking_narrative_parser import UnpackingNarrativeParser
from backend.repositories.database import DatabaseManager

# 1. Classify document
classifier = DocumentClassifier()
doc_type, confidence = classifier.classify("document.pdf")

# 2. Use appropriate parser
if doc_type == DocumentType.STANDARDS:
    parser = NCStandardsParser(use_vision=False)
    standards = parser.parse_standards_document("document.pdf")
    
    # 3. Save to database
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    
    db_standards, db_objectives = parser.normalize_to_models("document.pdf")
    # ... save to database ...
    
elif doc_type == DocumentType.UNPACKING:
    parser = UnpackingNarrativeParser()
    sections = parser.parse_unpacking_document("document.pdf")
    # ... process sections ...
```

## Contributing

When adding new parsers:
1. Inherit common patterns from existing parsers
2. Add to `document_classifier.py` if new document type
3. Add validation tests to `validate_parsers.py`
4. Update this documentation
5. Export from `backend/ingestion/__init__.py`

## Support

For issues or questions:
1. Check validation tests: `python validate_parsers.py`
2. Enable debug logging: `export LOG_LEVEL=DEBUG`
3. Review parser statistics output
4. Consult parser-specific docstrings
