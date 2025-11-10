#!/usr/bin/env python3

import sys
sys.path.append('.')

from backend.ingestion.standards_parser import NCStandardsParser

# Test the parsing with state tracking
pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"

parser = NCStandardsParser()
pages = parser.pdf_reader.read_pdf(pdf_path)

print(f"Parsed {len(pages)} pages")

# Manually test the parsing logic for page 2
if len(pages) > 1:
    page = pages[1]  # Page 2 (0-indexed)
    print(f"\n=== Parsing Page 2 ===")
    
    standards = []
    current_grade = None
    current_strand = None
    
    # Get text blocks in reading order
    blocks = sorted(page.text_blocks, key=lambda b: (b.y0, b.x0))
    
    for i, block in enumerate(blocks):
        text = block.text.strip()
        
        print(f"\nBlock {i+1}: {text}")
        print(f"  Current grade: {current_grade}")
        print(f"  Current strand: {current_strand}")
        
        # Check for grade level headers
        grade = parser._extract_grade_level(text)
        if grade:
            current_grade = grade
            print(f"  -> FOUND GRADE: {grade}")
            continue
        
        # Check for strand headers
        strand = parser._extract_strand(text)
        if strand:
            current_strand = strand
            print(f"  -> FOUND STRAND: {strand}")
            continue
        
        # Check for standard IDs
        standard_id = parser._extract_standard_id(text)
        if standard_id:
            print(f"  -> FOUND STANDARD ID: {standard_id}")
            print(f"  -> Conditions: grade={current_grade}, strand={current_strand}")
            
            if current_grade and current_strand:
                print(f"  -> WOULD EXTRACT STANDARD HERE!")
                # This is where a standard would be extracted
            else:
                print(f"  -> Missing grade or strand, skipping")
        
        if i >= 25:  # Limit output
            break