#!/usr/bin/env python3
"""
Test script to verify file linking integration
"""

import os
import sys
import tempfile
import sqlite3
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from backend.repositories.database import DatabaseManager
from backend.repositories.migrations import MigrationManager
from backend.repositories.models import Standard, Objective
from backend.repositories.standards_repository import StandardsRepository
from backend.llm.embeddings import StandardsEmbeddings
from backend.citations.citation_repository import CitationRepository
from auth.models import Citation as CitationModel
from backend.utils.file_storage import FileStorageManager


def test_file_linking_integration():
    """Test that file_id columns are properly added and functional"""

    print("🧪 Testing File Linking Integration...")

    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
        temp_db_path = temp_db.name

    try:
        # Initialize database with migrations
        db_manager = DatabaseManager(db_path=temp_db_path)
        migration_manager = MigrationManager(db_path=temp_db_path)

        # Run all migrations including the new file linking migration
        migration_manager.run_migrations()

        print("✅ Database migrations completed successfully")

        # Verify file_id columns exist in all tables
        conn = db_manager.get_connection()

        # Check standards table
        cursor = conn.execute("PRAGMA table_info(standards)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "file_id" in columns, "file_id column missing from standards table"
        print("✅ file_id column exists in standards table")

        # Check objectives table
        cursor = conn.execute("PRAGMA table_info(objectives)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "file_id" in columns, "file_id column missing from objectives table"
        print("✅ file_id column exists in objectives table")

        # Check standard_embeddings table
        cursor = conn.execute("PRAGMA table_info(standard_embeddings)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "file_id" in columns, (
            "file_id column missing from standard_embeddings table"
        )
        print("✅ file_id column exists in standard_embeddings table")

        # Check objective_embeddings table
        cursor = conn.execute("PRAGMA table_info(objective_embeddings)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "file_id" in columns, (
            "file_id column missing from objective_embeddings table"
        )
        print("✅ file_id column exists in objective_embeddings table")

        # Check citations table
        cursor = conn.execute("PRAGMA table_info(citations)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "file_id" in columns, "file_id column missing from citations table"
        print("✅ file_id column exists in citations table")

        # Test foreign key constraints
        cursor = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='standards'"
        )
        table_sql = cursor.fetchone()[0]
        assert (
            "FOREIGN KEY (file_id) REFERENCES uploaded_files(file_id)" in table_sql
        ), "Foreign key constraint missing for standards.file_id"
        print("✅ Foreign key constraint exists for standards.file_id")

        # Test indexes
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%file_id%'"
        )
        indexes = cursor.fetchall()
        assert len(indexes) > 0, "No file_id indexes found"
        print(f"✅ Found {len(indexes)} file_id indexes")

        conn.close()

        # Test repositories work with file_id
        standards_repo = StandardsRepository(db_path=temp_db_path)

        # Create a test standard with file_id
        test_file_id = "test-file-123"
        standard = Standard(
            standard_id="TEST.MU.1.1",
            grade_level="1",
            strand_code="CR",
            strand_name="Creative Rhythm",
            strand_description="Test strand",
            standard_text="Test standard text",
            file_id=test_file_id,
        )

        # Save standard (this will test the INSERT with file_id)
        standards_repo.create_standard(standard)
        print("✅ Standard saved with file_id")

        # Retrieve standard (this will test the SELECT with file_id)
        retrieved_standard = standards_repo.get_standard_by_id("TEST.MU.1.1")
        assert retrieved_standard is not None, "Failed to retrieve standard"
        assert retrieved_standard.file_id == test_file_id, (
            "file_id not preserved in retrieval"
        )
        print("✅ Standard retrieved with correct file_id")

        # Test file_id-based queries
        standards_by_file = standards_repo.get_standards_by_file_id(test_file_id)
        assert len(standards_by_file) == 1, "Failed to retrieve standards by file_id"
        assert standards_by_file[0].file_id == test_file_id, (
            "Incorrect file_id in retrieved standards"
        )
        print("✅ Standards retrieved by file_id successfully")

        # Test embeddings with file_id
        embeddings_manager = StandardsEmbeddings()

        # Create a mock embedding
        test_embedding = [0.1] * 1536  # Mock embedding vector

        # Store embedding with file_id
        objective = Objective(
            objective_id="TEST.OBJ.1.1.1",
            standard_id="TEST.MU.1.1",
            objective_text="Test objective text",
            file_id=test_file_id,
        )

        embeddings_manager.store_objective_embedding(
            objective, test_embedding, test_file_id
        )
        print("✅ Objective embedding stored with file_id")

        # Retrieve embedding with file_id
        embedding_with_file = embeddings_manager.get_objective_embedding_with_file(
            "TEST.OBJ.1.1.1"
        )
        assert embedding_with_file is not None, (
            "Failed to retrieve objective embedding with file_id"
        )
        retrieved_embedding, retrieved_file_id = embedding_with_file
        assert retrieved_file_id == test_file_id, (
            "file_id not correctly retrieved with embedding"
        )
        print("✅ Objective embedding retrieved with correct file_id")

        # Test citations with file_id
        citation_repo = CitationRepository(db_path=temp_db_path)

        citation = citation_repo.save_citation(
            lesson_id="test-lesson-123",
            source_type="standard",
            source_id="TEST.MU.1.1",
            source_title="Test Standard",
            citation_number=1,
            file_id=test_file_id,
        )
        print("✅ Citation saved with file_id")

        assert citation.file_id == test_file_id, "file_id not preserved in citation"
        print("✅ Citation retrieved with correct file_id")

        # Test file_id-based citation queries
        citations_by_file = citation_repo.get_citations_by_file_id(test_file_id)
        assert len(citations_by_file) == 1, "Failed to retrieve citations by file_id"
        assert citations_by_file[0].file_id == test_file_id, (
            "Incorrect file_id in retrieved citations"
        )
        print("✅ Citations retrieved by file_id successfully")

        print("\n🎉 All file linking integration tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ File linking integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Clean up temporary database
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
            print("🧹 Cleaned up temporary database")


if __name__ == "__main__":
    success = test_file_linking_integration()
    sys.exit(0 if success else 1)
