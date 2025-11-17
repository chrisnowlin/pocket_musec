"""Simple test for sessions normalization helpers"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock
from backend.repositories.session_repository import SessionRepository
from backend.repositories.standards_repository import StandardsRepository
from backend.auth import Session

def test_session_normalization_helpers():
    """Test that session repository normalization helpers work correctly"""

    # Create session repository
    session_repo = SessionRepository()

    # Create a test session with comma-separated fields
    test_session = Session(
        id="test-session-123",
        user_id="test-user",
        grade_level="Grade 3",
        strand_code="Connect",
        selected_standards="K.CC.1,K.CC.2,K.CC.3",
        selected_objectives="obj1,obj2,obj3",
        additional_context="Test context",
        created_at="2025-11-16T10:00:00",
        updated_at="2025-11-16T10:30:00"
    )

    # Test standards parsing
    standards_list = session_repo.parse_selected_standards_list(test_session)
    print("✅ Standards parsing:", standards_list)
    assert standards_list == ["K.CC.1", "K.CC.2", "K.CC.3"]

    # Test objectives parsing
    objectives_list = session_repo.parse_selected_objectives_list(test_session)
    print("✅ Objectives parsing:", objectives_list)
    assert objectives_list == ["obj1", "obj2", "obj3"]

    # Test standards normalization with mocked standards repo
    mock_standards_repo = Mock()
    mock_standard = Mock()
    mock_standard.standard_id = "K.CC.1"
    mock_standard.grade_level = "Kindergarten"
    mock_standard.strand_code = "CC"
    mock_standard.strand_name = "Counting and Cardinality"
    mock_standard.standard_text = "Know number names and the count sequence"

    mock_standards_repo.get_standard_by_id.return_value = mock_standard

    normalized_standards = session_repo.normalize_standards_for_response(test_session, mock_standards_repo)
    print("✅ Normalized standards count:", len(normalized_standards))

    # Should have 3 normalized standards (same mock returned 3 times)
    assert len(normalized_standards) == 3

    # Check structure of first standard
    first_standard = normalized_standards[0]
    assert first_standard["id"] == "K.CC.1"
    assert first_standard["code"] == "K.CC.1"
    assert first_standard["grade"] == "Kindergarten"
    assert first_standard["strandCode"] == "CC"
    assert first_standard["strandName"] == "Counting and Cardinality"
    assert first_standard["title"] == "Know number names and the count sequence"
    assert first_standard["description"] == "Know number names and the count sequence"

    # Test objectives normalization
    normalized_objectives = session_repo.normalize_objectives_for_response(test_session)
    print("✅ Normalized objectives:", normalized_objectives)
    assert normalized_objectives == ["obj1", "obj2", "obj3"]

    # Test conversion back to strings
    standards_string = session_repo.convert_standards_list_to_string(standards_list)
    assert standards_string == "K.CC.1,K.CC.2,K.CC.3"

    objectives_string = session_repo.convert_objectives_list_to_string(objectives_list)
    assert objectives_string == "obj1,obj2,obj3"

    # Test empty conversions
    assert session_repo.convert_standards_list_to_string([]) is None
    assert session_repo.convert_objectives_list_to_string([]) is None

    print("✅ All session normalization helpers work correctly!")
    return True

if __name__ == "__main__":
    try:
        test_session_normalization_helpers()
        print("Simple normalization test passed!")
    except Exception as e:
        print(f"Simple normalization test failed: {e}")
        sys.exit(1)