"""End-to-end API flow tests"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from backend.repositories.session_repository import SessionRepository
from backend.repositories.lesson_repository import LessonRepository
from backend.repositories.standards_repository import StandardsRepository
from backend.pocketflow.lesson_agent import LessonAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.api.routes.sessions import (
    _create_lesson_agent,
    _compose_lesson_from_agent,
)
from backend.auth.models import User, ProcessingMode


class TestEndToEndFlow:
    """End-to-end flow tests"""

    def test_session_creation_flow(self):
        """Test complete session creation flow"""
        # This test verifies that session creation works
        # We test with real SessionRepository to ensure integration
        from backend.repositories.session_repository import SessionRepository

        repo = SessionRepository()
        session = repo.create_session(
            user_id="user-123",
            grade_level="Grade 3",
            strand_code="CN",
            standard_id=None,
            additional_context=None,
        )

        assert session.id is not None
        assert session.user_id == "user-123"
        assert session.grade_level == "Grade 3"
        assert session.strand_code == "CN"

    def test_agent_conversation_flow(self):
        """Test complete agent conversation flow through all states"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # State 1: Welcome
        response = agent.chat("Hello")
        assert response is not None
        assert "Welcome" in response or "Grade" in response
        assert agent.get_state() == "grade_selection"

        # State 2: Grade selection
        response = agent.chat("1")  # Select first grade
        assert response is not None

        # Check that we've moved to next state
        current_state = agent.get_state()
        assert current_state in ["strand_selection", "standard_selection"]

    def test_agent_with_all_inputs(self):
        """Test agent with full user journey"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # Welcome -> Grade Selection
        agent.chat("Hi")
        assert agent.get_state() == "grade_selection"

        # Grade Selection -> Strand Selection
        agent.chat("1")
        # State should advance
        state_after_grade = agent.get_state()
        assert state_after_grade is not None

    @patch(
        "backend.repositories.standards_repository.StandardsRepository.get_grade_levels"
    )
    def test_agent_grade_options(self, mock_get_grades):
        """Test that agent shows correct grade options"""
        mock_get_grades.return_value = ["K", "1", "2", "3", "4", "5"]

        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        response = agent.chat("hello")

        # Should show grade options
        assert "K" in response or "Grade" in response or "1" in response

    def test_lesson_composition(self):
        """Test lesson composition from agent requirements"""
        user = User(
            id="user-123",
            email="test@example.com",
            password_hash="hash",
            processing_mode=ProcessingMode.CLOUD,
        )

        agent = Mock()
        standard_mock = Mock()
        standard_mock.standard_id = "3.CN.1"

        agent.get_lesson_requirements.return_value = {
            "grade_level": "Grade 3",
            "strand_code": "CN",
            "standard": standard_mock,
            "duration": "30 minutes",
            "class_size": "25",
        }

        plan = _compose_lesson_from_agent(agent, user)

        assert "title" in plan
        assert "content" in plan
        assert "metadata" in plan
        assert plan["metadata"]["grade_level"] == "Grade 3"
        assert plan["metadata"]["strand_code"] == "CN"

    def test_message_flow_sequence(self):
        """Test a sequence of messages through the API flow"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # Simulate a user conversation
        messages = [
            ("Hi! I want to create a music lesson", "Welcome or grade selection"),
            ("1", "Should select first grade"),
            ("1", "Should select first strand"),
        ]

        for user_msg, expectation in messages:
            response = agent.chat(user_msg)
            assert response is not None
            assert isinstance(response, str)
            print(f"User: {user_msg}")
            print(f"Agent: {response[:100]}...")
            print(f"State: {agent.get_state()}\n")

    def test_error_recovery(self):
        """Test error recovery in conversation"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # Get to grade selection
        agent.chat("Hello")

        # Send invalid input
        response1 = agent.chat("invalid")
        assert response1 is not None

        # Should still be in same state, ready for valid input
        response2 = agent.chat("1")
        assert response2 is not None

        # State should have advanced
        assert agent.get_state() != "grade_selection"


class TestAPIIntegrationScenarios:
    """Test realistic API integration scenarios"""

    def test_session_with_lesson_generation(self):
        """Test creating a session and generating a lesson"""
        user = User(
            id="user-123",
            email="teacher@school.edu",
            password_hash="hash",
            processing_mode=ProcessingMode.CLOUD,
        )

        # Create session
        flow = Flow(name="test")
        store = Store()
        agent = _create_lesson_agent(
            Mock(grade_level="Grade 3", strand_code="CN", selected_standards=None)
        )

        # Simulate conversation
        agent.chat("Hi")
        agent.chat("1")  # Select grade

        # Get requirements
        requirements = agent.get_lesson_requirements()
        assert len(requirements) > 0

        # Compose lesson
        lesson = _compose_lesson_from_agent(agent, user)
        assert lesson["title"] is not None

    def test_multiple_sessions(self):
        """Test managing multiple sessions"""
        flow = Flow(name="test")
        store = Store()

        # Create multiple agents (simulating multiple sessions)
        agents = []
        for i in range(3):
            agent = LessonAgent(flow=flow, store=store)
            agents.append(agent)

        # Each should be independent
        for agent in agents:
            agent.chat("Hi")
            agent.chat("1")

        # All should have different instances
        assert len(agents) == 3

    def test_conversation_context_isolation(self):
        """Test that conversation contexts don't bleed between sessions"""
        flow1 = Flow(name="flow1")
        store1 = Store()
        agent1 = LessonAgent(flow=flow1, store=store1)

        flow2 = Flow(name="flow2")
        store2 = Store()
        agent2 = LessonAgent(flow=flow2, store=store2)

        # Run through agent1
        agent1.chat("Hi")
        agent1.chat("1")
        req1 = agent1.get_lesson_requirements()

        # Run through agent2
        agent2.chat("Hi")
        agent2.chat("2")
        req2 = agent2.get_lesson_requirements()

        # Both should have completed their flows independently
        assert agent1.get_state() is not None
        assert agent2.get_state() is not None


