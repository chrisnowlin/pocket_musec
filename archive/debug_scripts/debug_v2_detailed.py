#!/usr/bin/env python3
"""Detailed debug of v2 parser"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.ingestion.standards_parser_v2 import NCStandardsParser

def debug_v2_detailed():
    """Debug v2 parser step by step"""
    
    pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"
    
    print("=== Detailed V2 Parser Debug ===")
    parser = NCStandardsParser()
    
    try:
        # Read PDF
        pages = parser.pdf_reader.read_pdf(pdf_path)
        print(f"Read {len(pages)} pages")
        
        # Test pattern matching
        import re
        
        # Test the patterns
        standard_id_pattern = r"^(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+$"
        objective_pattern = r"^(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+"
        
        print(f"\nStandard pattern: {standard_id_pattern}")
        print(f"Objective pattern: {objective_pattern}")
        
        # Test on actual blocks
        for page_num, page in enumerate(pages[:3]):
            print(f"\n--- Page {page.page_number} ---")
            blocks = sorted(page.text_blocks, key=lambda b: (b.y0, b.x0))
            
            for i, block in enumerate(blocks[:15]):  # First 15 blocks
                text = block.text.strip()
                
                # Test grade extraction
                grade = parser._extract_grade_level_precise(text)
                strand = parser._extract_strand_precise(text)
                standard_id = parser._extract_standard_id_precise(text)
                is_objective = parser._is_objective_precise(text)
                
                if any([grade, strand, standard_id, is_objective]):
                    print(f"  {i:2d}. [{block.x0:.1f},{block.y0:.1f}] '{text}'")
                    if grade:
                        print(f"      -> GRADE: {grade}")
                    if strand:
                        print(f"      -> STRAND: {strand}")
                    if standard_id:
                        print(f"      -> STANDARD ID: {standard_id}")
                    if is_objective:
                        print(f"      -> OBJECTIVE")
                elif "K." in text or "KINDERGARTEN" in text.upper():
                    print(f"  {i:2d}. [{block.x0:.1f},{block.y0:.1f}] '{text}' (no match)")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_v2_detailed()