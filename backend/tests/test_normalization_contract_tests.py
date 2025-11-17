"""Simplified normalization contract tests focusing on core functionality"""

import os
import sys
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

class TestNormalizationContract:
    """Core normalization functionality tests"""

    def test_session_normalization_contract(self):
        """Test session normalization helpers work correctly"""
        from backend.repositories.session_repository import SessionRepository
        from backend.auth import Session

        session_repo = SessionRepository()

        # Test basic comma-separated parsing
        test_session = Session(
            id="test-session",
            user_id="test-user",
            grade_level="Grade 3",
            strand_code="Connect",
            selected_standards="K.CC.1,K.CC.2,K.CC.3",
            selected_objectives="obj1,obj2,obj3",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Test standards parsing
        standards = session_repo.parse_selected_standards_list(test_session)
        assert standards == ["K.CC.1", "K.CC.2", "K.CC.3"], "Should parse comma-separated standards"

        # Test objectives parsing
        objectives = session_repo.parse_selected_objectives_list(test_session)
        assert objectives == ["obj1", "obj2", "obj3"], "Should parse comma-separated objectives"

        # Test normalization to strings
        standards_str = session_repo.convert_standards_list_to_string(standards)
        objectives_str = session_repo.convert_objectives_list_to_string(objectives)
        assert standards_str == "K.CC.1,K.CC.2,K.CC.3", "Should convert back to string"
        assert objectives_str == "obj1,obj2,obj3", "Should convert back to string"

        print("✅ Session normalization contract test passed")

    def test_lesson_normalization_contract(self):
        """Test lesson normalization helpers work correctly"""
        from backend.repositories.lesson_repository import LessonRepository
        from backend.auth import Lesson

        lesson_repo = LessonRepository()

        # Test metadata parsing
        lesson_with_metadata = Lesson(
            id="test-lesson",
            session_id="test-session",
            user_id="test-user",
            title="Test",
            content="Test content",
            metadata=json.dumps({
                "grade_level": "Grade 3",
                "strand_code": "Connect",
                "selected_standards": "K.CC.1,K.CC.2",
                "selected_objectives": "obj1,obj2"
            }),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Test metadata parsing
        metadata = lesson_repo.parse_metadata(lesson_with_metadata)
        assert metadata["grade_level"] == "Grade 3", "Should parse metadata JSON"
        assert metadata["selected_standards"] == "K.CC.1,K.CC.2", "Should extract standards from metadata"

        # Test lesson normalization
        normalized = lesson_repo.normalize_lesson_for_response(lesson_with_metadata)

        # Check field mapping
        assert normalized["id"] == "test-lesson", "Should preserve ID"
        assert normalized["grade"] == "Grade 3", "Should map grade_level to grade"
        assert normalized["strand"] == "Connect", "Should map strand_code to strand"

        # Check date formatting
        assert normalized["createdAt"] is not None, "Should format created_at to ISO string"
        assert normalized["updatedAt"] is not None, "Should format updated_at to ISO string"

        # Check standards/objectives normalization
        assert normalized["selectedStandards"] == ["K.CC.1", "K.CC.2"], "Should normalize standards to array"
        assert normalized["selectedObjectives"] == ["obj1", "obj2"], "Should normalize objectives to array"

        print("✅ Lesson normalization contract test passed")

    def test_edge_cases_contract(self):
        """Test edge cases in normalization"""
        from backend.repositories.session_repository import SessionRepository
        from backend.repositories.lesson_repository import LessonRepository
        from backend.auth import Session, Lesson

        session_repo = SessionRepository()
        lesson_repo = LessonRepository()

        # Test empty/null handling
        empty_session = Session(
            id="empty",
            user_id="test",
            selected_standards=None,
            selected_objectives=None,
            created_at=None,
            updated_at=None
        )

        standards = session_repo.parse_selected_standards_list(empty_session)
        objectives = session_repo.parse_selected_objectives_list(empty_session)
        assert standards == [], "Empty standards should return empty array"
        assert objectives == [], "Empty objectives should return empty array"

        # Test whitespace handling
        whitespace_session = Session(
            id="whitespace",
            user_id="test",
            selected_standards="K.CC.1, K.CC.2 , K.CC.3",
            selected_objectives=" obj1 ,obj2, obj3 ",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        standards = session_repo.parse_selected_standards_list(whitespace_session)
        objectives = session_repo.parse_selected_objectives_list(whitespace_session)
        assert standards == ["K.CC.1", "K.CC.2", "K.CC.3"], "Should trim whitespace"
        assert objectives == ["obj1", "obj2", "obj3"], "Should trim whitespace"

        # Test empty metadata
        empty_metadata_lesson = Lesson(
            id="empty-meta",
            session_id="test",
            user_id="test",
            title="Test",
            content="Test content",
            metadata=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        metadata = lesson_repo.parse_metadata(empty_metadata_lesson)
        assert metadata == {}, "Empty metadata should return empty dict"

        # Test malformed JSON metadata
        malformed_lesson = Lesson(
            id="malformed",
            session_id="test",
            user_id="test",
            title="Test",
            content="Test content",
            metadata="invalid json",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        metadata = lesson_repo.parse_metadata(malformed_lesson)
        assert metadata == {}, "Malformed JSON metadata should return empty dict"

        print("✅ Edge cases contract test passed")

    def test_array_vs_string_handling_contract(self):
        """Test normalization handles both array and string inputs"""
        from backend.repositories.lesson_repository import LessonRepository
        from backend.auth import Lesson

        lesson_repo = LessonRepository()

        # Test with string metadata (legacy format)
        string_metadata_lesson = Lesson(
            id="string-meta",
            session_id="test",
            user_id="test",
            title="Test",
            content="Test content",
            metadata=json.dumps({
                "selected_standards": "K.CC.1,K.CC.2",
                "selected_objectives": "obj1,obj2"
            }),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        normalized = lesson_repo.normalize_lesson_for_response(string_metadata_lesson)
        assert normalized["selectedStandards"] == ["K.CC.1", "K.CC.2"], "Should normalize string standards"
        assert normalized["selectedObjectives"] == ["obj1", "obj2"], "Should normalize string objectives"

        # Test with array metadata (new format)
        array_metadata_lesson = Lesson(
            id="array-meta",
            session_id="test",
            user_id="test",
            title="Test",
            content="Test content",
            metadata=json.dumps({
                "selected_standards": ["K.CC.1", "K.CC.2"],
                "selected_objectives": ["obj1", "obj2"]
            }),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        normalized = lesson_repo.normalize_lesson_for_response(array_metadata_lesson)
        assert normalized["selectedStandards"] == ["K.CC.1", "K.CC.2"], "Should preserve array standards"
        assert normalized["selectedObjectives"] == ["obj1", "obj2"], "Should preserve array objectives"

        print("✅ Array vs string handling contract test passed")

    def run_all_tests(self):
        """Run all normalization contract tests"""
        try:
            self.test_session_normalization_contract()
            self.test_lesson_normalization_contract()
            self.test_edge_cases_contract()
            self.test_array_vs_string_handling_contract()

            print("\n🎉 All normalization contract tests passed!")
            return True
        except Exception as e:
            print(f"\n❌ Normalization contract test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    test_runner = TestNormalizationContract()
    success = test_runner.run_all_tests()
    sys.exit(0 if success else 1)