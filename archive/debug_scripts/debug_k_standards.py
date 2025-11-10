#!/usr/bin/env python3
"""Debug Kindergarten standards extraction"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.ingestion.pdf_parser import PDFReader

def debug_k_standards():
    """Debug Kindergarten standards specifically"""
    
    pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"
    
    print("=== Debugging Kindergarten Standards ===")
    reader = PDFReader()
    
    try:
        pages = reader.read_pdf(pdf_path)
        
        # Look through pages for K standards
        import re
        standard_pattern = r"K\.(CN|CR|PR|RE)\.\d+"
        objective_pattern = r"K\.(CN|CR|PR|RE)\.\d+\.\d+"
        
        for page_num, page in enumerate(pages):
            if page.page_number < 10:  # First few pages
                print(f"\n--- Page {page.page_number} ---")
                blocks = sorted(page.text_blocks, key=lambda b: (b.y0, b.x0))
                
                for i, block in enumerate(blocks):
                    text = block.text.strip()
                    
                    # Look for anything with K.CN, K.CR, etc.
                    if "K." in text and ("CN" in text or "CR" in text or "PR" in text or "RE" in text):
                        print(f"  {i:2d}. [{block.x0:.1f},{block.y0:.1f}] {text}")
                    
                    # Look for grade/strand markers
                    elif "KINDERGARTEN" in text.upper():
                        print(f"  GRADE: {text}")
                    elif text.upper() in ["CONNECT", "CREATE", "PRESENT", "RESPOND"]:
                        print(f"  STRAND: {text}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_k_standards()