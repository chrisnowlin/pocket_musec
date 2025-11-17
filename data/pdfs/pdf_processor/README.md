# PDF Processor - Automated PDF to Markdown Pipeline

## Overview

Automated system for extracting text from PDFs using vision AI and converting to searchable markdown.

**Technology**: Qwen Vision Model via Chutes.ai API

## Features

✅ **Complete Pipeline**
- PDF → PNG conversion (150 DPI)
- PNG → Markdown extraction (via Qwen Vision AI)
- Automatic retry with exponential backoff
- Watermark removal (OceanofPDF, etc.)
- Multiple output formats

✅ **Robust Processing**
- 10 concurrent requests (optimized for API rate limits)
- 3 retry attempts per page with exponential backoff
- Automatic error tracking and reporting
- Resume capability (skips already processed files)

✅ **Output Formats**
- Individual page files (page-XXXX.md)
- Complete book with page markers
- Continuous reading version (no markers)
- Processing summary with statistics

## Requirements

### Software
```bash
# Python 3.8+
python3 --version

# ImageMagick (for PDF → PNG conversion)
convert --version

# pdfinfo (for page counting)
pdfinfo --version
```

### Python Dependencies
```bash
pip install aiohttp asyncio
```

### API Key
Chutes.ai API key configured in `master_pdf_processor.py`

## Usage

### Process Single PDF
```bash
python3 master_pdf_processor.py path/to/book.pdf
```

### Process All PDFs in Directory
```bash
python3 batch_process_all.py
```

The batch processor will:
- Find all PDFs in `/Users/cnowlin/Developer/pocket_musec/data/pdfs/`
- Skip already processed PDFs
- Process remaining PDFs sequentially
- Provide comprehensive summary at the end

## Output Structure

For each PDF, creates:

```
Book_Name/
└── extracted/
    ├── Book_Name_COMPLETE.md          ← Complete book with page markers
    ├── Book_Name_CONTINUOUS.md        ← Continuous reading version
    ├── PROCESSING_SUMMARY.md          ← Statistics and metadata
    ├── pages_md/                      ← Individual page markdown files
    │   ├── page-0000.md
    │   ├── page-0001.md
    │   └── ...
    └── pages_png/                     ← Source PNG images
        ├── page-0000.png
        ├── page-0001.png
        └── ...
```

## Performance

**Test Results** (Holistic Musical Thinking - 32 pages):
- Success rate: 100%
- Processing time: 4.5 minutes
- Rate: 7.1 pages/minute
- Cost: $2.10

**Estimated for All PDFs** (~1,656 pages):
- Time: ~3.5 hours
- Cost: ~$70-80

## Configuration

Edit `master_pdf_processor.py` to adjust:

```python
# API Configuration
API_KEY = "your_api_key_here"
ENDPOINT = "https://llm.chutes.ai/v1/chat/completions"
MODEL = "Qwen/Qwen3-VL-235B-A22B-Thinking"

# Processing Configuration
CONCURRENCY = 10      # Concurrent API requests
MAX_RETRIES = 3       # Retry attempts per page
TIMEOUT = 180         # Seconds per request
MAX_TOKENS = 8000     # Max tokens per response
DPI = 150             # PNG resolution
```

## Error Handling

The script handles:
- **Rate limiting (429)**: Exponential backoff and retry
- **Network errors**: Automatic retry with backoff
- **Missing files**: Graceful error messages
- **API errors**: Logged and continued

Failed pages can be reprocessed by running the script again (it will only process missing/failed pages).

## Quality Verification

After processing, verify:
```bash
cd "Book_Name/extracted"

# Check for errors
grep -r "Error on page" pages_md/

# Check for watermarks
grep -ri "oceanofpdf" pages_md/

# View summary
cat PROCESSING_SUMMARY.md
```

## Cost Management

Approximate costs (at $0.015 per 1K tokens):
- Small book (50 pages): ~$3
- Medium book (150 pages): ~$10
- Large book (300 pages): ~$20
- Very large book (500+ pages): ~$35+

Average: ~$0.04-0.07 per page

## Troubleshooting

**PDF conversion fails**:
- Install ImageMagick: `brew install imagemagick`
- Check PDF permissions

**Rate limiting errors**:
- Reduce CONCURRENCY (try 5 instead of 10)
- Increase wait time between batches

**High failure rate**:
- Check API key validity
- Verify internet connection
- Try processing in smaller batches

**Missing pages**:
- Re-run the script (it will only process missing pages)
- Check `PROCESSING_SUMMARY.md` for statistics

## Development

Based on successful processing of "Teach Like a Champion" (893 pages):
- Optimized concurrency to avoid rate limits
- Implemented robust retry logic
- Added watermark removal
- Created multiple output formats

## Files

- `master_pdf_processor.py` - Main processing script
- `batch_process_all.py` - Batch processor for multiple PDFs
- `README.md` - This file

## License

For educational use with Pocket MUSEC project.