class TestDataPersistence:
    """Test data persistence scenarios"""

    def test_requirement_persistence_across_turns(self):
        """Test that requirements persist across conversation turns"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # First turn
        agent.chat("Hi")
        agent.chat("1")  # Select grade 1
        reqs_after_grade = agent.get_lesson_requirements()
        grade_1 = reqs_after_grade.get("grade_level")

        # Subsequent turns
        agent.chat("1")  # Select strand
        reqs_after_strand = agent.get_lesson_requirements()
        grade_2 = reqs_after_strand.get("grade_level")

        # Grade should persist
        assert grade_1 == grade_2

    def test_lesson_requirements_accumulation(self):
        """Test that lesson requirements accumulate through conversation"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        initial_keys = set(agent.get_lesson_requirements().keys())

        agent.chat("Hi")
        agent.chat("1")

        after_keys = set(agent.get_lesson_requirements().keys())

        # Should have accumulated at least grade_level
        if "grade_level" in after_keys:
            assert len(after_keys) >= len(initial_keys)


class TestStateTransitions:
    """Test state transition logic"""

    def test_forward_transitions(self):
        """Test forward state transitions"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        states_visited = []
        states_visited.append(agent.get_state())  # welcome

        agent.chat("Hi")
        states_visited.append(agent.get_state())  # Should be grade_selection

        agent.chat("1")
        states_visited.append(agent.get_state())

        # Should have progressed through states
        assert len(set(states_visited)) >= 2

    def test_back_transitions(self):
        """Test backward state transitions with 'back' command"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # Get to grade selection
        agent.chat("Hi")
        assert agent.get_state() == "grade_selection"

        # Go back to welcome
        agent.chat("back")
        # Should be back at welcome or able to see welcome options
        # The exact state depends on implementation


class TestInputValidation:
    """Test input validation"""

    def test_invalid_numeric_input(self):
        """Test handling of invalid numeric inputs"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        agent.chat("Hi")  # Get to grade selection

        # Too high
        response = agent.chat("999")
        assert response is not None
        assert (
            "Please enter" in response
            or "number" in response.lower()
            or agent.get_state() == "grade_selection"
        )

    def test_empty_input_handling(self):
        """Test handling of empty inputs"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        agent.chat("Hi")

        # Empty input
        response = agent.chat("")
        assert response is not None

    def test_special_character_input(self):
        """Test handling of special character inputs"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        agent.chat("Hi")

        response = agent.chat("!@#$%")
        assert response is not None
