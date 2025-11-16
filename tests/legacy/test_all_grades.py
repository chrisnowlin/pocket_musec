#!/usr/bin/env python3
"""Test vision extraction across multiple grade levels"""

import sys
sys.path.insert(0, '/Users/cnowlin/Developer/pocket_musec')

from backend.llm.chutes_client import ChutesClient
from backend.ingestion.vision_extraction_helper import (
    extract_standards_from_pdf_multipage,
    get_extraction_statistics
)
import time

pdf_path = "/Users/cnowlin/Developer/pocket_musec/NC Music Standards and Resources/1 PAGE QUICK GUIDES GENERAL MUSIC - Google Docs.pdf"

# Test different grade levels
# Based on typical standards document structure, each grade likely has 2 pages
test_grades = [
    {"grade": "K", "pages": (1, 2), "label": "Kindergarten"},
    {"grade": "1", "pages": (3, 4), "label": "1st Grade"},
    {"grade": "2", "pages": (5, 6), "label": "2nd Grade"},
    {"grade": "3", "pages": (7, 8), "label": "3rd Grade"},
]

print("="*70)
print("MULTI-GRADE VISION EXTRACTION TEST (DPI: 300)")
print("="*70)

client = ChutesClient()
all_results = {}

for test in test_grades:
    grade = test["grade"]
    pages = test["pages"]
    label = test["label"]
    
    print(f"\n{'='*70}")
    print(f"Testing {label} (Grade {grade}) - Pages {pages[0]}-{pages[1]}")
    print("="*70)
    
    start_time = time.time()
    
    try:
        standards = extract_standards_from_pdf_multipage(
            pdf_path=pdf_path,
            llm_client=client,
            page_range=pages,
            grade_filter=grade,
            dpi=300  # High quality
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n✓ Extraction completed in {elapsed:.1f}s")
        print(f"  Standards found: {len(standards)}")
        
        # Display results
        for std in sorted(standards, key=lambda x: x['id']):
            std_id = std['id']
            text_preview = std['text'][:60] + "..." if len(std['text']) > 60 else std['text']
            obj_count = len(std.get('objectives', []))
            
            print(f"\n  {std_id}: {text_preview}")
            print(f"    └─ {obj_count} objectives")
            
            # Show objectives
            for obj in std.get('objectives', [])[:3]:  # First 3
                obj_preview = obj['text'][:50] + "..." if len(obj['text']) > 50 else obj['text']
                print(f"       • {obj['id']}: {obj_preview}")
            
            if obj_count > 3:
                print(f"       • ... and {obj_count - 3} more")
        
        # Statistics
        stats = get_extraction_statistics(standards)
        print(f"\n  Statistics:")
        print(f"    Total standards: {stats['total_standards']}")
        print(f"    Total objectives: {stats['total_objectives']}")
        print(f"    Avg objectives/standard: {stats['avg_objectives_per_standard']:.1f}")
        print(f"    By strand: {stats['by_strand']}")
        
        # Completeness check
        expected_count = 8  # 2 standards per strand × 4 strands
        expected_strands = ['CN', 'CR', 'PR', 'RE']
        
        found_strands = list(stats['by_strand'].keys())
        missing_strands = [s for s in expected_strands if s not in found_strands]
        
        if len(standards) == expected_count and not missing_strands:
            print(f"    ✅ Complete: All {expected_count} standards found")
        else:
            print(f"    ⚠️  Expected {expected_count}, found {len(standards)}")
            if missing_strands:
                print(f"    ⚠️  Missing strands: {', '.join(missing_strands)}")
        
        all_results[grade] = {
            'standards': standards,
            'stats': stats,
            'elapsed': elapsed,
            'complete': len(standards) == expected_count and not missing_strands
        }
        
    except Exception as e:
        print(f"\n❌ Error extracting {label}: {e}")
        import traceback
        traceback.print_exc()
        all_results[grade] = None

# Final summary
print("\n" + "="*70)
print("FINAL SUMMARY")
print("="*70)

total_standards = 0
total_objectives = 0
complete_grades = []
incomplete_grades = []

for grade, result in all_results.items():
    if result:
        total_standards += result['stats']['total_standards']
        total_objectives += result['stats']['total_objectives']
        
        status = "✅" if result['complete'] else "⚠️"
        elapsed = result['elapsed']
        std_count = result['stats']['total_standards']
        obj_count = result['stats']['total_objectives']
        
        print(f"\n{status} Grade {grade}: {std_count} standards, {obj_count} objectives ({elapsed:.1f}s)")
        
        if result['complete']:
            complete_grades.append(grade)
        else:
            incomplete_grades.append(grade)
    else:
        print(f"\n❌ Grade {grade}: Failed to extract")
        incomplete_grades.append(grade)

print(f"\n{'─'*70}")
print(f"Total across all grades: {total_standards} standards, {total_objectives} objectives")
print(f"Complete grades: {len(complete_grades)}/{len(test_grades)}")

if incomplete_grades:
    print(f"⚠️  Incomplete/Failed: {', '.join(incomplete_grades)}")
else:
    print(f"✅ All grades extracted completely!")

# Check for specific standards mentioned in issue
print(f"\n{'─'*70}")
print("Specific Checks:")

# K.PR.2
k_result = all_results.get('K')
if k_result and k_result['standards']:
    k_pr_2 = next((s for s in k_result['standards'] if s['id'] == 'K.PR.2'), None)
    if k_pr_2:
        print(f"✅ K.PR.2 found with {len(k_pr_2.get('objectives', []))} objectives")
    else:
        print(f"❌ K.PR.2 NOT FOUND")

# Check one standard from each grade
for grade in ['1', '2', '3']:
    result = all_results.get(grade)
    if result and result['standards']:
        pr_2 = next((s for s in result['standards'] if s['id'] == f'{grade}.PR.2'), None)
        if pr_2:
            print(f"✅ {grade}.PR.2 found with {len(pr_2.get('objectives', []))} objectives")
        else:
            print(f"⚠️  {grade}.PR.2 not found (may not exist in document)")

print("="*70)
