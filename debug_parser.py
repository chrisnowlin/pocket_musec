#!/usr/bin/env python3

import sys
sys.path.append('.')

from backend.ingestion.pdf_parser import PDFReader

# Test the full parsing pipeline
pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"

reader = PDFReader()
pages = reader.read_pdf(pdf_path)

print(f"Parsed {len(pages)} pages")

# Check first page text blocks
if pages:
    page = pages[0]
    print(f"\nPage 1 has {len(page.text_blocks)} text blocks")
    
    for i, block in enumerate(page.text_blocks[:10]):
        print(f"Block {i+1}: {block.text[:100]}...")

# Test standards parser
from backend.ingestion.standards_parser import NCStandardsParser

parser = NCStandardsParser()
standards = parser.parse_standards_document(pdf_path)

print(f"\nExtracted {len(standards)} standards")

# Show some extracted standards if any
for i, standard in enumerate(standards[:3]):
    print(f"\nStandard {i+1}:")
    print(f"  ID: {standard.standard_id}")
    print(f"  Grade: {standard.grade_level}")
    print(f"  Strand: {standard.strand_code}")
    print(f"  Text: {standard.standard_text[:100]}...")