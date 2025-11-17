"""Integration test for sessions API field normalization"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from backend.api.main import app

def test_sessions_api_returns_arrays():
    """Test that sessions API endpoint returns normalized arrays instead of comma-separated strings"""

    client = TestClient(app)

    # Mock authentication
    with patch('backend.api.dependencies.get_current_user') as mock_auth:
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_auth.return_value = mock_user

        # Mock repositories
        with patch('backend.repositories.session_repository.SessionRepository') as mock_session_repo_class, \
             patch('backend.repositories.standards_repository.StandardsRepository') as mock_standards_repo_class:

            # Setup session repository mock
            mock_session_repo = Mock()
            mock_session_repo_class.return_value = mock_session_repo

            # Create a test session with comma-separated fields
            from backend.auth import Session
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

            mock_session_repo.create_session.return_value = test_session
            mock_session_repo.get_session.return_value = test_session

            # Setup standards repository mock
            mock_standards_repo = Mock()
            mock_standards_repo_class.return_value = mock_standards_repo

            mock_standard = Mock()
            mock_standard.standard_id = "K.CC.1"
            mock_standard.grade_level = "Kindergarten"
            mock_standard.strand_code = "CC"
            mock_standard.strand_name = "Counting and Cardinality"
            mock_standard.standard_text = "Know number names and the count sequence"
            mock_standards_repo.get_standard_by_id.return_value = mock_standard

            # Test create session endpoint
            response = client.post(
                "/api/sessions",
                json={
                    "grade_level": "Grade 3",
                    "strand_code": "Connect",
                    "standard_ids": ["K.CC.1", "K.CC.2", "K.CC.3"],
                    "selected_objectives": ["obj1", "obj2", "obj3"],
                    "additional_context": "Test context"
                }
            )

            assert response.status_code == 200

            session_data = response.json()
            print("Debug: session_data:", session_data)

            # Verify that selectedStandards is returned as array (camelCase for frontend)
            assert "selectedStandards" in session_data, f"selectedStandards not found in keys: {session_data.keys()}"
            assert isinstance(session_data["selectedStandards"], list), f"expected list, got {type(session_data['selectedStandards'])}"
            assert len(session_data["selectedStandards"]) == 3

            # Verify that selectedObjectives is returned as array (camelCase for frontend)
            assert isinstance(session_data["selectedObjectives"], list), f"expected list, got {type(session_data['selectedObjectives'])}"
            assert session_data["selectedObjectives"] == ["obj1", "obj2", "obj3"]

            # Verify the structure of normalized standards
            standard = session_data["selectedStandards"][0]
            assert "id" in standard
            assert "code" in standard
            assert "grade" in standard
            assert "strandCode" in standard
            assert "strandName" in standard
            assert "title" in standard
            assert "description" in standard

            print("✅ Session API returns properly normalized arrays")
            return True

if __name__ == "__main__":
    try:
        test_sessions_api_returns_arrays()
        print("Integration test passed!")
    except Exception as e:
        print(f"Integration test failed: {e}")
        sys.exit(1)