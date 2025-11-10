#!/usr/bin/env python3
"""Debug PDF block extraction"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.ingestion.pdf_parser import PDFReader

def debug_pdf_blocks():
    """Debug what blocks are extracted from PDF"""
    
    pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"
    
    print("=== Debugging PDF Block Extraction ===")
    reader = PDFReader()
    
    try:
        pages = reader.read_pdf(pdf_path)
        print(f"Read {len(pages)} pages")
        
        # Show first page blocks
        if pages:
            page = pages[0]
            print(f"Page {page.page_number} has {len(page.text_blocks)} blocks")
            
            # Show first 20 blocks
            for i, block in enumerate(page.text_blocks[:20]):
                print(f"  {i+1:2d}. [{block.x0:.1f},{block.y0:.1f}] {block.text.strip()}")
                
            # Look for standards patterns
            print("\n=== Looking for Standard Patterns ===")
            import re
            standard_pattern = r"^(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+$"
            
            for page_num, page in enumerate(pages[:3]):  # First 3 pages
                print(f"\nPage {page.page_number}:")
                blocks = sorted(page.text_blocks, key=lambda b: (b.y0, b.x0))
                
                for i, block in enumerate(blocks):
                    text = block.text.strip()
                    if re.match(standard_pattern, text):
                        print(f"  FOUND STANDARD: {text}")
                    elif "KINDERGARTEN" in text.upper():
                        print(f"  FOUND GRADE: {text}")
                    elif text.upper() in ["CONNECT", "CREATE", "PRESENT", "RESPOND"]:
                        print(f"  FOUND STRAND: {text}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_pdf_blocks()