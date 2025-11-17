#!/usr/bin/env python3
"""
Master PDF Processor - Automated pipeline for extracting PDFs to markdown
Handles: PDF→PNG→Markdown→Organization→Cleanup
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

# Processing Configuration
CONCURRENCY = 10  # Concurrent API requests
MAX_RETRIES = 3
TIMEOUT = 180
MAX_TOKENS = 8000
TEMPERATURE = 0.1
DPI = 150  # PNG resolution


class PDFProcessor:
    """Process a single PDF through the complete pipeline"""
    
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
        
        try:
            # Use ImageMagick convert
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
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                print(f"❌ Conversion failed: {result.stderr}")
                return False
            
            # Count created PNGs
            png_count = len(list(self.png_dir.glob("page-*.png")))
            print(f"✅ Created {png_count} PNG files")
            self.total_pages = png_count
            return True
            
        except Exception as e:
            print(f"❌ Error during conversion: {e}")
            return False
    
    async def extract_single_page(
        self, 
        session: aiohttp.ClientSession, 
        page_num: int, 
        semaphore: asyncio.Semaphore
    ) -> Dict:
        """Extract text from a single PNG page"""
        async with semaphore:
            start = time.time()
            
            for attempt in range(MAX_RETRIES):
                try:
                    # Load PNG
                    png_path = self.png_dir / f"page-{page_num:04d}.png"
                    if not png_path.exists():
                        print(f"❌ Page {page_num:04d} | PNG not found", flush=True)
                        return {"page": page_num, "success": False}
                    
                    with open(png_path, "rb") as f:
                        img_b64 = base64.b64encode(f.read()).decode("utf-8")
                    
                    # Build API request
                    content = [
                        {
                            "type": "text",
                            "text": "Extract ALL text from this page. Format as clean markdown. Only return the extracted markdown text, no commentary."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                        }
                    ]
                    
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
                            
                            # Save page
                            output = self.md_dir / f"page-{page_num:04d}.md"
                            output.write_text(text.strip(), encoding="utf-8")
                            
                            print(f"✅ Page {page_num:04d} | {elapsed:5.1f}s | {tokens:5d} tokens", flush=True)
                            
                            return {
                                "page": page_num,
                                "success": True,
                                "tokens": tokens,
                                "time": elapsed
                            }
                        
                        elif response.status == 429:
                            # Rate limited - retry with backoff
                            if attempt < MAX_RETRIES - 1:
                                wait_time = (2 ** attempt) + random.uniform(0, 1)
                                print(f"⏳ Page {page_num:04d} | Rate limited, waiting {wait_time:.1f}s", flush=True)
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                print(f"❌ Page {page_num:04d} | Rate limited after {MAX_RETRIES} attempts", flush=True)
                                return {"page": page_num, "success": False}
                        else:
                            error_text = await response.text()
                            print(f"❌ Page {page_num:04d} | HTTP {response.status}", flush=True)
                            return {"page": page_num, "success": False}
                
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        print(f"⏳ Page {page_num:04d} | Error, retrying in {wait_time:.1f}s", flush=True)
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ Page {page_num:04d} | Failed after {MAX_RETRIES} attempts", flush=True)
                        return {"page": page_num, "success": False}
    
    async def extract_all_pages(self) -> Dict:
        """Extract text from all PNG pages"""
        print(f"\n📝 Extracting text from {self.total_pages} pages...")
        print(f"   Concurrency: {CONCURRENCY} requests")
        print(f"   Model: {MODEL}")
        print()
        
        semaphore = asyncio.Semaphore(CONCURRENCY)
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.extract_single_page(session, page_num, semaphore)
                for page_num in range(self.total_pages)
            ]
            results = await asyncio.gather(*tasks)
        
        # Calculate statistics
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.get("success", False))
        failed = len(results) - successful
        total_tokens = sum(r.get("tokens", 0) for r in results if r.get("success", False))
        
        stats = {
            "total_pages": self.total_pages,
            "successful": successful,
            "failed": failed,
            "total_time": total_time,
            "total_tokens": total_tokens,
            "cost": (total_tokens / 1000) * 0.015
        }
        
        print()
        print("=" * 70)
        print(f"✨ Extraction Complete!")
        print(f"   Success: {successful}/{self.total_pages} pages ({successful*100//self.total_pages}%)")
        print(f"   Failed: {failed} pages")
        print(f"   Time: {total_time/60:.1f} minutes")
        print(f"   Tokens: {total_tokens:,}")
        print(f"   Rate: {self.total_pages/total_time*60:.1f} pages/minute")
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
            
            # Remove lines that only contain watermarks
            lines = content.split('\n')
            cleaned_lines = [line for line in lines if not re.match(r'^\s*$', line) or line == '']
            content = '\n'.join(cleaned_lines)
            
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
        
        # Remove horizontal separators between pages
        content = re.sub(r'\n---\n\n', '\n\n', content)
        
        # Remove excessive blank lines
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

## Statistics

- **Successfully Extracted**: {stats['successful']} / {stats['total_pages']} pages ({stats['successful']*100//stats['total_pages']}%)
- **Failed Pages**: {stats['failed']}
- **Processing Time**: {stats['total_time']/60:.1f} minutes
- **Total Tokens**: {stats['total_tokens']:,}
- **Processing Rate**: {stats['total_pages']/stats['total_time']*60:.1f} pages/minute
- **Estimated Cost**: ${stats['cost']:.2f}

## Configuration

- **Model**: {MODEL}
- **API**: Chutes.ai
- **Concurrency**: {CONCURRENCY} requests
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
        print(f"🚀 Processing: {self.book_name}")
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
        print("Usage: python master_pdf_processor.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        sys.exit(1)
    
    output_dir = pdf_path.parent
    
    processor = PDFProcessor(pdf_path, output_dir)
    success = await processor.process()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
