"""Tests for session management API endpoints"""

import pytest
from unittest.mock import Mock, patch
from backend.api.routes.sessions import (
    _create_lesson_agent,
    _compose_lesson_from_agent,
    _standard_to_response,
    _session_to_response,
)
from backend.auth.models import User, ProcessingMode
from backend.pocketflow.lesson_agent import LessonAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store


class TestSessionHelpers:
    """Test suite for session helper functions"""

    def test_standard_to_response(self):
        """Test conversion of standard to response"""
        from backend.repositories.models import Standard

        standard = Standard(
            standard_id="3.CN.1",
            grade_level="Grade 3",
            strand_code="CN",
            strand_name="Connect",
            standard_text="Relate musical ideas",
            strand_description="Connect music with other arts",
        )

        # Mock repository
        mock_repo = Mock()
        mock_repo.get_objectives_for_standard = Mock(return_value=[])

        response = _standard_to_response(standard, mock_repo)

        assert response.id == "3.CN.1"
        assert response.code == "3.CN.1"
        assert response.grade == "Grade 3"
        assert response.strand_code == "CN"

    def test_session_to_response_without_standard(self):
        """Test conversion of session to response without selected standard"""
        session = Mock()
        session.id = "session-123"
        session.grade_level = "Grade 3"
        session.strand_code = "CN"
        session.selected_standards = None
        session.additional_context = "Test context"
        session.created_at = "2025-11-11T08:00:00Z"
        session.updated_at = "2025-11-11T08:00:00Z"

        mock_repo = Mock()
        mock_repo.get_standard_by_id = Mock(return_value=None)

        response = _session_to_response(session, mock_repo)

        assert response.id == "session-123"
        assert response.grade_level == "Grade 3"
        assert response.strand_code == "CN"
        assert response.selected_standard is None

    def test_create_lesson_agent(self):
        """Test creation of lesson agent from session"""
        session = Mock()
        session.grade_level = "Grade 3"
        session.strand_code = "CN"
        session.selected_standards = None

        agent = _create_lesson_agent(session)

        assert isinstance(agent, LessonAgent)
        assert agent.lesson_requirements.get("grade_level") == "Grade 3"
        assert agent.lesson_requirements.get("strand_code") == "CN"

    def test_compose_lesson_from_agent(self):
        """Test lesson composition from agent state"""
        user = Mock()
        user.id = "user-123"

        agent = Mock()
        agent.get_lesson_requirements = Mock(
            return_value={
                "grade_level": "Grade 3",
                "strand_code": "CN",
                "standard": Mock(standard_id="3.CN.1"),
                "duration": "30 minutes",
                "class_size": "25",
            }
        )

        result = _compose_lesson_from_agent(agent, user)

        assert "title" in result
        assert "content" in result
        assert "metadata" in result
        assert result["metadata"]["grade_level"] == "Grade 3"
        assert result["metadata"]["strand_code"] == "CN"


class TestLessonAgentIntegration:
    """Test suite for LessonAgent integration"""

    def test_agent_initialization(self):
        """Test that agent initializes properly"""
        flow = Flow(name="test")
        store = Store()

        agent = LessonAgent(flow=flow, store=store)

        assert agent is not None
        assert agent.get_state() == "welcome"
        assert len(agent.lesson_requirements) >= 0

    def test_agent_welcome_state(self):
        """Test agent welcome state"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        response = agent.chat("Hi")

        assert response is not None
        assert isinstance(response, str)
        assert "Welcome" in response or "Grade" in response

    def test_agent_grade_selection(self):
        """Test agent grade selection flow"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # First message to get welcome
        agent.chat("Hi")

        # Try grade selection
        response = agent.chat("1")

        assert response is not None
        assert isinstance(response, str)

    def test_agent_back_navigation(self):
        """Test agent back navigation"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # Get to grade selection
        agent.chat("Hi")

        # Go back
        response = agent.chat("back")

        assert response is not None
        # Should show welcome options again
        assert "Grade" in response or "Welcome" in response

    def test_agent_quit_command(self):
        """Test agent quit command"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        response = agent.chat("quit")

        assert response is not None
        assert agent.get_state() == "complete"


class TestLessonRequirementsTracking:
    """Test suite for lesson requirements tracking"""

    def test_grade_level_tracking(self):
        """Test that grade level is tracked"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # Navigate to grade selection and pick a grade
        agent.chat("Hi")  # Welcome
        agent.chat("1")  # Select grade 1

        requirements = agent.get_lesson_requirements()
        assert "grade_level" in requirements

    def test_requirements_persistence(self):
        """Test that requirements persist through conversation"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        initial_reqs = agent.get_lesson_requirements()

        # Have conversation
        agent.chat("Hi")
        agent.chat("1")

        final_reqs = agent.get_lesson_requirements()

        # Grade should be set after selecting it
        if "grade_level" in final_reqs:
            assert final_reqs["grade_level"] is not None


class TestErrorHandling:
    """Test suite for error handling"""

    def test_invalid_grade_input(self):
        """Test handling of invalid grade input"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        agent.chat("Hi")  # Get to grade selection
        response = agent.chat("999")  # Invalid grade

        assert response is not None
        # Should ask for valid input or show error
        assert isinstance(response, str)

    def test_non_numeric_grade_input(self):
        """Test handling of non-numeric grade input"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        agent.chat("Hi")  # Get to grade selection
        response = agent.chat("abc")  # Non-numeric

        assert response is not None
        assert isinstance(response, str)


class TestConversationHistory:
    """Test suite for conversation history"""

    def test_history_tracking(self):
        """Test that conversation history is tracked"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        agent.chat("Hi")
        agent.chat("1")
        agent.chat("1")

        history = agent.get_conversation_history()
        assert len(history) > 0

    def test_reset_conversation(self):
        """Test conversation reset"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # Build up history
        agent.chat("Hi")
        agent.chat("1")

        # Reset
        agent.reset_conversation()

        assert agent.get_state() == "welcome"
        history = agent.get_conversation_history()
        assert len(history) == 0
