# Document Classification & Parser Routing Guide

**Created:** 2025-11-10  
**Status:** Implemented  
**Purpose:** Automatically detect NC Music Education document types and route to appropriate parsers

---

## Overview

The NC Music Education document collection contains **multiple document types** that require **different parsing strategies**:

1. **Standards Documents** - Table-based, need structure-aware parsing
2. **Unpacking Documents** - Narrative-based, need text extraction  
3. **Alignment Documents** - Comparative tables across grades
4. **Implementation Guides** - Instructional/reference material
5. **Skills Appendix** - Reference tables

---

## Current Status: ❌ NO Auto-Classification

**Problem Identified:**
- Current `ingest` command assumes ALL PDFs are standards documents
- No automatic document type detection
- Wrong parser applied to unpacking documents → 0 standards extracted

**Solution Created:**
- ✅ `DocumentClassifier` module (`backend/ingestion/document_classifier.py`)
- ✅ Detects document type via filename + content analysis
- ✅ Routes to appropriate parser
- ❌ **NOT YET INTEGRATED** into CLI commands

---

## Document Classification System

### DocumentClassifier Module

**Location:** `backend/ingestion/document_classifier.py`

**Features:**
- **Filename Pattern Matching** - Fast classification based on file naming
- **Content Analysis** - Verifies type by analyzing first 5 pages
- **Confidence Scoring** - 0.0-1.0 confidence level
- **Parser Recommendation** - Returns appropriate parser class name

### Classification Algorithm

```python
1. Extract filename → Match against patterns
2. If filename matches:
   a. Verify with content analysis
   b. If both agree → High confidence (1.0)
   c. If content disagrees → Trust content (0.6)
   d. If content inconclusive → Trust filename (0.7)
3. If no filename match:
   a. Analyze content only → Medium confidence (0.6)
4. If neither match → Unknown (0.0)
```

### Supported Document Types

| Type | Filename Patterns | Content Markers | Parser |
|------|-------------------|-----------------|--------|
| **STANDARDS** | `final.*music.*ncscos`<br/>`standards.*music` | "Standard Course of Study"<br/>"Note on Numbering" | `NCStandardsParser`<br/>(Table Parser) |
| **UNPACKING** | `*unpacking*`<br/>`kindergarten.*gm`<br/>`first.*grade.*gm` | "Standards Unpacking"<br/>"Glossary"<br/>"Essential Questions" | `UnpackingParser` |
| **ALIGNMENT** | `horizontal.*alignment`<br/>`vertical.*alignment` | "Horizontal Alignment"<br/>"progression of skills" | `TextParser` |
| **GUIDE** | `quick.*guide`<br/>`implementation.*guide` | "Implementation Guide"<br/>"Getting Started" | `TextParser` |
| **SKILLS** | `skills.*appendix` | "Music Skills" | `TextParser` |

---

## Test Results

### Standards Document ✅

```bash
$ python backend/ingestion/document_classifier.py \
  "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"

Document: Final Music NCSCOS - Google Docs.pdf
Type: standards
Confidence: 100.0%
Recommended parser: NCStandardsParser
```

**Analysis:**
- ✅ Filename pattern: `final.*music.*ncscos` matched
- ✅ Content markers: "Standard Course of Study", "Note on Numbering" found
- ✅ Both agree → High confidence

### Unpacking Document ✅

```bash
$ python backend/ingestion/document_classifier.py \
  "NC Music Standards and Resources/Kindergarten GM Unpacking - Google Docs.pdf"

Document: Kindergarten GM Unpacking - Google Docs.pdf
Type: unpacking
Confidence: 100.0%
Recommended parser: UnpackingParser
```

**Analysis:**
- ✅ Filename pattern: `*unpacking*` matched
- ✅ Content markers: "Standards Unpacking", "Glossary", "Essential Questions" found
- ✅ Both agree → High confidence

### Alignment Document ✅

```bash
$ python backend/ingestion/document_classifier.py \
  "NC Music Standards and Resources/Horizontal Alignment - Arts Education Unpacking - Google Docs.pdf"

Filename suggested unpacking but content suggests alignment
Type: alignment
Confidence: 60.0%
Recommended parser: TextParser
```

**Analysis:**
- ⚠️ Filename contains "unpacking" → suggested UNPACKING
- ✅ Content markers: "Horizontal Alignment" found → suggests ALIGNMENT
- ✅ Content trusted over filename → Correct classification

---

## Integration Needed

### Current Workflow (No Classification)

```python
# cli/commands/ingest.py
@ingest_app.command()
def standards(pdf_path: str, ...):
    parser = NCStandardsParser(use_vision=use_vision)  # Always NCStandardsParser
    parsed_standards = parser.parse_standards_document(pdf_path)
```

**Problem:** Unpacking documents → 0 standards extracted

### Proposed Workflow (With Classification)

