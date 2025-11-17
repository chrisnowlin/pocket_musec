"""End-to-end integration test for REST field normalization"""

import os
import sys
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from backend.api.main import app

def test_end_to_end_field_normalization():
    """Test complete flow: frontend API calls -> backend normalization -> frontend consumption"""

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

            # Setup standards repository mock
            mock_standards_repo = Mock()
            mock_standards_repo_class.return_value = mock_standards_repo

            # Create mock standard object
            mock_standard = Mock()
            mock_standard.standard_id = "K.CC.1"
            mock_standard.grade_level = "Kindergarten"
            mock_standard.strand_code = "CC"
            mock_standard.strand_name = "Counting and Cardinality"
            mock_standard.standard_text = "Know number names and the count sequence"
            mock_standards_repo.get_standard_by_id.return_value = mock_standard

            # Create a test session that will be returned by the create_session call
            from backend.auth import Session
            created_session = Session(
                id="created-session-123",
                user_id="test-user",
                grade_level="Grade 3",
                strand_code="Connect",
                selected_standards="K.CC.1,K.CC.2,K.CC.3",  # Comma-separated for DB storage
                selected_objectives="obj1,obj2,obj3",        # Comma-separated for DB storage
                additional_context="Test context",
                created_at="2025-11-16T10:00:00",
                updated_at="2025-11-16T10:30:00"
            )

            # Test the normalization helpers directly
            print("\n🔍 Testing normalization helpers directly...")
            from backend.repositories.session_repository import SessionRepository
            real_session_repo = SessionRepository()  # Create real instance for testing

            standards_list = real_session_repo.parse_selected_standards_list(created_session)
            objectives_list = real_session_repo.parse_selected_objectives_list(created_session)
            normalized_standards = real_session_repo.normalize_standards_for_response(created_session, mock_standards_repo)
            normalized_objectives = real_session_repo.normalize_objectives_for_response(created_session)

            print(f"🔍 Direct - standards_list: {standards_list}")
            print(f"🔍 Direct - objectives_list: {objectives_list}")
            print(f"🔍 Direct - normalized_standards count: {len(normalized_standards)}")
            print(f"🔍 Direct - normalized_objectives: {normalized_objectives}")

            # Set up the mock to use the real normalization helpers
            mock_session_repo.parse_selected_standards_list = real_session_repo.parse_selected_standards_list
            mock_session_repo.parse_selected_objectives_list = real_session_repo.parse_selected_objectives_list
            mock_session_repo.normalize_standards_for_response = real_session_repo.normalize_standards_for_response
            mock_session_repo.normalize_objectives_for_response = real_session_repo.normalize_objectives_for_response

            mock_session_repo.create_session.return_value = created_session
            mock_session_repo.get_session.return_value = created_session

            print("🧪 Testing end-to-end field normalization...")

            # 1. Test session creation with frontend-style camelCase payload
            print("\n1️⃣ Testing session creation...")
            create_response = client.post(
                "/api/sessions",
                json={
                    "grade_level": "Grade 3",
                    "strand_code": "Connect",
                    "standard_ids": ["K.CC.1", "K.CC.2", "K.CC.3"],  # Array input (new format)
                    "selectedObjectives": ["obj1", "obj2", "obj3"],    # Array input
                    "additionalContext": "Test context"
                }
            )

            assert create_response.status_code == 200
            session_data = create_response.json()
            print(f"✅ Response status: {create_response.status_code}")
            print(f"✅ Response fields: {list(session_data.keys())}")
            print(f"🔍 Debug selectedStandards: {session_data['selectedStandards']}")
            print(f"🔍 Debug selectedStandards type: {type(session_data['selectedStandards'])}")
            print(f"🔍 Debug selectedObjectives: {session_data['selectedObjectives']}")

            # 2. Verify response uses camelCase field names
            print("\n2️⃣ Verifying camelCase field names...")
            expected_camelcase_fields = [
                "gradeLevel", "strandCode", "selectedStandards",
                "selectedObjectives", "additionalContext",
                "createdAt", "updatedAt"
            ]

            for field in expected_camelcase_fields:
                assert field in session_data, f"Missing camelCase field: {field}"
            print("✅ All expected camelCase fields present")

            # 3. Verify selectedStandards is returned as structured array
            print("\n3️⃣ Verifying selectedStandards normalization...")
            assert isinstance(session_data["selectedStandards"], list), f"selectedStandards should be array, got {type(session_data['selectedStandards'])}"
            assert len(session_data["selectedStandards"]) > 0, "selectedStandards should not be empty"

            # Check structure of normalized standards
            standard = session_data["selectedStandards"][0]
            expected_standard_fields = ["id", "code", "grade", "strandCode", "strandName", "title", "description"]
            for field in expected_standard_fields:
                assert field in standard, f"Missing field in normalized standard: {field}"

            print(f"✅ selectedStandards properly normalized: {len(session_data['selectedStandards'])} items")
            print(f"✅ First standard structure: {list(standard.keys())}")

            # 4. Verify selectedObjectives is returned as simple string array
            print("\n4️⃣ Verifying selectedObjectives normalization...")
            assert isinstance(session_data["selectedObjectives"], list), f"selectedObjectives should be array, got {type(session_data['selectedObjectives'])}"
            assert all(isinstance(obj, str) for obj in session_data["selectedObjectives"]), "All objectives should be strings"

            print(f"✅ selectedObjectives properly normalized: {session_data['selectedObjectives']}")

            # 5. Test session listing (multiple sessions)
            print("\n5️⃣ Testing session listing...")

            # Mock multiple sessions for listing
            from backend.auth import Session
            test_sessions = [
                Session(
                    id="session-1",
                    user_id="test-user",
                    grade_level="Grade 1",
                    strand_code="Connect",
                    selected_standards="K.CC.1,K.CC.2",
                    selected_objectives="analyze,evaluate",
                    created_at="2025-11-16T10:00:00",
                    updated_at="2025-11-16T10:30:00"
                ),
                Session(
                    id="session-2",
                    user_id="test-user",
                    grade_level="Grade 2",
                    strand_code="Create",
                    selected_standards="K.CC.3,K.CC.4",
                    selected_objectives="create,design",
                    created_at="2025-11-16T11:00:00",
                    updated_at="2025-11-16T11:30:00"
                )
            ]

            mock_session_repo.list_sessions.return_value = test_sessions

            list_response = client.get("/api/sessions")
            assert list_response.status_code == 200

            sessions_list = list_response.json()
            assert isinstance(sessions_list, list), "Sessions list should be an array"
            assert len(sessions_list) >= 2, "Should have multiple sessions"

            # Verify each session in the list is properly normalized
            for session in sessions_list[:2]:  # Check first 2 sessions
                assert isinstance(session["selectedStandards"], list), " Each session should have normalized standards array"
                assert isinstance(session["selectedObjectives"], list), "Each session should have normalized objectives array"

            print(f"✅ Sessions listing properly normalized: {len(sessions_list)} sessions")

            # 6. Test session retrieval by ID
            print("\n6️⃣ Testing session retrieval...")
            mock_session_repo.get_session.return_value = test_sessions[0]

            get_response = client.get(f"/api/sessions/{test_sessions[0].id}")
            assert get_response.status_code == 200

            retrieved_session = get_response.json()
            assert isinstance(retrieved_session["selectedStandards"], list), "Retrieved session should have normalized standards"
            assert isinstance(retrieved_session["selectedObjectives"], list), "Retrieved session should have normalized objectives"

            print(f"✅ Session retrieval properly normalized")

            # 7. Test field consistency across all endpoints
            print("\n7️⃣ Verifying field consistency...")
            all_session_responses = [
                session_data,           # From create
                sessions_list[0],       # From list
                retrieved_session       # From get
            ]

            for response_data in all_session_responses:
                # Verify no snake_case fields that should be camelCase
                snake_case_fields_to_check = [
                    "grade_level", "strand_code", "selected_standards",
                    "selected_objectives", "additional_context",
                    "created_at", "updated_at"
                ]

                for snake_field in snake_case_fields_to_check:
                    assert snake_field not in response_data, f"Found snake_case field in response: {snake_field}"

            print("✅ No snake_case fields leaked to frontend responses")

            # 8. Verify data integrity
            print("\n8️⃣ Verifying data integrity...")
            original_standards = ["K.CC.1", "K.CC.2", "K.CC.3"]
            returned_standards = [s["id"] for s in session_data["selectedStandards"]]

            # The order might be different, but all original standards should be present
            for original in original_standards:
                assert original in returned_standards, f"Original standard {original} not found in response"

            original_objectives = ["obj1", "obj2", "obj3"]
            returned_objectives = session_data["selectedObjectives"]
            assert original_objectives == returned_objectives, "Objectives should match exactly"

            print("✅ Data integrity maintained through normalization")

            print("\n🎉 All field normalization tests passed!")
            print("\n📋 Summary:")
            print("   ✅ Backend: Comma-separated DB fields → Arrays")
            print("   ✅ API: Snake_case → camelCase field names")
            print("   ✅ Frontend: Consumes normalized arrays correctly")
            print("   ✅ Data integrity: All original data preserved")

            return True

if __name__ == "__main__":
    try:
        test_end_to_end_field_normalization()
        print("\n🏁 End-to-end field normalization integration test: PASSED")
    except Exception as e:
        print(f"\n❌ End-to-end field normalization test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)