#!/usr/bin/env python3
"""Verify data quality in the database"""

import sqlite3
from pathlib import Path

def verify_data_quality():
    """Check the quality of ingested standards and objectives"""
    
    db_path = Path("data/standards/standards.db")
    if not db_path.exists():
        print("❌ Database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== Database Quality Verification ===\n")
    
    # Check total counts
    cursor.execute("SELECT COUNT(*) FROM standards")
    total_standards = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM objectives")  
    total_objectives = cursor.fetchone()[0]
    
    print(f"📊 Total counts:")
    print(f"  • Standards: {total_standards}")
    print(f"  • Objectives: {total_objectives}")
    
    # Check K.CN.1 specifically
    print("\n🔍 Checking K.CN.1:")
    cursor.execute("SELECT * FROM standards WHERE standard_id = 'K.CN.1'")
    k_cn_1 = cursor.fetchone()
    
    if k_cn_1:
        print(f"  ✅ Found K.CN.1:")
        print(f"     Grade: {k_cn_1[1]}")
        print(f"     Strand: {k_cn_1[2]}")
        print(f"     Text: {k_cn_1[5][:100]}...")
        
        # Check objectives for K.CN.1
        cursor.execute("SELECT * FROM objectives WHERE standard_id = 'K.CN.1' ORDER BY objective_id")
        objectives = cursor.fetchall()
        
        print(f"\n  Objectives ({len(objectives)}):")
        for obj in objectives:
            print(f"    • {obj[0]}: {obj[2][:80]}...")
            
        # Check for K.CN.1.1 specifically
        if any("K.CN.1.1" in obj[0] for obj in objectives):
            print("\n  ✅ K.CN.1.1 is present!")
        else:
            print("\n  ❌ K.CN.1.1 is MISSING!")
    else:
        print("  ❌ K.CN.1 not found!")
    
    # Check for mismatched objectives
    print("\n🔍 Checking for mismatched objectives:")
    cursor.execute("""
        SELECT o.objective_id, o.standard_id, o.objective_text
        FROM objectives o
        WHERE NOT o.objective_id LIKE o.standard_id || '.%'
        LIMIT 10
    """)
    mismatches = cursor.fetchall()
    
    if mismatches:
        print("  ❌ Found mismatched objectives:")
        for obj_id, std_id, text in mismatches:
            print(f"    • {obj_id} assigned to {std_id}")
    else:
        print("  ✅ All objectives correctly mapped!")
    
    # Check grade distribution
    print("\n📚 Grade distribution:")
    cursor.execute("""
        SELECT grade_level, COUNT(*) as count 
        FROM standards 
        GROUP BY grade_level 
        ORDER BY 
            CASE 
                WHEN grade_level = 'K' THEN 0
                WHEN grade_level GLOB '[0-9]*' THEN CAST(grade_level AS INTEGER)
                ELSE 100
            END,
            grade_level
    """)
    
    for grade, count in cursor.fetchall():
        print(f"  • Grade {grade}: {count} standards")
    
    # Check strand distribution
    print("\n🎵 Strand distribution:")
    cursor.execute("""
        SELECT strand_code, strand_name, COUNT(*) as count 
        FROM standards 
        GROUP BY strand_code, strand_name
        ORDER BY strand_code
    """)
    
    for strand_code, strand_name, count in cursor.fetchall():
        print(f"  • {strand_name} ({strand_code}): {count} standards")
    
    # Sample a few standards to check text quality
    print("\n📝 Sample standard texts:")
    cursor.execute("""
        SELECT standard_id, standard_text 
        FROM standards 
        WHERE standard_id IN ('K.CN.1', '1.CR.1', '5.PR.2', '8.RE.1')
        ORDER BY standard_id
    """)
    
    for std_id, text in cursor.fetchall():
        print(f"  • {std_id}: {text[:100]}...")
    
    conn.close()
    print("\n✅ Verification complete!")

if __name__ == "__main__":
    verify_data_quality()