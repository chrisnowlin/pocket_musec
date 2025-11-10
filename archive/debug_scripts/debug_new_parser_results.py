#!/usr/bin/env python3
"""Debug the new parser results"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.ingestion.standards_parser import NCStandardsParser

def debug_new_parser():
    """Debug new parser results"""
    
    pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"
    
    print("=== Debugging New Parser Results ===")
    parser = NCStandardsParser()
    
    try:
        standards = parser.parse_standards_document(pdf_path)
        print(f"Parsed {len(standards)} standards")
        
        # Check for duplicates
        standard_ids = [s.standard_id for s in standards]
        unique_ids = set(standard_ids)
        
        print(f"Unique standard IDs: {len(unique_ids)}")
        
        if len(standard_ids) != len(unique_ids):
            print("DUPLICATES FOUND:")
            from collections import Counter
            counts = Counter(standard_ids)
            for std_id, count in counts.items():
                if count > 1:
                    print(f"  {std_id}: {count} times")
        
        # Show first few standards
        print("\nFirst 10 standards:")
        for i, std in enumerate(standards[:10]):
            print(f"  {i+1:2d}. {std.standard_id}: {std.standard_text[:60]}...")
            print(f"       Objectives: {len(std.objectives)}")
            for obj in std.objectives[:2]:
                print(f"         {obj}")
        
        # Show statistics
        stats = parser.get_statistics()
        print(f"\nStatistics: {stats}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_new_parser()