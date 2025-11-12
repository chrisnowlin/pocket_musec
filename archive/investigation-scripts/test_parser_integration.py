#!/usr/bin/env python3
"""Test the integrated vision extraction in the NC Standards parser"""

import sys
sys.path.insert(0, '/Users/cnowlin/Developer/pocket_musec')

from backend.ingestion.nc_standards_unified_parser import NCStandardsParser, ParsingStrategy
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

pdf_path = "/Users/cnowlin/Developer/pocket_musec/NC Music Standards and Resources/1 PAGE QUICK GUIDES GENERAL MUSIC - Google Docs.pdf"

print("="*70)
print("TESTING INTEGRATED VISION PARSER")
print("="*70)

# Create parser with VISION_FIRST strategy
parser = NCStandardsParser(strategy=ParsingStrategy.VISION_FIRST)

print(f"\nParser initialized with strategy: {parser.strategy}")

# Parse the document
print(f"\nParsing: {pdf_path}")
print("This will use 300 DPI and multi-page processing...")
print("-"*70)

try:
    standards = parser.parse_standards_document(pdf_path)
    
    print("\n" + "="*70)
    print("PARSING COMPLETE")
    print("="*70)
    
    print(f"\nTotal standards extracted: {len(standards)}")
    
    # Group by grade
    by_grade = {}
    for std in standards:
        grade = std.grade_level
        if grade not in by_grade:
            by_grade[grade] = []
        by_grade[grade].append(std)
    
    print(f"Grades found: {', '.join(sorted(by_grade.keys(), key=lambda x: (len(x), x)))}")
    
    # Show sample from first few grades
    print("\n" + "="*70)
    print("SAMPLE RESULTS")
    print("="*70)
    
    for grade in ['K', '1', '2', '3']:
        if grade not in by_grade:
            continue
        grade_stds = by_grade[grade]
        print(f"\nGrade {grade}: {len(grade_stds)} standards")
        
        # Show first standard
        if grade_stds:
            std = grade_stds[0]
            print(f"  Example: {std.standard_id}")
            print(f"    Text: {std.standard_text[:60]}...")
            print(f"    Objectives: {len(std.objectives)}")
    
    # Check for K.PR.2 specifically
    print("\n" + "="*70)
    print("SPECIFIC VALIDATION: K.PR.2")
    print("="*70)
    
    k_pr_2 = next((s for s in standards if s.standard_id == 'K.PR.2'), None)
    if k_pr_2:
        print(f"\n✅ K.PR.2 FOUND")
        print(f"   Text: {k_pr_2.standard_text}")
        print(f"   Objectives: {len(k_pr_2.objectives)}")
        for i, obj in enumerate(k_pr_2.objectives, 1):
            print(f"     {i}. {obj[:80]}...")
    else:
        print(f"\n❌ K.PR.2 NOT FOUND")
        # List what we do have for K
        k_stds = [s.standard_id for s in standards if s.standard_id.startswith('K.')]
        print(f"   K standards found: {', '.join(sorted(k_stds))}")
    
    # Check K.RE standards
    k_re_1 = next((s for s in standards if s.standard_id == 'K.RE.1'), None)
    k_re_2 = next((s for s in standards if s.standard_id == 'K.RE.2'), None)
    
    if k_re_1:
        print(f"\n✅ K.RE.1 FOUND with {len(k_re_1.objectives)} objectives")
    else:
        print(f"\n⚠️  K.RE.1 NOT FOUND")
        
    if k_re_2:
        print(f"✅ K.RE.2 FOUND with {len(k_re_2.objectives)} objectives")
    else:
        print(f"⚠️  K.RE.2 NOT FOUND")
    
    # Statistics
    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)
    
    total_objectives = sum(len(s.objectives) for s in standards)
    print(f"Total standards: {len(standards)}")
    print(f"Total objectives: {total_objectives}")
    if standards:
        print(f"Avg objectives/standard: {total_objectives / len(standards):.1f}")
    
    # By strand
    by_strand = {}
    for std in standards:
        strand = std.strand_code
        by_strand[strand] = by_strand.get(strand, 0) + 1
    
    if by_strand:
        print(f"\nBy strand:")
        for strand, count in sorted(by_strand.items()):
            print(f"  {strand}: {count} standards")
    
    # Check if we got complete kindergarten
    k_standards = [s for s in standards if s.standard_id.startswith('K.')]
    if len(k_standards) == 8:
        print(f"\n✅ Complete Kindergarten extraction (8/8 standards)")
    else:
        print(f"\n⚠️  Kindergarten: {len(k_standards)}/8 standards")
    
    print("\n" + "="*70)
    if k_pr_2 and len(k_standards) >= 6:
        print("✅ INTEGRATION TEST PASSED")
    else:
        print("⚠️  INTEGRATION TEST PARTIAL - Some data missing")
    print("="*70)
    
    sys.exit(0 if k_pr_2 else 1)
    
except Exception as e:
    print(f"\n{'='*70}")
    print(f"❌ INTEGRATION TEST FAILED")
    print(f"{'='*70}")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
