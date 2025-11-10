"""Integration tests for ingestion workflow"""

def test_full_ingestion_workflow():
    """Test the complete ingestion workflow with a simple PDF"""
    from backend.ingestion.standards_parser import NCStandardsParser
    from backend.repositories.database import DatabaseManager
    import tempfile
    import os
    from pathlib import Path
    
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Initialize database
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()
        
        # Test with a simple PDF (if available)
        pdf_dir = Path(__file__).parent.parent.parent.parent / "NC Music Standards and Resources"
        test_pdfs = list(pdf_dir.glob("*.pdf"))
        
        if test_pdfs:
            # Use the first available PDF for testing
            test_pdf = test_pdfs[0]
            
            # Parse the PDF
            parser = NCStandardsParser()
            parsed_standards = parser.parse_standards_document(str(test_pdf))
            
            # Convert to models
            standards, objectives = parser.normalize_to_models(test_pdf.name)
            
            # Save to database
            with db_manager.get_connection() as conn:
                for standard in standards:
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
                
                for objective in objectives:
                    conn.execute(
                        """INSERT INTO objectives (objective_id, standard_id, objective_text)
                           VALUES (?, ?, ?)""",
                        (objective.objective_id, objective.standard_id, objective.objective_text)
                    )
                
                conn.commit()
            
            # Verify data was saved
            with db_manager.get_connection() as conn:
                standard_count = conn.execute("SELECT COUNT(*) FROM standards").fetchone()[0]
                objective_count = conn.execute("SELECT COUNT(*) FROM objectives").fetchone()[0]
                
                assert standard_count == len(standards)
                assert objective_count == len(objectives)
            
            # Get statistics
            stats = parser.get_statistics()
            assert stats["total_standards"] == len(standards)
            assert stats["total_objectives"] == len(objectives)
        
        else:
            # Skip test if no PDFs available
            import pytest
            pytest.skip("No PDF files available for testing")
    
    finally:
        # Clean up temporary database
        if os.path.exists(db_path):
            os.unlink(db_path)