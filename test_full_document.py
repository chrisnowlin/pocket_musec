#!/usr/bin/env python3
"""Test extraction on the full 22-page document"""

import sys
sys.path.insert(0, '/Users/cnowlin/Developer/pocket_musec')

from backend.llm.chutes_client import ChutesClient
from backend.ingestion.vision_extraction_helper import (
    extract_standards_from_pdf_multipage,
    get_extraction_statistics
)
import time

pdf_path = "/Users/cnowlin/Developer/pocket_musec/NC Music Standards and Resources/1 PAGE QUICK GUIDES GENERAL MUSIC - Google Docs.pdf"

print("="*70)
print("FULL DOCUMENT EXTRACTION TEST (22 pages)")
print("="*70)

client = ChutesClient()

print("\nStarting extraction...")
print("This will process all 22 pages at 300 DPI")
print("Expected time: ~5-8 minutes for complete extraction")
print("-"*70)

start_time = time.time()

try:
    standards = extract_standards_from_pdf_multipage(
        pdf_path=pdf_path,
        llm_client=client,
        page_range=None,  # Process all pages
        grade_filter=None,  # Extract all grades
        dpi=300
    )
    
    elapsed_time = time.time() - start_time
    
    print(f"\n{'='*70}")
    print("EXTRACTION COMPLETE")
    print("="*70)
    print(f"Time: {elapsed_time/60:.1f} minutes ({elapsed_time:.1f} seconds)")
    print(f"Standards extracted: {len(standards)}")
    
    # Get statistics
    stats = get_extraction_statistics(standards)
    
    print(f"\n{'='*70}")
    print("STATISTICS")
    print("="*70)
    print(f"Total standards: {stats['total_standards']}")
    print(f"Total objectives: {stats['total_objectives']}")
    print(f"Avg objectives per standard: {stats['avg_objectives_per_standard']:.1f}")
    
    print(f"\nBy Grade:")
    for grade, count in sorted(stats['by_grade'].items(), key=lambda x: (len(x[0]), x[0])):
        print(f"  {grade:3s}: {count:2d} standards")
    
    print(f"\nBy Strand:")
    for strand, count in sorted(stats['by_strand'].items()):
        print(f"  {strand}: {count} standards")
    
    # Check for complete kindergarten
    print(f"\n{'='*70}")
    print("KINDERGARTEN VALIDATION")
    print("="*70)
    
    k_standards = [s for s in standards if s['id'].startswith('K.')]
    print(f"Kindergarten standards: {len(k_standards)}/8 expected")
    
    k_ids = sorted([s['id'] for s in k_standards])
    expected_k = ['K.CN.1', 'K.CN.2', 'K.CR.1', 'K.CR.2', 'K.PR.1', 'K.PR.2', 'K.RE.1', 'K.RE.2']
    
    for exp_id in expected_k:
        found = exp_id in k_ids
        status = "✅" if found else "❌"
        print(f"  {status} {exp_id}")
    
    # Check K.PR.2 specifically
    k_pr_2 = next((s for s in standards if s['id'] == 'K.PR.2'), None)
    if k_pr_2:
        print(f"\n✅ K.PR.2 validated:")
        print(f"   Text: {k_pr_2['text'][:60]}...")
        print(f"   Objectives: {len(k_pr_2.get('objectives', []))}")
    
    # Sample from each grade level
    print(f"\n{'='*70}")
    print("SAMPLE BY GRADE LEVEL")
    print("="*70)
    
    for grade in ['K', '1', '2', '3', '4', '5', '6', '7', '8']:
        grade_stds = [s for s in standards if s['id'].startswith(f'{grade}.')]
        if grade_stds:
            total_obj = sum(len(s.get('objectives', [])) for s in grade_stds)
            print(f"\nGrade {grade}: {len(grade_stds)} standards, {total_obj} objectives")
            
            # Show first standard as sample
            sample = grade_stds[0]
            print(f"  Example: {sample['id']} - {sample['text'][:50]}...")
    
    # Check for secondary levels
    print(f"\n{'='*70}")
    print("SECONDARY LEVELS")
    print("="*70)
    
    for level in ['BE', 'IN', 'AD', 'AC']:
        level_stds = [s for s in standards if s['id'].startswith(f'{level}.')]
        if level_stds:
            print(f"{level}: {len(level_stds)} standards")
        else:
            print(f"{level}: Not found in document")
    
    # Performance metrics
    print(f"\n{'='*70}")
    print("PERFORMANCE")
    print("="*70)
    print(f"Total time: {elapsed_time:.1f}s ({elapsed_time/60:.1f} min)")
    print(f"Pages processed: 22")
    print(f"Avg per page: {elapsed_time/22:.1f}s")
    print(f"Standards per minute: {len(standards)/(elapsed_time/60):.1f}")
    
    # Completeness check
    print(f"\n{'='*70}")
    print("COMPLETENESS CHECK")
    print("="*70)
    
    # Expected: K-8 = 9 grades × 8 standards = 72 standards minimum
    elementary_grades = ['K', '1', '2', '3', '4', '5', '6', '7', '8']
    elementary_count = sum(1 for s in standards if any(s['id'].startswith(f'{g}.') for g in elementary_grades))
    
    print(f"Elementary (K-8): {elementary_count} standards")
    expected_elem = 9 * 8  # 9 grades × 8 standards each
    print(f"Expected minimum: {expected_elem} standards")
    
    if elementary_count >= expected_elem:
        print(f"✅ Complete elementary coverage")
    else:
        print(f"⚠️  Missing {expected_elem - elementary_count} elementary standards")
    
    print(f"\n{'='*70}")
    if len(standards) >= 70:  # At least most standards
        print("✅ FULL DOCUMENT TEST PASSED")
        print("="*70)
        exit_code = 0
    else:
        print("⚠️  FULL DOCUMENT TEST PARTIAL")
        print("="*70)
        exit_code = 1
    
    sys.exit(exit_code)
    
except KeyboardInterrupt:
    print("\n\n⚠️  Test interrupted by user")
    sys.exit(1)
    
except Exception as e:
    print(f"\n{'='*70}")
    print("❌ FULL DOCUMENT TEST FAILED")
    print("="*70)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
