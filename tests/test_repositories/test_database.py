"""Tests for database management"""

def test_database_manager_initialization():
    """Test that DatabaseManager can be created and initialized"""
    from backend.repositories.database import DatabaseManager
    
    # Use in-memory database for testing
    db_manager = DatabaseManager(":memory:")
    assert db_manager is not None
    assert not db_manager.database_exists()  # In-memory doesn't exist as file
    
    # Test initialization
    db_manager.initialize_database()
    
    # Test connection
    conn = db_manager.get_connection()
    assert conn is not None
    conn.close()


def test_database_schema_creation():
    """Test that database schema is created correctly"""
    from backend.repositories.database import DatabaseManager
    
    # Use a temporary file database instead of in-memory
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        tmp_db_path = tmp_file.name
    
    try:
        db_manager = DatabaseManager(tmp_db_path)
        db_manager.initialize_database()
        
        with db_manager.get_connection() as conn:
            # Check tables exist
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [row[0] for row in tables]
            
            assert "standards" in table_names
            assert "objectives" in table_names
            
            # Check indexes exist
            indexes = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            index_names = [row[0] for row in indexes]
            
            assert "idx_grade_level" in index_names
            assert "idx_strand_code" in index_names
            assert "idx_standard_objectives" in index_names
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_db_path):
            os.unlink(tmp_db_path)