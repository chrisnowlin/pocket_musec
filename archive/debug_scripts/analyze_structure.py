#!/usr/bin/env python3

import sys
sys.path.append('.')

from backend.ingestion.standards_parser import NCStandardsParser

# Analyze the exact structure of standards and objectives
pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"

parser = NCStandardsParser()
pages = parser.pdf_reader.read_pdf(pdf_path)

# Look at page 2 where Kindergarten standards are
if len(pages) > 1:
    page = pages[1]  # Page 2 (0-indexed)
    blocks = sorted(page.text_blocks, key=lambda b: (b.y0, b.x0))
    
    print("=== Complete analysis of K.CN.1 section ===")
    
    # Find the K.CN.1 section
    in_k_cn1_section = False
    k_cn1_blocks = []
    
    for i, block in enumerate(blocks):
        text = block.text.strip()
        
        # Start of K.CN.1 section
        if "K.CN.1" in text and not in_k_cn1_section:
            in_k_cn1_section = True
            print(f"STARTING K.CN.1 SECTION at block {i+1}")
        
        if in_k_cn1_section:
            k_cn1_blocks.append((i+1, text))
            
            # Check for different types of content
            is_standard_id = parser._extract_standard_id(text)
            is_objective = parser._is_objective(text)
            is_strand = parser._extract_strand(text)
            is_grade = parser._extract_grade_level(text)
            
            print(f"Block {i+1}: {text}")
            if is_standard_id:
                print(f"  -> STANDARD ID: {is_standard_id}")
            if is_objective:
                print(f"  -> OBJECTIVE")
            if is_strand:
                print(f"  -> STRAND: {is_strand}")
            if is_grade:
                print(f"  -> GRADE: {is_grade}")
            print()
            
            # End of section when we hit the next standard
            if "K.CN.2" in text and "K.CN.1" not in text:
                print(f"ENDING K.CN.1 SECTION at block {i+1}")
                break
                
    print(f"\nTotal blocks in K.CN.1 section: {len(k_cn1_blocks)}")
    
    # Now let's see what the current parser extracted for K.CN.1
    print("\n=== Current parser extraction for K.CN.1 ===")
    standards = parser.parse_standards_document(pdf_path)
    k_cn1_standards = [s for s in standards if s.standard_id == "K.CN.1"]
    
    if k_cn1_standards:
        standard = k_cn1_standards[0]
        print(f"Standard ID: {standard.standard_id}")
        print(f"Standard text: {standard.standard_text}")
        print(f"Objectives ({len(standard.objectives)}):")
        for i, obj in enumerate(standard.objectives):
            print(f"  {i+1}. {obj}")
    else:
        print("No K.CN.1 standard found!")