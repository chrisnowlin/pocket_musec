# Teach Like a Champion 3.0 - Extracted Content

## Overview

Complete extraction of all 893 pages from "Teach Like a Champion 3.0" by Doug Lemov.

**Extraction Date**: November 16, 2025  
**Method**: Qwen Vision Model (Qwen3-VL-235B-A22B-Thinking)  
**Success Rate**: 100%  
**Quality**: High-fidelity text extraction with markdown formatting

---

## Available Files

### 📖 Complete Book (Single File)
**File**: `TEACH_LIKE_A_CHAMPION_COMPLETE.md`
- **Size**: 1.4 MB
- **Words**: 244,473
- **Lines**: 12,973
- **Format**: Single markdown file with all chapters
- **Use for**: Reading cover-to-cover, full-text search, conversion to other formats

### 📚 By Chapter (13 Files)
**Location**: `chapters/`

Individual chapter files for easier navigation:

1. `00_Front_Matter.md` (95 KB) - Title, TOC, Preface, Introduction
2. `01_Five_Themes.md` (96 KB) - Mental Models and Purposeful Execution
3. `02_Lesson_Preparation.md` (100 KB) - 5 techniques
4. `03_Check_for_Understanding.md` (164 KB) - 9 techniques ⭐ Largest
5. `04_Academic_Ethos.md` (124 KB) - 5 techniques
6. `05_Lesson_Structures.md` (130 KB) - 7 techniques
7. `06_Pacing.md` (73 KB) - 5 techniques
8. `07_Building_Ratio_Questioning.md` (155 KB) - 6 techniques
9. `08_Building_Ratio_Writing.md` (81 KB) - 5 techniques
10. `09_Building_Ratio_Discussion.md` (83 KB) - 4 techniques
11. `10_Procedures_and_Routines.md` (91 KB) - 5 techniques
12. `11_High_Behavioral_Expectations.md` (140 KB) - 10 techniques
13. `12_Building_Motivation_and_Trust.md` (108 KB) - Final chapter

**See**: `chapters/00_INDEX.md` for detailed chapter index

### 📄 Individual Pages (893 Files)
**Location**: `pages_md/`
- Files: `page-0000.md` through `page-0892.md`
- **Use for**: Granular access, page-specific references

### 🖼️ Source Images (893 Files)
**Location**: `pages_png/`
- Files: `page-0000.png` through `page-0892.png`
- Resolution: 150 DPI
- **Use for**: Original source verification, re-extraction if needed

---

## Usage Examples

### Search for a Technique
```bash
# Search in complete book
grep -n -i "cold call" TEACH_LIKE_A_CHAMPION_COMPLETE.md

# Search in specific chapter
grep -i "cold call" chapters/07_Building_Ratio_Questioning.md

# Search across all chapters
rg -i "cold call" chapters/
```

### Read a Chapter
```bash
# Using less
less chapters/03_Check_for_Understanding.md

# Using cat with pagination
cat chapters/05_Lesson_Structures.md | less
```

### Convert to Other Formats
```bash
# Convert complete book to PDF
pandoc TEACH_LIKE_A_CHAMPION_COMPLETE.md -o TeachLikeAChampion.pdf

# Convert single chapter to PDF
pandoc chapters/04_Academic_Ethos.md -o Academic_Ethos.pdf

# Convert to EPUB
pandoc TEACH_LIKE_A_CHAMPION_COMPLETE.md -o TeachLikeAChampion.epub

# Convert to Word
pandoc TEACH_LIKE_A_CHAMPION_COMPLETE.md -o TeachLikeAChampion.docx
```

### Extract Specific Content
```bash
# Find all technique names
rg "^### TECHNIQUE \d+:" chapters/

# Count techniques per chapter
for f in chapters/*.md; do 
    echo "$f: $(rg -c "^### TECHNIQUE" "$f" 2>/dev/null || echo 0)"; 
done

# Extract just the table of contents
head -100 pages_md/page-0001.md
```

---

## Content Structure

### The 62+ Techniques

The book covers 62+ teaching techniques organized by theme:

- **Chapter 2**: Lesson Preparation (5 techniques)
- **Chapter 3**: Check for Understanding (9 techniques)
- **Chapter 4**: Academic Ethos (5 techniques)
- **Chapter 5**: Lesson Structures (7 techniques)
- **Chapter 6**: Pacing (5 techniques)
- **Chapter 7**: Building Ratio - Questioning (6 techniques)
- **Chapter 8**: Building Ratio - Writing (5 techniques)
- **Chapter 9**: Building Ratio - Discussion (4 techniques)
- **Chapter 10**: Procedures and Routines (5 techniques)
- **Chapter 11**: High Behavioral Expectations (10 techniques)
- **Chapter 12**: Building Motivation and Trust

---

## Quality Notes

✅ **Verified Clean**
- All OceanofPDF.com references removed
- No piracy watermarks
- Clean, professional text

✅ **High Quality Extraction**
- Complete sentences and paragraphs
- Markdown formatting preserved
- Technical terms intact
- Structure maintained (headings, lists, emphasis)

✅ **Complete Coverage**
- All 893 pages extracted
- 0 pages with errors
- 100% success rate

---

## Technical Details

**Extraction Method**:
- Vision model: Qwen/Qwen3-VL-235B-A22B-Thinking
- API: Chutes.ai (https://llm.chutes.ai)
- Concurrency: 10 concurrent requests (optimal)
- Retry logic: Exponential backoff with 3 retries
- Processing time: ~2 hours total
- Cost: ~$75 (estimated)

**Token Usage**:
- Total tokens: ~2,500,000
- Average per page: ~2,800 tokens
- Max tokens per request: 8,000

---

## File Organization

```
extracted/
├── TEACH_LIKE_A_CHAMPION_COMPLETE.md    ← Complete book (1.4 MB)
├── README.md                             ← This file
├── EXTRACTION_COMPLETE.md                ← Detailed extraction report
├── chapters/                             ← 13 chapter files
│   ├── 00_INDEX.md                       ← Chapter index
│   ├── 00_Front_Matter.md
│   ├── 01_Five_Themes.md
│   ├── 02_Lesson_Preparation.md
│   └── ... (10 more chapters)
├── pages_md/                             ← 893 individual pages
│   ├── page-0000.md
│   ├── page-0001.md
│   └── ... (891 more pages)
└── pages_png/                            ← 893 source images
    ├── page-0000.png
    ├── page-0001.png
    └── ... (891 more images)
```

---

## Recommended Usage

**For Reading**:
- Use chapter files in `chapters/` directory
- Easier to navigate and reference specific topics

**For Searching**:
- Use `TEACH_LIKE_A_CHAMPION_COMPLETE.md`
- Single file makes searching faster and simpler

**For Reference**:
- Use individual pages in `pages_md/`
- Cite specific page numbers from original book

**For Conversion**:
- Use `TEACH_LIKE_A_CHAMPION_COMPLETE.md` for full book
- Use chapter files for section-by-section conversion

---

## Support Files

Additional documentation in `../png conversion/`:
- `EXTRACTION_SUMMARY.md` - Original extraction plan
- `REPROCESSING_PLAN.md` - Reprocessing approach
- `reprocess.log` - Detailed extraction log
- Scripts for extraction and processing

---

**Status**: ✅ Complete and ready to use!
