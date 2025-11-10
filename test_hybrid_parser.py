#!/usr/bin/env python3
"""Test the hybrid parser"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.ingestion.standards_parser_hybrid import NCStandardsParser

def test_hybrid_parser():
    """Test hybrid parser for accuracy"""
    
    pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"
    
    print("=== Testing Hybrid Parser ===\n")
    parser = NCStandardsParser()
    
    try:
        standards = parser.parse_standards_document(pdf_path)
        print(f"Parsed {len(standards)} standards")
        
        # Check for K.CN.1 specifically
        k_cn_1 = None
        for std in standards:
            if std.standard_id == "K.CN.1":
                k_cn_1 = std
                break
        
        if k_cn_1:
            print("\n✅ K.CN.1 FOUND:")
            print(f"  Grade: {k_cn_1.grade_level}")
            print(f"  Strand: {k_cn_1.strand_code} - {k_cn_1.strand_name}")
            print(f"  Standard Text: {k_cn_1.standard_text}")
            print(f"  Number of Objectives: {len(k_cn_1.objectives)}")
            print("\n  Objectives:")
            
            # Check for K.CN.1.1 specifically
            has_kcn11 = False
            for i, obj in enumerate(k_cn_1.objectives):
                print(f"    {i+1}. {obj[:100]}...")
                if "K.CN.1.1" in obj:
                    has_kcn11 = True
            
            if has_kcn11:
                print("\n  ✅ K.CN.1.1 is included!")
            else:
                print("\n  ❌ K.CN.1.1 is MISSING!")
        else:
            print("❌ K.CN.1 NOT FOUND!")
        
        # Show statistics
        stats = parser.get_statistics()
        print(f"\n📊 Statistics:")
        print(f"  • Total standards: {stats.get('total_standards', 0)}")
        print(f"  • Total objectives: {stats.get('total_objectives', 0)}")
        print(f"  • Average objectives per standard: {stats.get('average_objectives_per_standard', 0):.1f}")
        
        # Grade distribution
        print(f"\n📚 Grade distribution:")
        for grade, count in stats.get('grade_distribution', {}).items():
            print(f"  • {grade}: {count} standards")
        
        # Check for wrong mappings
        print("\n🔍 Checking for mismatched objectives:")
        issues_found = False
        for std in standards:
            for obj in std.objectives:
                # Extract objective ID from text
                if "." in obj:
                    obj_id_parts = obj.split(' ')[0] if ' ' in obj else obj
                    if '.' in obj_id_parts:
                        # Check if objective starts with the correct standard ID
                        if not obj_id_parts.startswith(std.standard_id + "."):
                            print(f"  ❌ Mismatch: {obj_id_parts} assigned to {std.standard_id}")
                            issues_found = True
        
        if not issues_found:
            print("  ✅ All objectives correctly mapped to their standards!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hybrid_parser()