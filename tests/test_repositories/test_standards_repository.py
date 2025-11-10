"""Tests for StandardsRepository"""

import pytest
import tempfile
import os
from pathlib import Path

from backend.repositories.database import DatabaseManager
from backend.repositories.standards_repository import StandardsRepository
from backend.repositories.models import Standard, Objective


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_database()
    
    # Insert test data
    conn = db_manager.get_connection()
    try:
        # Insert test standards
        standards_data = [
            ('K.MH.CN.1', 'Kindergarten', 'CN', 'Musical History', 'Understanding music in historical contexts', 'Demonstrate awareness of music in daily life', 'test_doc.pdf', '2024-01-01', '1.0'),
            ('K.MH.CR.1', 'Kindergarten', 'CR', 'Cultural Relevance', 'Understanding music in cultural contexts', 'Recognize music from different cultures', 'test_doc.pdf', '2024-01-01', '1.0'),
            ('1.MH.CN.1', '1st Grade', 'CN', 'Musical History', 'Understanding music in historical contexts', 'Identify musical instruments from different periods', 'test_doc.pdf', '2024-01-01', '1.0'),
            ('1.MH.PR.1', '1st Grade', 'PR', 'Performance', 'Musical performance skills', 'Perform simple rhythmic patterns', 'test_doc.pdf', '2024-01-01', '1.0'),
        ]
        
        conn.executemany("""
            INSERT INTO standards 
            (standard_id, grade_level, strand_code, strand_name, strand_description, standard_text, source_document, ingestion_date, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, standards_data)
        
        # Insert test objectives
        objectives_data = [
            ('K.MH.CN.1.1', 'K.MH.CN.1', 'Identify music heard at home and school'),
            ('K.MH.CN.1.2', 'K.MH.CN.1', 'Recognize music in community settings'),
            ('K.MH.CR.1.1', 'K.MH.CR.1', 'Listen to music from different cultures'),
            ('1.MH.CN.1.1', '1.MH.CN.1', 'Identify instruments by sight and sound'),
            ('1.MH.PR.1.1', '1.MH.PR.1', 'Clap steady beat'),
            ('1.MH.PR.1.2', '1.MH.PR.1', 'Play simple rhythmic patterns'),
        ]
        
        conn.executemany("""
            INSERT INTO objectives (objective_id, standard_id, objective_text)
            VALUES (?, ?, ?)
        """, objectives_data)
        
        conn.commit()
    finally:
        conn.close()
    
    yield db_manager
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def repository(temp_db):
    """Create StandardsRepository with test database"""
    return StandardsRepository(temp_db)


def test_get_all_standards(repository):
    """Test retrieving all standards"""
    standards = repository.get_all_standards()
    assert len(standards) == 4
    
    # Check that we have the expected standards (order may vary)
    standard_ids = [s.standard_id for s in standards]
    expected_ids = ['K.MH.CN.1', 'K.MH.CR.1', '1.MH.CN.1', '1.MH.PR.1']
    for expected_id in expected_ids:
        assert expected_id in standard_ids
    
    # Check that all standards have required fields
    for standard in standards:
        assert standard.standard_id
        assert standard.grade_level
        assert standard.strand_code
        assert standard.strand_name


def test_get_standards_by_grade(repository):
    """Test filtering standards by grade level"""
    standards = repository.get_standards_by_grade('Kindergarten')
    assert len(standards) == 2
    
    for standard in standards:
        assert standard.grade_level == 'Kindergarten'
    
    # Check specific standards
    standard_ids = [s.standard_id for s in standards]
    assert 'K.MH.CN.1' in standard_ids
    assert 'K.MH.CR.1' in standard_ids


def test_get_standards_by_strand(repository):
    """Test filtering standards by strand code"""
    standards = repository.get_standards_by_strand('CN')
    assert len(standards) == 2
    
    for standard in standards:
        assert standard.strand_code == 'CN'
    
    # Check specific standards
    standard_ids = [s.standard_id for s in standards]
    assert 'K.MH.CN.1' in standard_ids
    assert '1.MH.CN.1' in standard_ids


def test_get_standards_by_grade_and_strand(repository):
    """Test filtering standards by both grade and strand"""
    standards = repository.get_standards_by_grade_and_strand('1st Grade', 'CN')
    assert len(standards) == 1
    
    standard = standards[0]
    assert standard.standard_id == '1.MH.CN.1'
    assert standard.grade_level == '1st Grade'
    assert standard.strand_code == 'CN'


def test_get_standard_by_id(repository):
    """Test retrieving a specific standard by ID"""
    standard = repository.get_standard_by_id('K.MH.CN.1')
    assert standard is not None
    assert standard.standard_id == 'K.MH.CN.1'
    assert standard.grade_level == 'Kindergarten'
    assert standard.strand_code == 'CN'
    
    # Test non-existent standard
    standard = repository.get_standard_by_id('NONEXISTENT')
    assert standard is None


def test_get_objectives_for_standard(repository):
    """Test retrieving objectives for a standard"""
    objectives = repository.get_objectives_for_standard('K.MH.CN.1')
    assert len(objectives) == 2
    
    # Check objective content
    objective_texts = [obj.objective_text for obj in objectives]
    assert 'Identify music heard at home and school' in objective_texts
    assert 'Recognize music in community settings' in objective_texts
    
    # Test standard with no objectives
    objectives = repository.get_objectives_for_standard('NONEXISTENT')
    assert len(objectives) == 0


def test_get_standard_with_objectives(repository):
    """Test retrieving a standard with its objectives"""
    result = repository.get_standard_with_objectives('K.MH.CN.1')
    assert result is not None
    assert result.standard.standard_id == 'K.MH.CN.1'
    assert len(result.objectives) == 2
    
    # Test non-existent standard
    result = repository.get_standard_with_objectives('NONEXISTENT')
    assert result is None


def test_search_standards(repository):
    """Test full-text search of standards"""
    # Search for 'cultural' should find CR strand
    standards = repository.search_standards('cultural')
    assert len(standards) == 1
    assert standards[0].strand_code == 'CR'
    
    # Search for 'performance' should find PR strand
    standards = repository.search_standards('performance')
    assert len(standards) == 1
    assert standards[0].strand_code == 'PR'
    
    # Search for 'musical' should find standards with 'musical' in text
    standards = repository.search_standards('musical')
    assert len(standards) == 3  # Only those with 'musical' in their text fields


def test_get_grade_levels(repository):
    """Test retrieving all grade levels"""
    grades = repository.get_grade_levels()
    assert len(grades) == 2
    assert 'Kindergarten' in grades
    assert '1st Grade' in grades


def test_get_strand_codes(repository):
    """Test retrieving all strand codes"""
    strands = repository.get_strand_codes()
    assert len(strands) == 3  # CN, CR, PR from test data
    assert 'CN' in strands
    assert 'CR' in strands
    assert 'PR' in strands


def test_get_strand_info(repository):
    """Test retrieving strand information"""
    strand_info = repository.get_strand_info()
    assert len(strand_info) == 3  # CN, CR, PR from test data
    
    # Check CN strand info
    cn_info = strand_info['CN']
    assert cn_info['name'] == 'Musical History'
    assert 'historical' in cn_info['description'].lower()
    
    # Check CR strand info
    cr_info = strand_info['CR']
    assert cr_info['name'] == 'Cultural Relevance'
    assert 'cultural' in cr_info['description'].lower()


def test_get_standards_count(repository):
    """Test counting standards"""
    count = repository.get_standards_count()
    assert count == 4


def test_get_objectives_count(repository):
    """Test counting objectives"""
    count = repository.get_objectives_count()
    assert count == 6


def test_caching_functionality(repository):
    """Test that caching works for frequently accessed data"""
    # First call should populate cache
    grades1 = repository.get_grade_levels()
    assert len(grades1) == 2
    
    # Second call should use cache (same object)
    grades2 = repository.get_grade_levels()
    assert grades1 is grades2  # Same object from cache
    
    # Clear cache and verify it's repopulated
    repository.clear_cache()
    grades3 = repository.get_grade_levels()
    assert grades1 is not grades3  # Different object after cache clear
    assert grades1 == grades3  # But same content
    
    # Test strand info caching
    strand_info1 = repository.get_strand_info()
    strand_info2 = repository.get_strand_info()
    assert strand_info1 is strand_info2  # Same object from cache
    
    repository.clear_cache()
    strand_info3 = repository.get_strand_info()
    assert strand_info1 is not strand_info3  # Different object after cache clear
    assert strand_info1 == strand_info3  # But same content