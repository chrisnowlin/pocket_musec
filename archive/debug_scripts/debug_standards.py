#!/usr/bin/env python3

import sys
sys.path.append('.')

from backend.ingestion.standards_parser import NCStandardsParser

# Test the standards parser with debug output
pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"

parser = NCStandardsParser()
pages = parser.pdf_reader.read_pdf(pdf_path)

print(f"Parsed {len(pages)} pages")

# Look at page 2 where Kindergarten standards should be
if len(pages) > 1:
    page = pages[1]  # Page 2 (0-indexed)
    print(f"\nPage 2 has {len(page.text_blocks)} text blocks")
    
    for i, block in enumerate(page.text_blocks[:20]):
        print(f"Block {i+1}: {block.text}")
        
        # Test the extraction functions
        grade = parser._extract_grade_level(block.text)
        strand = parser._extract_strand(block.text)
        standard_id = parser._extract_standard_id(block.text)
        
        if grade:
            print(f"  -> GRADE: {grade}")
        if strand:
            print(f"  -> STRAND: {strand}")
        if standard_id:
            print(f"  -> STANDARD ID: {standard_id}")

# Test strand extraction
print("\n\n--- Testing strand extraction ---")
test_texts = [
    "CONNECT",
    "CN - Explore and relate artistic ideas and works to past, present, and future societies and cultures.",
    "CREATE",
    "K.CN.1.1 Identify the similarities and differences of music representing diverse global",
    "K.CR.1.1 Improvise rhythmic patterns and 2-pitch melodic patterns."
]

for text in test_texts:
    strand = parser._extract_strand(text)
    standard_id = parser._extract_standard_id(text)
    grade = parser._extract_grade_level(text)
    print(f"Text: {text}")
    print(f"  Grade: {grade}")
    print(f"  Strand: {strand}")
    print(f"  Standard ID: {standard_id}")
    print()