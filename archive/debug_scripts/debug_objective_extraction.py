#!/usr/bin/env python3
"""Debug objective extraction in v2 parser"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.ingestion.standards_parser_v2 import NCStandardsParser

def debug_objective_extraction():
    """Debug objective extraction specifically"""
    
    pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"
    
    print("=== Debugging Objective Extraction ===")
    parser = NCStandardsParser()
    
    try:
        # Read PDF
        pages = parser.pdf_reader.read_pdf(pdf_path)
        
        # Look at first few pages and manually extract K.CN.1
        for page_num, page in enumerate(pages[:3]):
            if page.page_number == 2:  # Page with K.CN.1
                print(f"\n--- Page {page.page_number} ---")
                blocks = sorted(page.text_blocks, key=lambda b: (b.y0, b.x0))
                
                # Find blocks around K.CN.1
                for i, block in enumerate(blocks):
                    text = block.text.strip()
                    
                    if "K.CN.1" in text:
                        print(f"Block {i}: '{text}'")
                        
                        # Check if it's identified as objective
                        is_obj = parser._is_objective_precise(text)
                        print(f"  Is objective: {is_obj}")
                        
                        # Show surrounding blocks
                        print("  Surrounding blocks:")
                        for j in range(max(0, i-2), min(len(blocks), i+5)):
                            surrounding_text = blocks[j].text.strip()
                            surrounding_is_obj = parser._is_objective_precise(surrounding_text)
                            print(f"    {j}: '{surrounding_text}' (obj: {surrounding_is_obj})")
                        break
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_objective_extraction()