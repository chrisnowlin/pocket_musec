#!/usr/bin/env python3

import sys
sys.path.append('.')

from backend.ingestion.standards_parser_v2 import NCStandardsParser

# Test the precise parser
pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"

parser = NCStandardsParser()
standards = parser.parse_standards_document(pdf_path)

print(f"Extracted {len(standards)} standards with precise parser")

# Find K.CN.1 specifically
k_cn1 = [s for s in standards if s.standard_id == "K.CN.1"]
if k_cn1:
    standard = k_cn1[0]
    print(f"\n=== K.CN.1 Extraction Results ===")
    print(f"Standard ID: {standard.standard_id}")
    print(f"Grade: {standard.grade_level}")
    print(f"Strand: {standard.strand_code}")
    print(f"Standard Text: {standard.standard_text}")
    print(f"Objectives ({len(standard.objectives)}):")
    for i, obj in enumerate(standard.objectives):
        print(f"  {i+1}. {obj}")
else:
    print("K.CN.1 not found!")

# Show a few other standards for comparison
print(f"\n=== First 5 standards ===")
for i, standard in enumerate(standards[:5]):
    print(f"{i+1}. {standard.standard_id}: {standard.standard_text[:60]}...")
    print(f"   Objectives: {len(standard.objectives)}")