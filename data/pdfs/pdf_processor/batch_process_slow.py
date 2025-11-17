#!/usr/bin/env python3
"""
Batch process all PDFs using SLOW/RELIABLE mode
Lower concurrency, batched pages, more retries
"""

import asyncio
import sys
from pathlib import Path
from master_pdf_processor_slow import PDFProcessorSlow
import time


async def process_all_pdfs(pdf_dir: Path):
    """Process all PDFs in the directory using SLOW mode"""
    
    # Find all PDFs
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    
    # Filter out already processed ones
    to_process = []
    for pdf in pdfs:
        extracted_dir = pdf_dir / pdf.stem / "extracted"
        summary_file = extracted_dir / "PROCESSING_SUMMARY.md"
        
        # Check if already fully processed
        if summary_file.exists():
            content = summary_file.read_text()
            if "100%" in content or "All pages successfully extracted" in content:
                print(f"⏭️  Skipping (100% complete): {pdf.name}")
                continue
        
        to_process.append(pdf)
    
    if not to_process:
        print("\n✅ All PDFs already processed!")
        return
    
    print(f"\n📚 Found {len(to_process)} PDFs to process (SLOW MODE):")
    for i, pdf in enumerate(to_process, 1):
        print(f"   {i}. {pdf.name}")
    
    print("\n🐢 SLOW MODE Configuration:")
    print("   - Concurrency: 3 requests (vs 10 in fast mode)")
    print("   - Pages per request: 2 (batching for efficiency)")
    print("   - Max retries: 5 (vs 3 in fast mode)")
    print("   - Longer backoff times")
    print("   - More conservative and reliable")
    
    print("\n" + "=" * 70)
    
    total_start = time.time()
    results = []
    
    for i, pdf in enumerate(to_process, 1):
        print(f"\n📖 Processing {i}/{len(to_process)}: {pdf.name}")
        print("=" * 70)
        
        processor = PDFProcessorSlow(pdf, pdf_dir)
        success = await processor.process()
        
        results.append({
            "pdf": pdf.name,
            "success": success
        })
        
        # Longer pause between PDFs
        if i < len(to_process):
            wait_time = 30  # 30 seconds between PDFs
            print(f"\n⏸️  Pausing {wait_time} seconds before next PDF...")
            await asyncio.sleep(wait_time)
    
    # Final summary
    total_time = time.time() - total_start
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print("\n" + "=" * 70)
    print("🎉 BATCH PROCESSING COMPLETE!")
    print("=" * 70)
    print(f"\n📊 Summary:")
    print(f"   Total PDFs: {len(results)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Total time: {total_time/60:.1f} minutes ({total_time/3600:.1f} hours)")
    print()
    
    if successful > 0:
        print("✅ Successfully processed:")
        for r in results:
            if r["success"]:
                print(f"   - {r['pdf']}")
    
    if failed > 0:
        print("\n❌ Failed:")
        for r in results:
            if not r["success"]:
                print(f"   - {r['pdf']}")


if __name__ == "__main__":
    pdf_dir = Path("/Users/cnowlin/Developer/pocket_musec/data/pdfs")
    asyncio.run(process_all_pdfs(pdf_dir))
