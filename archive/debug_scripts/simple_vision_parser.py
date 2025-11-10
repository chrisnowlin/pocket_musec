#!/usr/bin/env python3
"""Simple vision parser for NC Music Standards"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Run vision parser on standards documents"""
    
    print("🎵 PocketMusec Vision Parser")
    print("Processing NC Music Standards with AI vision enhancement...\n")
    
    # Find standards PDFs
    standards_dir = Path("NC Music Standards and Resources")
    if not standards_dir.exists():
        print(f"❌ Error: Standards directory not found: {standards_dir}")
        return
    
    pdf_files = list(standards_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDF files found in standards directory")
        return
    
    print(f"✅ Found {len(pdf_files)} PDF files to process")
    for pdf in pdf_files:
        print(f"  • {pdf.name}")
    
    print("\n⚠️  This will take some time as each page is processed with AI vision...")
    
    try:
        # Import here to avoid import errors
        from backend.ingestion.standards_parser_vision import NCStandardsParser
        from backend.repositories.database import DatabaseManager
        
        # Initialize database
        db_manager = DatabaseManager()
        db_manager.initialize_database()
        
        # Initialize vision parser
        parser = NCStandardsParser(use_vision=True)
        
        total_standards = 0
        total_objectives = 0
        
        # Process each PDF
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n📄 Processing {i}/{len(pdf_files)}: {pdf_file.name}")
            
            start_time = time.time()
            
            try:
                # Parse with vision enhancement
                standards = parser.parse_standards_document(str(pdf_file))
                
                # Convert to database models
                db_standards, db_objectives = parser.normalize_to_models(pdf_file.name)
                
                # Save to database
                with db_manager.get_connection() as conn:
                    # Clear existing data for this document
                    conn.execute("DELETE FROM standards WHERE source_document = ?", (pdf_file.name,))
                    
                    # Insert new data
                    for standard in db_standards:
                        conn.execute(
                            """INSERT INTO standards 
                               (standard_id, grade_level, strand_code, strand_name, 
                                strand_description, standard_text, source_document, 
                                ingestion_date, version)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                standard.standard_id,
                                standard.grade_level,
                                standard.strand_code,
                                standard.strand_name,
                                standard.strand_description,
                                standard.standard_text,
                                standard.source_document,
                                standard.ingestion_date,
                                standard.version
                            )
                        )
                    
                    for objective in db_objectives:
                        conn.execute(
                            """INSERT INTO objectives (objective_id, standard_id, objective_text)
                               VALUES (?, ?, ?)""",
                            (objective.objective_id, objective.standard_id, objective.objective_text)
                        )
                    
                    conn.commit()
                
                processing_time = time.time() - start_time
                
                # Get statistics
                stats = parser.get_statistics()
                
                print(f"✅ Completed {pdf_file.name}")
                print(f"   Standards: {stats.get('total_standards', 0)}")
                print(f"   Objectives: {stats.get('total_objectives', 0)}")
                print(f"   Time: {processing_time:.1f}s")
                print(f"   Vision enhanced: {stats.get('vision_enhanced', False)}")
                
                total_standards += stats.get('total_standards', 0)
                total_objectives += stats.get('total_objectives', 0)
                
            except Exception as e:
                print(f"❌ Failed to process {pdf_file.name}: {e}")
                continue
        
        # Final summary
        print("\n" + "="*60)
        print("🎉 Vision Processing Complete!")
        print(f"\nSummary:")
        print(f"  • Files processed: {len(pdf_files)}")
        print(f"  • Total standards extracted: {total_standards}")
        print(f"  • Total objectives extracted: {total_objectives}")
        
        # Database verification
        with db_manager.get_connection() as conn:
            std_count = conn.execute("SELECT COUNT(*) FROM standards").fetchone()[0]
            obj_count = conn.execute("SELECT COUNT(*) FROM objectives").fetchone()[0]
            
            print(f"\nDatabase Verification:")
            print(f"  • Standards in database: {std_count}")
            print(f"  • Objectives in database: {obj_count}")
            
            if std_count == total_standards and obj_count == total_objectives:
                print("✅ Database counts match extraction totals")
            else:
                print("⚠️  Database counts don't match extraction totals")
        
        print("\n🎵 Vision-enhanced standards are now ready for lesson generation!")
        print("="*60)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()