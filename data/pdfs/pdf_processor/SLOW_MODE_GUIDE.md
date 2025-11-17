# Slow Mode Processing Guide

## Overview

The **SLOW mode** processor is designed for reliability when the API is experiencing high load or service issues.

## Differences from Fast Mode

| Feature | Fast Mode | Slow Mode |
|---------|-----------|-----------|
| **Concurrency** | 10 requests | 3 requests |
| **Pages per Request** | 1 page | 2 pages |
| **Max Retries** | 3 attempts | 5 attempts |
| **Timeout** | 180s | 300s (5 min) |
| **Backoff** | 2^n seconds | 3^n seconds |
| **Pause Between PDFs** | 10s | 30s |

## When to Use Slow Mode

Use SLOW mode when:
- ✅ Getting HTTP 503 errors (service unavailable)
- ✅ Experiencing frequent failures
- ✅ API is under heavy load
- ✅ Want maximum reliability over speed

Use FAST mode when:
- ✅ API is responsive
- ✅ No service errors
- ✅ Want faster processing

## Usage

### Process Single PDF (Slow Mode)
```bash
cd /Users/cnowlin/Developer/pocket_musec/data/pdfs/pdf_processor
python3 master_pdf_processor_slow.py "../Book_Name.pdf"
```

### Process All PDFs (Slow Mode)
```bash
cd /Users/cnowlin/Developer/pocket_musec/data/pdfs/pdf_processor
python3 batch_process_slow.py
```

## Performance

**Estimated Rates**:
- Fast mode: ~7-10 pages/minute
- Slow mode: ~4-6 pages/minute

**Reliability**:
- Fast mode: Good when API is healthy
- Slow mode: Excellent even under high API load

## Key Features

### 1. Lower Concurrency (3 vs 10)
- Puts less load on the API
- Reduces chance of rate limiting
- More reliable during high API usage

### 2. Batched Pages (2 per request)
- More efficient than 1 page per request
- Reduces total API calls by 50%
- Lower cost per page
- Better throughput despite lower concurrency

### 3. More Retries (5 vs 3)
- Gives API more time to recover
- Exponential backoff: 3^n vs 2^n
- Longer wait times between retries
- Higher success rate on transient errors

### 4. Resume Capability
Both scripts automatically:
- Skip already extracted pages
- Resume from failures
- Can be run multiple times safely

## Cost Comparison

**Fast Mode**:
- ~$0.04-0.07 per page (single page requests)
- Faster but potentially more retries

**Slow Mode**:
- ~$0.03-0.05 per page (batched requests)
- Slightly cheaper due to batching
- Fewer retries needed

## Current Status

After API service issues, we need SLOW mode to complete:

1. **Better Than Carrots or Sticks** - 95/170 pages remaining
2. **Classroom Music Games** - 96/96 pages remaining
3. **From Lesson Plans to Power Struggles** - 228/228 pages remaining
4. **Hacking Classroom Management** - 161 pages
5. **Mindsets in the Classroom** - 153 pages
6. **School Discipline & Management** - 390 pages
7. **The Classroom Behavior Manual** - 290 pages
8. **What's Your Procedure For That?** - 136 pages

**Total Remaining**: 1,549 pages

**Estimated Time (Slow Mode)**: 
- At 5 pages/minute: ~310 minutes (~5.2 hours)
- With pauses: ~6-7 hours total

**Estimated Cost**: ~$70-80

## Running the Slow Mode Batch

```bash
cd /Users/cnowlin/Developer/pocket_musec/data/pdfs/pdf_processor
python3 batch_process_slow.py
```

The script will:
1. ✅ Find all PDFs needing processing
2. ✅ Skip already completed PDFs
3. ✅ Process remaining pages from partial PDFs
4. ✅ Use 3 concurrent requests with 2 pages each
5. ✅ Retry up to 5 times with exponential backoff
6. ✅ Wait 30 seconds between PDFs
7. ✅ Generate complete and continuous versions
8. ✅ Provide detailed progress tracking

## Monitoring Progress

While running, you'll see:
```
✅ Pages 0001,0002      |  45.3s |  6234 tokens
✅ Pages 0003,0004      |  52.1s |  6891 tokens
⏳ Pages 0005,0006      | HTTP 503, waiting 9.2s (attempt 2/5)
✅ Pages 0005,0006      |  61.4s |  7123 tokens
```

## After Completion

Check results:
```bash
# View summary
cat "Book_Name/extracted/PROCESSING_SUMMARY.md"

# Check for errors
grep -r "Error on page" "Book_Name/extracted/pages_md/"

# Verify completeness
ls "Book_Name/extracted/pages_md/" | wc -l
```

---

**Recommendation**: Use slow mode for current batch due to previous API service issues. This will maximize success rate while still processing efficiently through batching.
