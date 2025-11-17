"""API contract tests for normalized endpoints"""

import os
import sys
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from backend.api.main import app

class TestApiContractsNormalized:
    """Comprehensive API contract tests for normalized endpoints"""

    def test_sessions_api_contract(self):
        """Test sessions API returns properly normalized responses"""
        client = TestClient(app)

        with patch('backend.api.dependencies.get_current_user') as mock_auth:
            # Mock authentication
            mock_user = Mock()
            mock_user.id = "test-user"
            mock_auth.return_value = mock_user

            # Mock repositories
            with patch('backend.repositories.session_repository.SessionRepository') as mock_session_repo_class, \
                 patch('backend.repositories.standards_repository.StandardsRepository') as mock_standards_repo_class:

                # Setup mocks
                mock_session_repo = Mock()
                mock_session_repo_class.return_value = mock_session_repo

                mock_standards_repo = Mock()
                mock_standards_repo_class.return_value = mock_standards_repo

                # Create test session with comma-separated fields
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

                # Mock standard
                mock_standard = Mock()
                mock_standard.standard_id = "K.CC.1"
                mock_standard.grade_level = "Kindergarten"
                mock_standard.strand_code = "CC"
                mock_standard.strand_name = "Counting and Cardinality"
                mock_standard.standard_text = "Know number names and the count sequence"
                mock_standards_repo.get_standard_by_id.return_value = mock_standard

                # Use real normalization helpers
                from backend.repositories.session_repository import SessionRepository
                real_session_repo = SessionRepository()
                mock_session_repo.parse_selected_standards_list = real_session_repo.parse_selected_standards_list
                mock_session_repo.parse_selected_objectives_list = real_session_repo.parse_selected_objectives_list
                mock_session_repo.normalize_standards_for_response = real_session_repo.normalize_standards_for_response
                mock_session_repo.normalize_objectives_for_response = real_session_repo.normalize_objectives_for_response

                # Test session creation
                response = client.post(
                    "/api/sessions",
                    json={
                        "grade_level": "Grade 3",
                        "strand_code": "Connect",
                        "standard_ids": ["K.CC.1", "K.CC.2", "K.CC.3"],
                        "selectedObjectives": ["obj1", "obj2", "obj3"],
                        "additionalContext": "Test context"
                    }
                )

                assert response.status_code == 200
                data = response.json()

                # Verify camelCase field names
                expected_camelcase_fields = [
                    "gradeLevel", "strandCode", "selectedStandards",
                    "selectedObjectives", "additionalContext",
                    "createdAt", "updatedAt"
                ]

                for field in expected_camelcase_fields:
                    assert field in data, f"Missing camelCase field: {field}"

                # Verify array types
                assert isinstance(data["selectedStandards"], list), "selectedStandards should be array"
                assert isinstance(data["selectedObjectives"], list), "selectedObjectives should be array"

                # Verify standards structure
                if len(data["selectedStandards"]) > 0:
                    standard = data["selectedStandards"][0]
                    expected_standard_fields = ["id", "code", "grade", "strandCode", "strandName", "title", "description"]
                    for field in expected_standard_fields:
                        assert field in standard, f"Missing field in normalized standard: {field}"

                print("✅ Sessions API contract test passed")

    def test_drafts_api_contract(self):
        """Test drafts API returns properly normalized responses"""
        client = TestClient(app)

        with patch('backend.api.dependencies.get_current_user') as mock_auth:
            # Mock authentication
            mock_user = Mock()
            mock_user.id = "test-user"
            mock_auth.return_value = mock_user

            # Mock repositories
            with patch('backend.repositories.lesson_repository.LessonRepository') as mock_lesson_repo_class, \
                 patch('backend.repositories.session_repository.SessionRepository') as mock_session_repo_class:

                # Setup mocks
                mock_lesson_repo = Mock()
                mock_lesson_repo_class.return_value = mock_lesson_repo

                mock_session_repo = Mock()
                mock_session_repo_class.return_value = mock_session_repo

                # Create test lesson with metadata containing comma-separated fields
                from backend.auth import Lesson
                from datetime import datetime
                test_lesson = Lesson(
                    id="test-lesson-123",
                    session_id="test-session-123",
                    user_id="test-user",
                    title="Test Lesson",
                    content="Test content",
                    metadata=json.dumps({
                        "grade_level": "Grade 3",
                        "strand_code": "Connect",
                        "selected_standards": "K.CC.1,K.CC.2",
                        "selected_objectives": "obj1,obj2"
                    }),
                    processing_mode="cloud",
                    is_draft=True,
                    created_at=datetime(2025, 11, 16, 10, 0, 0),
                    updated_at=datetime(2025, 11, 16, 10, 30, 0)
                )

                mock_lesson_repo.list_lessons_for_user.return_value = [test_lesson]

                # Mock session
                from backend.auth import Session
                test_session = Session(
                    id="test-session-123",
                    user_id="test-user",
                    grade_level="Grade 3",
                    strand_code="Connect",
                    selected_standards="K.CC.1,K.CC.2",
                    selected_objectives="obj1,obj2",
                    created_at=datetime(2025, 11, 16, 9, 0, 0),
                    updated_at=datetime(2025, 11, 16, 9, 30, 0)
                )
                mock_session_repo.get_session.return_value = test_session

                # Use real normalization helpers
                from backend.repositories.lesson_repository import LessonRepository
                real_lesson_repo = LessonRepository()
                mock_lesson_repo.parse_metadata = real_lesson_repo.parse_metadata
                mock_lesson_repo.normalize_lesson_for_response = real_lesson_repo.normalize_lesson_for_response

                # Test drafts listing
                response = client.get("/api/drafts")
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list), "Drafts list should be an array"
                assert len(data) >= 1, "Should have at least one draft"

                # Check first draft structure
                draft = data[0]

                # Verify camelCase field names
                expected_camelcase_fields = [
                    "grade", "strand", "standard", "selectedStandards",
                    "selectedObjectives", "createdAt", "updatedAt"
                ]

                for field in expected_camelcase_fields:
                    assert field in draft, f"Missing camelCase field: {field}"

                # Verify array types for normalized fields
                if draft["selectedStandards"] is not None:
                    assert isinstance(draft["selectedStandards"], list), "selectedStandards should be array"

                if draft["selectedObjectives"] is not None:
                    assert isinstance(draft["selectedObjectives"], list), "selectedObjectives should be array"

                print("✅ Drafts API contract test passed")

    def test_presentations_api_contract(self):
        """Test presentations API returns properly normalized responses"""
        client = TestClient(app)

        with patch('backend.api.dependencies.get_current_user') as mock_auth:
            # Mock authentication
            mock_user = Mock()
            mock_user.id = "test-user"
            mock_auth.return_value = mock_user

            # Mock presentation service
            with patch('backend.services.presentation_service.PresentationService') as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service

                # Mock presentation status
                mock_service.get_presentation_status.return_value = {
                    "id": "test-presentation-123",
                    "presentation_id": "test-presentation-123",
                    "lesson_id": "test-lesson-123",
                    "lesson_revision": 1,
                    "version": "1.0",
                    "status": "completed",
                    "style": "default",
                    "slide_count": 5,
                    "created_at": "2025-11-16T10:00:00",
                    "updated_at": "2025-11-16T10:30:00",
                    "has_exports": True
                }

                # Test presentation status
                response = client.get("/api/presentations/test-lesson-123/status")
                assert response.status_code == 200
                data = response.json()

                # Verify structure (should now be camelCase due to CamelModel inheritance)
                expected_fields = ["id", "presentationId", "lessonId", "lessonRevision",
                                  "version", "status", "style", "slideCount",
                                  "createdAt", "updatedAt", "hasExports"]

                for field in expected_fields:
                    assert field in data, f"Missing camelCase field: {field}"

                print("✅ Presentations API contract test passed")

    def test_field_normalization_edge_cases(self):
        """Test field normalization handles edge cases correctly"""
        from backend.repositories.session_repository import SessionRepository
        from backend.repositories.lesson_repository import LessonRepository
        from backend.auth import Session, Lesson
        from datetime import datetime

        # Test empty/null fields
        session_repo = SessionRepository()
        empty_session = Session(
            id="empty-session",
            user_id="test-user",
            selected_standards=None,
            selected_objectives=None,
            created_at=None,
            updated_at=None
        )

        # Should return empty arrays
        standards = session_repo.parse_selected_standards_list(empty_session)
        objectives = session_repo.parse_selected_objectives_list(empty_session)
        assert standards == [], "Empty standards should return empty array"
        assert objectives == [], "Empty objectives should return empty array"

        # Test whitespace handling
        whitespace_session = Session(
            id="whitespace-session",
            user_id="test-user",
            selected_standards="K.CC.1, K.CC.2 , K.CC.3",
            selected_objectives=" obj1 ,obj2, obj3 ",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        standards = session_repo.parse_selected_standards_list(whitespace_session)
        objectives = session_repo.parse_selected_objectives_list(whitespace_session)
        assert standards == ["K.CC.1", "K.CC.2", "K.CC.3"], "Should handle whitespace correctly"
        assert objectives == ["obj1", "obj2", "obj3"], "Should handle whitespace correctly"

        # Test lesson metadata normalization
        lesson_repo = LessonRepository()
        lesson_with_metadata = Lesson(
            id="metadata-lesson",
            session_id="test-session",
            user_id="test-user",
            title="Test",
            content="Test content",
            metadata=json.dumps({
                "selected_standards": "K.CC.1,K.CC.2",
                "selected_objectives": ["obj1", "obj2"]  # Mix of string and array
            }),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        normalized = lesson_repo.normalize_lesson_for_response(lesson_with_metadata)
        assert normalized["selectedStandards"] == ["K.CC.1", "K.CC.2"], "Should normalize metadata standards"
        assert normalized["selectedObjectives"] == ["obj1", "obj2"], "Should preserve array objectives"

        print("✅ Field normalization edge cases test passed")

    def run_all_tests(self):
        """Run all API contract tests"""
        try:
            self.test_sessions_api_contract()
            self.test_drafts_api_contract()
            self.test_presentations_api_contract()
            self.test_field_normalization_edge_cases()

            print("\n🎉 All API contract tests passed!")
            return True
        except Exception as e:
            print(f"\n❌ API contract test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    test_runner = TestApiContractsNormalized()
    success = test_runner.run_all_tests()
    sys.exit(0 if success else 1)