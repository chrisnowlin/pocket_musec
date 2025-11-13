"""Tests for file linking integration"""

def test_file_linking_database_schema():
    """Test that file_id columns are properly added to database schema"""
    from backend.repositories.database import DatabaseManager
    from backend.repositories.migrations import MigrationManager
    
    # Use a temporary file database for testing
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        tmp_db_path = tmp_file.name
    
    try:
        db_manager = DatabaseManager(tmp_db_path)
        migration_manager = MigrationManager(db_path=tmp_db_path)
        
        # Run all migrations including the new file linking migration
        migration_manager.migrate()
        
        with db_manager.get_connection() as conn:
            # Check file_id columns exist in all relevant tables
            cursor = conn.execute("PRAGMA table_info(standards)")
            columns = [row[1] for row in cursor.fetchall()]
            assert 'file_id' in columns, "file_id column missing from standards table"
            
            cursor = conn.execute("PRAGMA table_info(objectives)")
            columns = [row[1] for row in cursor.fetchall()]
            assert 'file_id' in columns, "file_id column missing from objectives table"
            
            cursor = conn.execute("PRAGMA table_info(standard_embeddings)")
            columns = [row[1] for row in cursor.fetchall()]
            assert 'file_id' in columns, "file_id column missing from standard_embeddings table"
            
            cursor = conn.execute("PRAGMA table_info(objective_embeddings)")
            columns = [row[1] for row in cursor.fetchall()]
            assert 'file_id' in columns, "file_id column missing from objective_embeddings table"
            
            cursor = conn.execute("PRAGMA table_info(citations)")
            columns = [row[1] for row in cursor.fetchall()]
            assert 'file_id' in columns, "file_id column missing from citations table"
            
            # Check foreign key constraints
            cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='standards'")
            table_sql = cursor.fetchone()[0]
            assert 'FOREIGN KEY (file_id) REFERENCES uploaded_files(file_id)' in table_sql
            
            # Check file_id indexes exist
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%file_id%'")
            indexes = cursor.fetchall()
            assert len(indexes) > 0, "No file_id indexes found"
            
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_db_path):
            os.unlink(tmp_db_path)


