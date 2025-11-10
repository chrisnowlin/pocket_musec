#!/usr/bin/env python3
"""Analyze the specific K.CN.1 extraction issue"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.ingestion.standards_parser_original import NCStandardsParser as OldParser
from backend.ingestion.pdf_parser import PDFReader

def analyze_kcn1():
    """Analyze K.CN.1 extraction specifically"""
    
    pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"
    
    print("=== Analyzing K.CN.1 Extraction Issue ===\n")
    
    # First, look at the raw PDF blocks around K.CN.1
    reader = PDFReader()
    pages = reader.read_pdf(pdf_path)
    
    print("1. RAW PDF BLOCKS AROUND K.CN.1:")
    print("-" * 50)
    
    for page in pages[:5]:  # First 5 pages
        blocks = sorted(page.text_blocks, key=lambda b: (b.y0, b.x0))
        for i, block in enumerate(blocks):
            text = block.text.strip()
            if "K.CN.1" in text:
                print(f"\nPage {page.page_number}, Block {i}:")
                print(f"  Position: [{block.x0:.1f}, {block.y0:.1f}]")
                print(f"  Text: '{text}'")
                
                # Show surrounding blocks for context
                print("  Context blocks:")
                for j in range(max(0, i-3), min(len(blocks), i+4)):
                    if j != i:
                        ctx_block = blocks[j]
                        ctx_text = ctx_block.text.strip()[:80]
                        print(f"    [{j}] '{ctx_text}'")
    
    # Now see what the parser extracts
    print("\n2. PARSER EXTRACTION:")
    print("-" * 50)
    
    parser = OldParser()
    standards = parser.parse_standards_document(pdf_path)
    
    # Find K.CN.1
    k_cn_1 = None
    for std in standards:
        if std.standard_id == "K.CN.1":
            k_cn_1 = std
            break
    
    if k_cn_1:
        print(f"Standard ID: {k_cn_1.standard_id}")
        print(f"Grade: {k_cn_1.grade_level}")
        print(f"Strand: {k_cn_1.strand_code} - {k_cn_1.strand_name}")
        print(f"Standard Text: {k_cn_1.standard_text}")
        print(f"Number of Objectives: {len(k_cn_1.objectives)}")
        print("\nObjectives:")
        for i, obj in enumerate(k_cn_1.objectives):
            print(f"  {i+1}. {obj}")
    else:
        print("K.CN.1 NOT FOUND!")
    
    # Check if K.CN.1.1 appears anywhere
    print("\n3. K.CN.1.1 SEARCH:")
    print("-" * 50)
    
    k_cn_1_1_found = False
    for std in standards:
        for obj in std.objectives:
            if "K.CN.1.1" in obj:
                print(f"Found in standard {std.standard_id}: {obj}")
                k_cn_1_1_found = True
                
    if not k_cn_1_1_found:
        print("K.CN.1.1 NOT found in any objectives!")
        
        # Look for it in the raw PDF
        print("\nSearching raw PDF for K.CN.1.1...")
        for page in pages[:10]:
            for block in page.text_blocks:
                if "K.CN.1.1" in block.text:
                    print(f"  Found on page {page.page_number}: '{block.text.strip()}'")

if __name__ == "__main__":
    analyze_kcn1()