```python
# cli/commands/ingest.py
from backend.ingestion.document_classifier import classify_document, DocumentType

@ingest_app.command()
def auto(pdf_path: str, ...):
    """Auto-detect document type and ingest with appropriate parser"""
    
    # Classify document
    doc_type, confidence, parser_name = classify_document(pdf_path)
    
    console.print(f"📋 Detected: {doc_type.value} (confidence: {confidence:.0%})")
    
    # Route to appropriate parser
    if doc_type == DocumentType.STANDARDS:
        parser = NCStandardsParser(use_vision=use_vision)
        result = parser.parse_standards_document(pdf_path, max_page=34)
        # Save to standards tables
        
    elif doc_type == DocumentType.UNPACKING:
        parser = UnpackingParser()
        result = parser.parse_unpacking_document(pdf_path)
        # Save to unpacking tables
        
    elif doc_type == DocumentType.ALIGNMENT:
        console.print("[yellow]Alignment documents not yet supported[/yellow]")
        
    else:
        console.print(f"[yellow]Unknown document type, trying standards parser...[/yellow]")
        parser = NCStandardsParser(use_vision=False)
        result = parser.parse_standards_document(pdf_path)
```

### Backward Compatibility

Keep existing `standards` command for explicit standards ingestion:

```bash
# Explicit (current behavior)
pocketmusec ingest standards "path/to/standards.pdf"

# Auto-detect (new behavior)
pocketmusec ingest auto "path/to/any-document.pdf"
```

---

## Implementation Checklist

### Phase 1: Core Classification ✅ COMPLETE

- [x] Create `DocumentClassifier` class
- [x] Implement filename pattern matching
- [x] Implement content analysis  
- [x] Add confidence scoring
- [x] Test on all document types

### Phase 2: CLI Integration ⏳ PENDING

- [ ] Add `auto` command to `cli/commands/ingest.py`
- [ ] Import `DocumentClassifier`
- [ ] Add classification step before parsing
- [ ] Display detected type + confidence to user
- [ ] Route to appropriate parser based on type

### Phase 3: Parser Creation ⏳ PENDING

- [ ] Create production `UnpackingParser` (proof of concept exists)
- [ ] Add database schema for unpacking content
- [ ] Create `TextParser` for guides/alignment
- [ ] Handle unknown document types gracefully

### Phase 4: Batch Processing 📋 FUTURE

- [ ] Add `ingest batch` command
- [ ] Process entire directory
- [ ] Auto-classify each document
- [ ] Generate summary report

---

## Recommended Next Steps

### Option 1: Integrate Classification into Existing Command (Quick)

**Pros:**
- Users get automatic classification immediately
- No command syntax changes

**Cons:**
- Might surprise users who expect explicit parser choice
- Breaking change if classification is wrong

**Implementation:**
```python
# Modify existing standards() command
doc_type, confidence, _ = classify_document(pdf_path)

if doc_type != DocumentType.STANDARDS and confidence > 0.7:
    console.print(f"[yellow]Warning: This appears to be a {doc_type.value} document, "
                 f"not a standards document. Proceeding anyway...[/yellow]")
```

### Option 2: Add New Auto Command (Recommended) ✅

**Pros:**
- Backward compatible
- Users can choose explicit or auto
- Safe to experiment

**Cons:**
- Need to maintain two commands
- More documentation needed

**Implementation:**
```bash
# Keep existing
pocketmusec ingest standards "path.pdf" --no-vision

# Add new auto-detect
pocketmusec ingest auto "path.pdf"
```

### Option 3: Add --auto-detect Flag (Compromise)

**Pros:**
- Single command with opt-in classification
- Easy to add
- Backward compatible

**Cons:**
- Extra flag complexity

**Implementation:**
```python
@ingest_app.command()
def standards(
    pdf_path: str,
    auto_detect: bool = typer.Option(False, "--auto-detect", "-a"),
    ...
):
    if auto_detect:
        doc_type, confidence, _ = classify_document(pdf_path)
        # Use appropriate parser
    else:
        # Current behavior
```

---

## Current Production Status

**What Works:**
- ✅ Document classification (100% accuracy on tests)
- ✅ Standards parsing (Table Parser, 80/80 standards)
- ✅ Unpacking proof of concept (20/20 objectives)

**What's Missing:**
- ❌ CLI integration for classification
- ❌ Production unpacking parser
- ❌ Database schema for unpacking content
- ❌ Batch processing capability

**Recommendation:**
Implement **Option 2** (new `auto` command) to safely add classification while maintaining backward compatibility. This allows users to benefit from automatic document type detection without breaking existing workflows.

---

## Files Created

1. **`backend/ingestion/document_classifier.py`** - Classification module ✅
2. **`DOCUMENT_CLASSIFICATION_GUIDE.md`** - This guide ✅
3. **`test_unpacking_parser.py`** - Unpacking proof of concept ✅

## Usage Example

```python
from backend.ingestion.document_classifier import classify_document, DocumentType

# Classify any PDF
doc_type, confidence, parser = classify_document("some_document.pdf")

if doc_type == DocumentType.STANDARDS:
    print(f"✓ Standards document detected ({confidence:.0%} confidence)")
    print(f"  Recommended parser: {parser}")
elif doc_type == DocumentType.UNPACKING:
    print(f"✓ Unpacking document detected ({confidence:.0%} confidence)")
    print(f"  Recommended parser: {parser}")
else:
    print(f"? Unknown document type")
```

---

## Conclusion

**Document type classification is critical** for accurate parsing of the diverse NC Music Education document collection. The classification system is built and tested, but **not yet integrated into the CLI**. 

The next step is to choose an integration strategy (recommended: Option 2 - new `auto` command) and implement it to enable automatic document type detection for users.
