#!/usr/bin/env python3
"""
Master PDF Processor - SLOW/RELIABLE Version
Lower concurrency (3 requests) with batched pages (2 pages per request)
For use when API is experiencing high load
"""

import asyncio
import aiohttp
import base64
import time
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import random
import json

# API Configuration
API_KEY = "cpk_b2a69dce82614c318761393792d24224.0c430c6531c953c9a169289fa1ebefdc.72nYsSozwc3lGPVLkmuLoZfrI0nhVhZ9"
ENDPOINT = "https://llm.chutes.ai/v1/chat/completions"
MODEL = "Qwen/Qwen3-VL-235B-A22B-Thinking"

# Processing Configuration - REDUCED for reliability
CONCURRENCY = 3  # Much lower concurrent requests
MAX_RETRIES = 5  # More retries
TIMEOUT = 300    # Longer timeout
PAGES_PER_REQUEST = 2  # Batch pages together
MAX_TOKENS = 16000  # Higher for multi-page
TEMPERATURE = 0.1
DPI = 150


class PDFProcessorSlow:
    """Process a single PDF through the complete pipeline - SLOW mode"""
    
    def __init__(self, pdf_path: Path, output_dir: Path):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.book_name = pdf_path.stem
        self.total_pages = 0
        
        # Create directory structure
        self.extracted_dir = output_dir / self.book_name / "extracted"
        self.png_dir = self.extracted_dir / "pages_png"
        self.md_dir = self.extracted_dir / "pages_md"
        
        for dir_path in [self.extracted_dir, self.png_dir, self.md_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_page_count(self) -> int:
        """Get total pages from PDF"""
        try:
            result = subprocess.run(
                ["pdfinfo", str(self.pdf_path)],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.split('\n'):
                if line.startswith('Pages:'):
                    return int(line.split(':')[1].strip())
        except Exception as e:
            print(f"❌ Error getting page count: {e}")
            return 0
    
    def convert_pdf_to_pngs(self) -> bool:
        """Convert PDF to PNG images"""
        print(f"\n📄 Converting PDF to PNGs...")
        print(f"   PDF: {self.pdf_path.name}")
        print(f"   Output: {self.png_dir}")
        
        # Skip if already done
        existing_pngs = len(list(self.png_dir.glob("page-*.png")))
        if existing_pngs > 0:
            print(f"✅ Found {existing_pngs} existing PNGs, skipping conversion")
            self.total_pages = existing_pngs
            return True
        
        try:
            cmd = [
                "convert",
                "-density", str(DPI),
                "-quality", "100",
                str(self.pdf_path),
                str(self.png_dir / "page-%04d.png")
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode != 0:
                print(f"❌ Conversion failed: {result.stderr}")
                return False
            
            png_count = len(list(self.png_dir.glob("page-*.png")))
            print(f"✅ Created {png_count} PNG files")
            self.total_pages = png_count
            return True
            
        except Exception as e:
            print(f"❌ Error during conversion: {e}")
            return False
    
    async def extract_page_batch(
        self, 
        session: aiohttp.ClientSession, 
        page_nums: List[int], 
        semaphore: asyncio.Semaphore
    ) -> Dict:
        """Extract text from a batch of pages (1-2 pages)"""
        async with semaphore:
            start = time.time()
            
            for attempt in range(MAX_RETRIES):
                try:
                    # Load PNGs
                    images_b64 = []
                    for page_num in page_nums:
                        png_path = self.png_dir / f"page-{page_num:04d}.png"
                        if not png_path.exists():
                            print(f"❌ Page {page_num:04d} | PNG not found", flush=True)
                            continue
                        
                        with open(png_path, "rb") as f:
                            img_b64 = base64.b64encode(f.read()).decode("utf-8")
                            images_b64.append((page_num, img_b64))
                    
                    if not images_b64:
                        return {"pages": page_nums, "success": False}
                    
                    # Build API request
                    num_pages = len(images_b64)
                    if num_pages == 1:
                        text_prompt = "Extract ALL text from this page. Format as clean markdown. Only return the extracted markdown text, no commentary."
                    else:
                        text_prompt = f"Extract ALL text from these {num_pages} pages. For each page, format as clean markdown. Separate pages with '---PAGE BREAK---'. Only return the extracted markdown text, no commentary."
                    
                    content = [{"type": "text", "text": text_prompt}]
                    
                    for page_num, img_b64 in images_b64:
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                        })
                    
                    payload = {
                        "model": MODEL,
                        "messages": [{"role": "user", "content": content}],
                        "max_tokens": MAX_TOKENS,
                        "temperature": TEMPERATURE
                    }
                    
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {API_KEY}"
                    }
                    
                    async with session.post(
                        ENDPOINT,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=TIMEOUT)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            text = result["choices"][0]["message"].get("content", "")
                            tokens = result.get("usage", {}).get("total_tokens", 0)
                            elapsed = time.time() - start
                            
                            # Split text if multiple pages
                            if num_pages > 1 and '---PAGE BREAK---' in text:
                                page_texts = text.split('---PAGE BREAK---')
                            else:
                                page_texts = [text]
                            
                            # Save each page
                            for i, (page_num, _) in enumerate(images_b64):
                                page_text = page_texts[i] if i < len(page_texts) else page_texts[0]
                                output = self.md_dir / f"page-{page_num:04d}.md"
                                output.write_text(page_text.strip(), encoding="utf-8")
                            
                            pages_str = ','.join([f"{p:04d}" for p, _ in images_b64])
                            print(f"✅ Pages {pages_str:15s} | {elapsed:5.1f}s | {tokens:5d} tokens", flush=True)
                            
                            return {
                                "pages": page_nums,
                                "success": True,
                                "tokens": tokens,
                                "time": elapsed
                            }
                        
                        elif response.status in [429, 503]:
                            # Rate limited or service unavailable
                            if attempt < MAX_RETRIES - 1:
                                wait_time = (3 ** attempt) + random.uniform(1, 3)  # Longer backoff
                                pages_str = ','.join([f"{p:04d}" for p in page_nums])
                                print(f"⏳ Pages {pages_str:15s} | HTTP {response.status}, waiting {wait_time:.1f}s (attempt {attempt+1}/{MAX_RETRIES})", flush=True)
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                pages_str = ','.join([f"{p:04d}" for p in page_nums])
                                print(f"❌ Pages {pages_str:15s} | Failed after {MAX_RETRIES} attempts", flush=True)
                                return {"pages": page_nums, "success": False}
                        else:
                            error_text = await response.text()
                            pages_str = ','.join([f"{p:04d}" for p in page_nums])
                            print(f"❌ Pages {pages_str:15s} | HTTP {response.status}", flush=True)
                            return {"pages": page_nums, "success": False}
                
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        wait_time = (3 ** attempt) + random.uniform(1, 3)
                        pages_str = ','.join([f"{p:04d}" for p in page_nums])
                        print(f"⏳ Pages {pages_str:15s} | Error, retrying in {wait_time:.1f}s", flush=True)
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        pages_str = ','.join([f"{p:04d}" for p in page_nums])
                        print(f"❌ Pages {pages_str:15s} | Failed after {MAX_RETRIES} attempts", flush=True)
                        return {"pages": page_nums, "success": False}
    
    async def extract_all_pages(self) -> Dict:
        """Extract text from all PNG pages"""
        print(f"\n📝 Extracting text from {self.total_pages} pages...")
        print(f"   Concurrency: {CONCURRENCY} requests (SLOW mode)")
        print(f"   Pages per request: {PAGES_PER_REQUEST}")
        print(f"   Model: {MODEL}")
        print()
        
        # Check which pages already exist
        existing_pages = set()
        for md_file in self.md_dir.glob("page-*.md"):
            # Skip files with errors
            content = md_file.read_text(encoding="utf-8")
            if not content.startswith("[Error") and len(content) > 50:
                page_num = int(md_file.stem.split('-')[1])
                existing_pages.add(page_num)
        
        # Group pages into batches
        page_batches = []
        all_pages = list(range(self.total_pages))
        
        # Filter out existing pages
        pages_to_process = [p for p in all_pages if p not in existing_pages]
        
        if not pages_to_process:
            print("✅ All pages already extracted!")
            return {
                "total_pages": self.total_pages,
                "successful": self.total_pages,
                "failed": 0,
                "total_time": 0,
                "total_tokens": 0,
                "cost": 0
            }
        
        print(f"   Found {len(existing_pages)} already extracted, processing {len(pages_to_process)} remaining")
        print()
        
        for i in range(0, len(pages_to_process), PAGES_PER_REQUEST):
            batch = pages_to_process[i:i+PAGES_PER_REQUEST]
            page_batches.append(batch)
        
        semaphore = asyncio.Semaphore(CONCURRENCY)
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.extract_page_batch(session, batch, semaphore)
                for batch in page_batches
            ]
            results = await asyncio.gather(*tasks)
        
        # Calculate statistics
        total_time = time.time() - start_time
        successful_batches = sum(1 for r in results if r.get("success", False))
        failed_batches = len(results) - successful_batches
        total_tokens = sum(r.get("tokens", 0) for r in results if r.get("success", False))
        
        # Count actual successful pages
        successful_pages = len(existing_pages)
        for r in results:
            if r.get("success", False):
                successful_pages += len(r.get("pages", []))
        
        stats = {
            "total_pages": self.total_pages,
            "successful": successful_pages,
            "failed": self.total_pages - successful_pages,
            "total_time": total_time,
            "total_tokens": total_tokens,
            "cost": (total_tokens / 1000) * 0.015
        }
        
        print()
        print("=" * 70)
        print(f"✨ Extraction Complete!")
        print(f"   Success: {successful_pages}/{self.total_pages} pages ({successful_pages*100//self.total_pages}%)")
        print(f"   Failed: {self.total_pages - successful_pages} pages")
        print(f"   Time: {total_time/60:.1f} minutes")
        print(f"   Tokens: {total_tokens:,}")
        if total_time > 0:
            print(f"   Rate: {len(pages_to_process)/total_time*60:.1f} pages/minute")
        print(f"   Cost: ${stats['cost']:.2f}")
        print("=" * 70)
        
        return stats
    
    def remove_watermarks(self):
        """Remove common watermarks from extracted files"""
        print(f"\n🧹 Removing watermarks...")
        
        watermark_patterns = [
            r'\[?OceanofPDF\.com\]?',
            r'https?://OceanofPDF\.com',
        ]
        
        cleaned_count = 0
        
        for md_file in self.md_dir.glob("page-*.md"):
            content = md_file.read_text(encoding="utf-8")
            original = content
            
            for pattern in watermark_patterns:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)
            
            if content != original:
                md_file.write_text(content, encoding="utf-8")
                cleaned_count += 1
        
        print(f"✅ Cleaned {cleaned_count} files")
    
    def create_complete_book(self):
        """Combine all pages into a single complete book file"""
        print(f"\n📖 Creating complete book file...")
        
        output_file = self.extracted_dir / f"{self.book_name}_COMPLETE.md"
        
        content = []
        content.append(f"# {self.book_name.replace('_', ' ')}\n\n")
        content.append("**Complete Edition**\n\n")
        content.append("Extracted using Qwen Vision Model\n\n")
        content.append("---\n\n")
        
        page_count = 0
        for page_num in range(self.total_pages):
            page_file = self.md_dir / f"page-{page_num:04d}.md"
            
            if page_file.exists():
                page_content = page_file.read_text(encoding="utf-8")
                # Skip error pages
                if not page_content.startswith("[Error"):
                    content.append(f"<!-- Page {page_num} -->\n\n")
                    content.append(page_content)
                    content.append("\n\n---\n\n")
                    page_count += 1
        
        final_content = ''.join(content)
        output_file.write_text(final_content, encoding="utf-8")
        
        file_size = output_file.stat().st_size
        word_count = len(final_content.split())
        
        print(f"✅ Created: {output_file.name}")
        print(f"   Size: {file_size/1024/1024:.2f} MB")
        print(f"   Words: {word_count:,}")
        print(f"   Pages: {page_count}")
    
    def create_continuous_version(self):
        """Create continuous reading version without page markers"""
        print(f"\n📚 Creating continuous reading version...")
        
        complete_file = self.extracted_dir / f"{self.book_name}_COMPLETE.md"
        continuous_file = self.extracted_dir / f"{self.book_name}_CONTINUOUS.md"
        
        if not complete_file.exists():
            print("⚠️  Complete file not found, skipping")
            return
        
        content = complete_file.read_text(encoding="utf-8")
        
        # Remove page markers
        content = re.sub(r'<!-- Page \d+ -->\n*', '', content)
        content = re.sub(r'\n---\n\n', '\n\n', content)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        continuous_file.write_text(content, encoding="utf-8")
        
        file_size = continuous_file.stat().st_size
        word_count = len(content.split())
        
        print(f"✅ Created: {continuous_file.name}")
        print(f"   Size: {file_size/1024/1024:.2f} MB")
        print(f"   Words: {word_count:,}")
    
    def create_summary(self, stats: Dict):
        """Create a processing summary document"""
        summary_file = self.extracted_dir / "PROCESSING_SUMMARY.md"
        
        summary = f"""# {self.book_name.replace('_', ' ')} - Processing Summary

## Extraction Results

**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**PDF**: {self.pdf_path.name}
**Total Pages**: {self.total_pages}
**Mode**: SLOW (Concurrency: {CONCURRENCY}, Pages per request: {PAGES_PER_REQUEST})

## Statistics

- **Successfully Extracted**: {stats['successful']} / {stats['total_pages']} pages ({stats['successful']*100//stats['total_pages']}%)
- **Failed Pages**: {stats['failed']}
- **Processing Time**: {stats['total_time']/60:.1f} minutes
- **Total Tokens**: {stats['total_tokens']:,}
- **Processing Rate**: {stats['total_pages']/stats['total_time']*60 if stats['total_time'] > 0 else 0:.1f} pages/minute
- **Estimated Cost**: ${stats['cost']:.2f}

## Configuration

- **Model**: {MODEL}
- **API**: Chutes.ai
- **Concurrency**: {CONCURRENCY} requests (SLOW mode)
- **Pages per Request**: {PAGES_PER_REQUEST}
- **Max Retries**: {MAX_RETRIES}
- **Timeout**: {TIMEOUT}s per request
- **Resolution**: {DPI} DPI

## Output Files

- **Complete Book**: `{self.book_name}_COMPLETE.md`
- **Continuous Version**: `{self.book_name}_CONTINUOUS.md`
- **Individual Pages**: `pages_md/page-XXXX.md` ({self.total_pages} files)
- **Source Images**: `pages_png/page-XXXX.png` ({self.total_pages} files)

## Status

{"✅ All pages successfully extracted!" if stats['failed'] == 0 else f"⚠️  {stats['failed']} pages failed extraction"}
"""
        
        summary_file.write_text(summary, encoding="utf-8")
        print(f"\n📋 Summary saved to: PROCESSING_SUMMARY.md")
    
    async def process(self):
        """Run the complete processing pipeline"""
        print("=" * 70)
        print(f"🚀 Processing: {self.book_name} (SLOW MODE)")
        print("=" * 70)
        
        # Step 1: Get page count
        self.total_pages = self.get_page_count()
        if self.total_pages == 0:
            print("❌ Could not determine page count")
            return False
        
        print(f"📊 Total pages: {self.total_pages}")
        
        # Step 2: Convert PDF to PNGs
        if not self.convert_pdf_to_pngs():
            return False
        
        # Step 3: Extract text from all pages
        stats = await self.extract_all_pages()
        
        # Step 4: Clean up watermarks
        self.remove_watermarks()
        
        # Step 5: Create complete book
        self.create_complete_book()
        
        # Step 6: Create continuous version
        self.create_continuous_version()
        
        # Step 7: Create summary
        self.create_summary(stats)
        
        print("\n" + "=" * 70)
        print("🎉 PROCESSING COMPLETE!")
        print("=" * 70)
        print(f"\n📁 Output directory: {self.extracted_dir}")
        
        return True


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python master_pdf_processor_slow.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        sys.exit(1)
    
    output_dir = pdf_path.parent
    
    processor = PDFProcessorSlow(pdf_path, output_dir)
    success = await processor.process()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
