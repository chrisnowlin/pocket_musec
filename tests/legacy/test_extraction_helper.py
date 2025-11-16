#!/usr/bin/env python3
"""Test the new extraction helper"""

import sys
sys.path.insert(0, '/Users/cnowlin/Developer/pocket_musec')

from backend.llm.chutes_client import ChutesClient
from backend.ingestion.vision_extraction_helper import (
    extract_standards_from_pdf_multipage,
    get_extraction_statistics
)

pdf_path = "/Users/cnowlin/Developer/pocket_musec/NC Music Standards and Resources/1 PAGE QUICK GUIDES GENERAL MUSIC - Google Docs.pdf"

print("="*70)
print("TESTING REFINED EXTRACTION HELPER")
print("="*70)

# Extract Kindergarten standards from first 2 pages
client = ChutesClient()
standards = extract_standards_from_pdf_multipage(
    pdf_path=pdf_path,
    llm_client=client,
    page_range=(1, 2),
    grade_filter="K",
    dpi=150
)

print(f"\n{'='*70}")
print("EXTRACTION RESULTS")
print("="*70)

for std in sorted(standards, key=lambda x: x['id']):
    print(f"\n**{std['id']}**: {std['text'][:80]}...")
    objectives = std.get('objectives', [])
    print(f"  Objectives: {len(objectives)}")
    for obj in objectives:
        print(f"    - {obj['id']}: {obj['text'][:60]}...")

stats = get_extraction_statistics(standards)

print(f"\n{'='*70}")
print("STATISTICS")
print("="*70)
print(f"Total standards: {stats['total_standards']}")
print(f"Total objectives: {stats['total_objectives']}")
print(f"Avg objectives/standard: {stats['avg_objectives_per_standard']:.1f}")
print(f"By grade: {stats['by_grade']}")
print(f"By strand: {stats['by_strand']}")

# Verify completeness
expected = ['K.CN.1', 'K.CN.2', 'K.CR.1', 'K.CR.2', 'K.PR.1', 'K.PR.2', 'K.RE.1', 'K.RE.2']
found = [s['id'] for s in standards]
missing = [e for e in expected if e not in found]

print(f"\n{'='*70}")
print("COMPLETENESS CHECK")
print("="*70)
print(f"Expected: {', '.join(expected)}")
print(f"Found: {', '.join(sorted(found))}")
if missing:
    print(f"❌ Missing: {', '.join(missing)}")
else:
    print(f"✅ All expected standards found!")

# Check K.PR.2 specifically
k_pr_2 = next((s for s in standards if s['id'] == 'K.PR.2'), None)
if k_pr_2:
    print(f"\n✅ K.PR.2 found with {len(k_pr_2.get('objectives', []))} objectives")
else:
    print(f"\n❌ K.PR.2 NOT FOUND")
