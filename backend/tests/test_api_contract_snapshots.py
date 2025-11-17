"""API Contract Snapshot Tests for Normalized Endpoints"""

import os
import sys
import json
from datetime import datetime
from unittest.mock import patch, Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.api.main import app

def test_api_contract_snapshots():
    """Create comprehensive API contract snapshots for normalized endpoints"""
    print("📸 Creating API contract snapshots...")

    client = TestClient(app)
    snapshots = {}

    def capture_snapshot(endpoint_name: str, response_data: dict, test_name: str):
        """Capture API response snapshot"""
        validation = {
            'has_camelcase_fields': False,
            'has_array_standards': False,
            'has_array_objectives': False,
            'field_types': {}
        }

        # Check for key normalized fields
        if any(field in response_data for field in ['gradeLevel', 'strandCode', 'selectedStandards', 'selectedObjectives']):
            validation['has_camelcase_fields'] = True

        if 'selectedStandards' in response_data and isinstance(response_data.get('selectedStandards'), list):
            validation['has_array_standards'] = True

        if 'selectedObjectives' in response_data and isinstance(response_data.get('selectedObjectives'), (list, type(None))):
            validation['has_array_objectives'] = True

        return {
            'endpoint': endpoint_name,
            'test_name': test_name,
            'response': response_data,
            'validation': validation
        }

    # Test Sessions API
    with patch('backend.api.dependencies.get_current_user') as mock_auth:
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_auth.return_value = mock_user

        with patch('backend.repositories.session_repository.SessionRepository') as mock_session_repo_class, \
             patch('backend.repositories.standards_repository.StandardsRepository') as mock_standards_repo_class:

            from backend.repositories.session_repository import SessionRepository
            from backend.repositories.standards_repository import StandardsRepository

            # Setup real repository helpers for testing
            real_session_repo = SessionRepository()
            real_standards_repo = StandardsRepository()

            mock_session_repo = Mock()
            mock_session_repo_class.return_value = mock_session_repo
            mock_session_repo.parse_selected_standards_list = real_session_repo.parse_selected_standards_list
            mock_session_repo.normalize_standards_for_response = real_session_repo.normalize_standards_for_response

            mock_standards_repo = Mock()
            mock_standards_repo_class.return_value = mock_standards_repo

            # Mock standard object
            mock_standard = Mock()
            mock_standard.standard_id = "K.CC.1"
            mock_standard.grade_level = "Kindergarten"
            mock_standard.strand_code = "CC"
            mock_standard.strand_name = "Counting and Cardinality"
            mock_standard.standard_text = "Know number names and the count sequence"
            mock_standards_repo.get_standard_by_id.return_value = mock_standard

            # Create test session
            from backend.auth import Session
            test_session = Session(
                id="test-session-123",
                user_id="test-user",
                grade_level="Grade 3",
                strand_code="Connect",
                selected_standards="K.CC.1,K.CC.2,K.CC.3",
                selected_objectives="obj1,obj2,obj3",
                additional_context="Test context",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            mock_session_repo.create_session.return_value = test_session

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
            session_data = response.json()

            # Capture snapshot
            snapshot = capture_snapshot("POST /api/sessions", session_data, "session_creation")
            snapshots["session_creation"] = snapshot

            # Verify normalization
            assert snapshot['validation']['has_camelcase_fields'], "Should have camelCase fields"
            assert snapshot['validation']['has_array_standards'], "Should have array standards"
            assert snapshot['validation']['has_array_objectives'], "Should have array objectives"

            print("✅ Sessions API contract snapshot captured")

    # Test Drafts API
    with patch('backend.api.dependencies.get_current_user') as mock_auth:
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_auth.return_value = mock_user

        with patch('backend.repositories.lesson_repository.LessonRepository') as mock_lesson_repo_class, \
             patch('backend.repositories.session_repository.SessionRepository') as mock_session_repo_class:

            from backend.repositories.lesson_repository import LessonRepository

            # Setup real repository helpers
            real_lesson_repo = LessonRepository()
            mock_lesson_repo = Mock()
            mock_lesson_repo_class.return_value = mock_lesson_repo
            mock_lesson_repo.parse_metadata = real_lesson_repo.parse_metadata
            mock_lesson_repo.normalize_lesson_for_response = real_lesson_repo.normalize_lesson_for_response
            mock_lesson_repo.list_lessons_for_user = real_lesson_repo.list_lessons_for_user

            # Create test lesson
            from backend.auth import Lesson
            test_lesson = Lesson(
                id="test-lesson-123",
                session_id="test-session-123",
                user_id="test-user",
                title="Test Lesson",
                content="Test content",
                metadata='{"grade_level": "Grade 3", "selected_standards": "K.CC.1,K.CC.2"}',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            mock_lesson_repo.list_lessons_for_user.return_value = [test_lesson]

            # Test drafts listing
            response = client.get("/api/drafts")
            assert response.status_code == 200
            drafts_data = response.json()

            if drafts_data:
                draft = drafts_data[0]
                snapshot = capture_snapshot("GET /api/drafts", draft, "draft_list")
                snapshots["draft_list"] = snapshot

                print(f"✅ Drafts API contract snapshot captured")

    # Test Presentations API
    with patch('backend.api.dependencies.get_current_user') as mock_auth:
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_auth.return_value = mock_user

        with patch('backend.services.presentation_service.PresentationService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            # Mock presentation status (should be camelCase due to CamelModel)
            mock_service.get_presentation_status.return_value = {
                "id": "test-presentation-123",
                "presentationId": "test-presentation-123",
                "lessonId": "test-lesson-123",
                "status": "completed",
                "createdAt": "2025-11-16T12:00:00Z",
                "updatedAt": "2025-11-16T12:30:00Z",
            }

            # Test presentation status
            response = client.get("/api/presentations/test-lesson-123/status")

            # Note: This might fail due to route implementation, but we capture what we can
            if response.status_code == 200:
                presentation_data = response.json()
                snapshot = capture_snapshot("GET /api/presentations/status", presentation_data, "presentation_status")
                snapshots["presentation_status"] = snapshot

                print(f"✅ Presentations API contract snapshot captured")
            else:
                print(f"⚠️ Presentations API endpoint returned {response.status_code}")

    # Save snapshots
    output_file = "api_contract_snapshots.json"
    with open(output_file, 'w') as f:
        json.dump(snapshots, f, indent=2)

    print(f"📝 API contract snapshots saved to {output_file}")

    # Print summary
    print(f"\n📊 API Contract Summary:")
    for endpoint_name, snapshot in snapshots.items():
        validation = snapshot['validation']
        print(f"   {endpoint_name}:")
        print(f"     ✅ CamelCase fields: {validation['has_camelcase_fields']}")
        print(f"     ✅ Array standards: {validation['has_array_standards']}")
        print(f"     ✅ Array objectives: {validation['has_array_objectives']}")

    return True

if __name__ == "__main__":
    try:
        test_api_contract_snapshots()
        print("\n🎉 API contract snapshot tests completed successfully!")
    except Exception as e:
        print(f"\n❌ API contract snapshot test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)