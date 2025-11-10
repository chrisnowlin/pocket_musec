#!/usr/bin/env python3
"""Debug the v2 parser"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.ingestion.standards_parser_v2 import NCStandardsParser

def debug_v2():
    """Debug the v2 parser"""
    
    pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"
    
    print("=== Debugging V2 Parser ===")
    parser = NCStandardsParser()
    
    try:
        standards = parser.parse_standards_document(pdf_path)
        print(f"Parsed {len(standards)} standards")
        
        if standards:
            print("First few standards:")
            for i, std in enumerate(standards[:3]):
                print(f"  {i+1}. {std.standard_id}: {std.standard_text[:80]}...")
                print(f"      Grade: {std.grade_level}, Strand: {std.strand_code}")
                print(f"      Objectives: {len(std.objectives)}")
                for obj in std.objectives[:2]:
                    print(f"        {obj}")
        else:
            print("No standards parsed!")
            
        # Get stats
        stats = parser.get_statistics()
        print(f"Stats: {stats}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_v2()