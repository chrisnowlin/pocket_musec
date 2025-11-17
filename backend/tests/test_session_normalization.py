"""Tests for session field normalization"""

import unittest
from unittest.mock import Mock, patch
from backend.repositories.session_repository import SessionRepository
from backend.auth import Session


class TestSessionNormalization(unittest.TestCase):
    """Test session field normalization helpers"""

    def setUp(self):
        """Create test session repository"""
        self.repo = SessionRepository()

        # Create a test session
        self.test_session = Session(
            id="test-session-id",
            user_id="test-user",
            grade_level="Grade 3",
            strand_code="Connect",
            selected_standards="K.CC.1,K.CC.2,K.CC.3",
            selected_objectives="obj1,obj2,obj3",
            additional_context="Test context",
            lesson_duration="45 minutes",
            class_size=25,
            created_at="2025-11-16T10:00:00",
            updated_at="2025-11-16T10:30:00"
        )

    def test_parse_selected_standards_list(self):
        """Test parsing comma-separated standards into array"""
        result = self.repo.parse_selected_standards_list(self.test_session)

        expected = ["K.CC.1", "K.CC.2", "K.CC.3"]
        self.assertEqual(result, expected)

    def test_parse_empty_standards(self):
        """Test handling empty standards"""
        empty_session = Session(
            id="test",
            user_id="test",
            selected_standards=None,
            selected_objectives=None,
            created_at=None,
            updated_at=None
        )

        result = self.repo.parse_selected_standards_list(empty_session)
        self.assertEqual(result, [])

    def test_parse_selected_objectives_list(self):
        """Test parsing comma-separated objectives into array"""
        result = self.repo.parse_selected_objectives_list(self.test_session)

        expected = ["obj1", "obj2", "obj3"]
        self.assertEqual(result, expected)

    def test_parse_empty_objectives(self):
        """Test handling empty objectives"""
        empty_session = Session(
            id="test",
            user_id="test",
            selected_standards=None,
            selected_objectives=None,
            created_at=None,
            updated_at=None
        )

        result = self.repo.parse_selected_objectives_list(empty_session)
        self.assertEqual(result, [])

    def test_convert_standards_list_to_string(self):
        """Test converting standards array back to string"""
        standards_list = ["K.CC.1", "K.CC.2", "K.CC.3"]
        result = self.repo.convert_standards_list_to_string(standards_list)

        self.assertEqual(result, "K.CC.1,K.CC.2,K.CC.3")

    def test_convert_empty_standards_list_to_string(self):
        """Test converting empty standards array"""
        result = self.repo.convert_standards_list_to_string([])
        self.assertIsNone(result)

    def test_convert_objectives_list_to_string(self):
        """Test converting objectives array back to string"""
        objectives_list = ["obj1", "obj2", "obj3"]
        result = self.repo.convert_objectives_list_to_string(objectives_list)

        self.assertEqual(result, "obj1,obj2,obj3")

    @patch('backend.repositories.standards_repository.StandardsRepository')
    def test_normalize_standards_for_response(self, mock_standards_repo_class):
        """Test normalizing standards for API response"""
        # Mock standard repository
        mock_repo = Mock()
        mock_standard = Mock()
        mock_standard.standard_id = "K.CC.1"
        mock_standard.grade_level = "Kindergarten"
        mock_standard.strand_code = "CC"
        mock_standard.strand_name = "Counting and Cardinality"
        mock_standard.standard_text = "Know number names and the count sequence"

        mock_repo.get_standard_by_id.return_value = mock_standard
        mock_standards_repo_class.return_value = mock_repo

        result = self.repo.normalize_standards_for_response(self.test_session, mock_repo)

        expected = [{
            "id": "K.CC.1",
            "code": "K.CC.1",
            "grade": "Kindergarten",
            "strandCode": "CC",
            "strandName": "Counting and Cardinality",
            "title": "Know number names and the count sequence",
            "description": "Know number names and the count sequence"
        }]

        self.assertEqual(len(result), 3)  # Three standards
        self.assertEqual(result[0], expected[0])

    def test_normalize_objectives_for_response(self):
        """Test normalizing objectives for API response"""
        result = self.repo.normalize_objectives_for_response(self.test_session)

        expected = ["obj1", "obj2", "obj3"]
        self.assertEqual(result, expected)

    def test_handle_whitespace_in_standards(self):
        """Test proper handling of whitespace in comma-separated standards"""
        session_with_whitespace = Session(
            id="test",
            user_id="test",
            selected_standards="K.CC.1, K.CC.2 , K.CC.3",
            selected_objectives=" obj1 ,obj2, obj3 ",
            created_at=None,
            updated_at=None
        )

        standards = self.repo.parse_selected_standards_list(session_with_whitespace)
        objectives = self.repo.parse_selected_objectives_list(session_with_whitespace)

        self.assertEqual(standards, ["K.CC.1", "K.CC.2", "K.CC.3"])
        self.assertEqual(objectives, ["obj1", "obj2", "obj3"])


if __name__ == "__main__":
    unittest.main()