def test_standards_repository_file_id_support():
    """Test that StandardsRepository supports file_id operations"""
    from backend.repositories.database import DatabaseManager
    from backend.repositories.migrations import MigrationManager
    from backend.repositories.standards_repository import StandardsRepository
    from backend.repositories.models import Standard
    
    # Use a temporary file database for testing
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        tmp_db_path = tmp_file.name
    
    try:
        # Initialize database with migrations
        db_manager = DatabaseManager(tmp_db_path)
        migration_manager = MigrationManager(db_path=tmp_db_path)
        migration_manager.migrate()
        
        # Test repository operations with file_id
        standards_repo = StandardsRepository(db_manager=db_manager)
        
        # Create a test standard with file_id
        test_file_id = "test-file-123"
        standard = Standard(
            standard_id="TEST.MU.1.1",
            grade_level="1",
            strand_code="CR",
            strand_name="Creative Rhythm",
            strand_description="Test strand",
            standard_text="Test standard text",
            file_id=test_file_id
        )
        
        # Since StandardsRepository doesn't have create_standard method,
        # we'll test the file_id functionality by inserting directly
        # and verifying the repository methods handle file_id correctly
        
        # Insert test standard directly into database
        conn = db_manager.get_connection()
        try:
            conn.execute("""
                INSERT INTO standards (
                    standard_id, grade_level, strand_code, strand_name,
                    strand_description, standard_text, source_document, file_id,
                    ingestion_date, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                standard.standard_id,
                standard.grade_level,
                standard.strand_code,
                standard.strand_name,
                standard.strand_description,
                standard.standard_text,
                "test_document.txt",
                standard.file_id,
                "2023-01-01",
                "1.0"
            ))
            conn.commit()
        finally:
            conn.close()
        
        # Test that get_standard_by_id handles file_id correctly
        retrieved_standard = standards_repo.get_standard_by_id("TEST.MU.1.1")
        assert retrieved_standard is not None
        assert retrieved_standard.file_id == test_file_id
        
        # Test file_id-based queries
        standards_by_file = standards_repo.get_standards_by_file_id(test_file_id)
        assert len(standards_by_file) == 1
        assert standards_by_file[0].file_id == test_file_id
        
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_db_path):
            os.unlink(tmp_db_path)


def test_embeddings_file_id_support():
    """Test that embeddings system supports file_id operations"""
    from backend.repositories.database import DatabaseManager
    from backend.repositories.migrations import MigrationManager
    from backend.repositories.standards_repository import StandardsRepository
    from backend.repositories.models import Standard, Objective
    from backend.llm.embeddings import StandardsEmbeddings
    
    # Use a temporary file database for testing
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        tmp_db_path = tmp_file.name
    
    try:
        # Initialize database with migrations
        db_manager = DatabaseManager(tmp_db_path)
        migration_manager = MigrationManager(db_path=tmp_db_path)
        migration_manager.migrate()
        
        # Create test data
        standards_repo = StandardsRepository(db_manager=db_manager)
        test_file_id = "test-file-456"
        
        standard = Standard(
            standard_id="TEST.MU.2.1",
            grade_level="2",
            strand_code="CR",
            strand_name="Creative Rhythm",
            strand_description="Test strand",
            standard_text="Test standard text",
            file_id=test_file_id
        )
        
        # Insert test standard directly into database
        conn = db_manager.get_connection()
        try:
            conn.execute("""
                INSERT INTO standards (
                    standard_id, grade_level, strand_code, strand_name,
                    strand_description, standard_text, source_document, file_id,
                    ingestion_date, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                standard.standard_id,
                standard.grade_level,
                standard.strand_code,
                standard.strand_name,
                standard.strand_description,
                standard.standard_text,
                "test_document.txt",
                standard.file_id,
                "2023-01-01",
                "1.0"
            ))
            
            objective = Objective(
                objective_id="TEST.OBJ.2.1.1",
                standard_id="TEST.MU.2.1",
                objective_text="Test objective text",
                file_id=test_file_id
            )
            
            # Insert objective directly
            conn.execute("""
                INSERT INTO objectives (
                    objective_id, standard_id, objective_text, file_id
                ) VALUES (?, ?, ?, ?)
            """, (
                objective.objective_id,
                objective.standard_id,
                objective.objective_text,
                objective.file_id
            ))
            
            conn.commit()
        finally:
            conn.close()
        
        # Test embeddings with file_id
        # Create embeddings manager with the test database
        from unittest.mock import patch
        
        # Create embeddings manager that uses our test database
        embeddings_manager = StandardsEmbeddings()
        # Override its database manager to use our test database
        embeddings_manager.db_manager = db_manager
        # Reinitialize tables to ensure they exist in our test database
        embeddings_manager._init_embeddings_table()
        
        test_embedding = [0.1] * 1536  # Mock embedding vector
        
        # Store embedding with file_id
        embeddings_manager.store_objective_embedding(objective, test_embedding, test_file_id)
        
        # Retrieve embedding with file_id
        embedding_with_file = embeddings_manager.get_objective_embedding_with_file("TEST.OBJ.2.1.1")
        assert embedding_with_file is not None
        retrieved_embedding, retrieved_file_id = embedding_with_file
        assert retrieved_file_id == test_file_id
        
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_db_path):
            os.unlink(tmp_db_path)


def test_citations_file_id_support():
    """Test that citation system supports file_id operations"""
    from backend.repositories.database import DatabaseManager
    from backend.repositories.migrations import MigrationManager
    from backend.citations.citation_repository import CitationRepository
    
    # Use a temporary file database for testing
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        tmp_db_path = tmp_file.name
    
    try:
        # Initialize database with migrations
        db_manager = DatabaseManager(tmp_db_path)
        migration_manager = MigrationManager(db_path=tmp_db_path)
        migration_manager.migrate()
        
        # Test citations with file_id
        citation_repo = CitationRepository(db_path=tmp_db_path)
        test_file_id = "test-file-789"
        
        citation = citation_repo.save_citation(
            lesson_id="test-lesson-123",
            source_type="standard",
            source_id="TEST.MU.1.1",
            source_title="Test Standard",
            citation_number=1,
            file_id=test_file_id
        )
        
        assert citation.file_id == test_file_id
        
        # Test file_id-based citation queries
        citations_by_file = citation_repo.get_citations_by_file_id(test_file_id)
        assert len(citations_by_file) == 1
        assert citations_by_file[0].file_id == test_file_id
        
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_db_path):
            os.unlink(tmp_db_path)