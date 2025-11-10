#!/usr/bin/env python3

import sys
sys.path.append('.')

from backend.ingestion.standards_parser import NCStandardsParser

# Debug objective extraction
pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"

parser = NCStandardsParser()
pages = parser.pdf_reader.read_pdf(pdf_path)

# Look at page 2 where Kindergarten standards are
if len(pages) > 1:
    page = pages[1]  # Page 2 (0-indexed)
    blocks = sorted(page.text_blocks, key=lambda b: (b.y0, b.x0))
    
    print("=== Blocks around K.CN.1 ===")
    for i, block in enumerate(blocks[8:20]):  # Around where K.CN.1 should be
        print(f"Block {i+9}: {block.text}")
        is_obj = parser._is_objective(block.text)
        print(f"  Is objective: {is_obj}")
        print()