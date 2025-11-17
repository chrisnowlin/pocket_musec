#!/usr/bin/env python3
"""
Batch process all PDFs in the directory
"""

import asyncio
import sys
from pathlib import Path
from master_pdf_processor import PDFProcessor
import time


async def process_all_pdfs(pdf_dir: Path):
    """Process all PDFs in the directory"""
    
    # Find all PDFs
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    
    # Filter out already processed ones
    to_process = []
    for pdf in pdfs:
        extracted_dir = pdf_dir / pdf.stem / "extracted"
        summary_file = extracted_dir / "PROCESSING_SUMMARY.md"
        
        if summary_file.exists():
            print(f"⏭️  Skipping (already processed): {pdf.name}")
        else:
            to_process.append(pdf)
    
    if not to_process:
        print("\n✅ All PDFs already processed!")
        return
    
    print(f"\n📚 Found {len(to_process)} PDFs to process:")
    for i, pdf in enumerate(to_process, 1):
        print(f"   {i}. {pdf.name}")
    
    print("\n" + "=" * 70)
    
    total_start = time.time()
    results = []
    
    for i, pdf in enumerate(to_process, 1):
        print(f"\n📖 Processing {i}/{len(to_process)}: {pdf.name}")
        print("=" * 70)
        
        processor = PDFProcessor(pdf, pdf_dir)
        success = await processor.process()
        
        results.append({
            "pdf": pdf.name,
            "success": success
        })
        
        # Brief pause between PDFs to avoid overwhelming the API
        if i < len(to_process):
            print("\n⏸️  Pausing 10 seconds before next PDF...")
            await asyncio.sleep(10)
    
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
    print(f"   Total time: {total_time/60:.1f} minutes")
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
