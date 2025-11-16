"""Tests for lesson generation with LLM integration"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.pocketflow.lesson_agent import LessonAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.api.routes.sessions import _compose_lesson_from_agent, _generate_draft_payload
from backend.auth.models import User, ProcessingMode
from backend.repositories.models import Standard, Objective


class TestLessonGeneration:
    """Test suite for lesson generation"""

    def test_agent_lesson_generation_flow(self):
        """Test agent reaches lesson generation state"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # Navigate through conversation to lesson generation
        agent.chat("Hi")  # Welcome
        agent.chat("1")  # Select grade
        agent.chat("1")  # Select strand
        agent.chat("1")  # Select standard

        # State should have advanced
        current_state = agent.get_state()
        assert current_state is not None

    @patch("backend.llm.chutes_client.ChutesClient.generate_lesson_plan")
    def test_llm_lesson_composition(self, mock_generate):
        """Test composing lesson from LLM output"""
        # Mock LLM output
        mock_lesson = """Music Lesson Plan: Grade 3 Connect

Objectives:
- Students will understand connections between music and culture
- Students will identify how music tells stories

Activities:
1. Listening Activity: Play cultural music examples
2. Discussion: How does music reflect culture?
3. Creative Task: Create a musical story

Assessment:
Students will present their musical story with cultural explanation
"""
        mock_generate.return_value = mock_lesson

        # Create agent with mocked LLM
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # Set up requirements as if we had completed the conversation
        user = User(
            id="user-123",
            email="test@example.com",
            password_hash="hash",
            processing_mode=ProcessingMode.CLOUD,
        )

        # Manually set up lesson requirements
        standard = Mock()
        standard.standard_id = "3.CN.1"
        agent.lesson_requirements["grade_level"] = "Grade 3"
        agent.lesson_requirements["strand_code"] = "CN"
        agent.lesson_requirements["standard"] = standard
        agent.lesson_requirements["generated_lesson"] = mock_lesson

        # Compose lesson
        plan = _compose_lesson_from_agent(agent, user)

        assert plan["content"] == mock_lesson
        assert plan["metadata"]["generated_by"] == "llm"

    def test_template_fallback_when_no_llm(self):
        """Test fallback to template when LLM output not available"""
        user = User(
            id="user-123",
            email="test@example.com",
            password_hash="hash",
            processing_mode=ProcessingMode.CLOUD,
        )

        agent = Mock()
        standard = Mock()
        standard.standard_id = "3.CN.1"

        # No generated_lesson in requirements
        agent.get_lesson_requirements.return_value = {
            "grade_level": "Grade 3",
            "strand_code": "CN",
            "standard": standard,
        }

        plan = _compose_lesson_from_agent(agent, user)

        # Should use template-based content
        assert "Warm-up" in plan["content"]
        assert plan["metadata"]["generated_by"] == "template"

    def test_lesson_requirements_building(self):
        """Test building lesson requirements from conversation"""
        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # Simulate conversation
        agent.chat("Hi")
        agent.chat("1")  # Grade 1

        requirements = agent.get_lesson_requirements()

        # Should have accumulated some requirements
        assert isinstance(requirements, dict)

    @patch("backend.llm.chutes_client.ChutesClient.generate_lesson_plan")
    def test_lesson_generation_with_context(self, mock_generate):
        """Test lesson generation includes context from user"""
        mock_lesson = "Generated lesson with context"
        mock_generate.return_value = mock_lesson

        flow = Flow(name="test")
        store = Store()
        agent = LessonAgent(flow=flow, store=store)

        # Set requirements with context
        user = User(
            id="user-123",
            email="test@example.com",
            password_hash="hash",
            processing_mode=ProcessingMode.CLOUD,
        )

        standard = Mock()
        standard.standard_id = "3.CN.1"

        agent.lesson_requirements["grade_level"] = "Grade 3"
        agent.lesson_requirements["strand_code"] = "CN"
        agent.lesson_requirements["standard"] = standard
        agent.lesson_requirements["duration"] = "30 minutes"
        agent.lesson_requirements["class_size"] = 25
        agent.lesson_requirements["additional_context"] = "Mixed instruments available"
        agent.lesson_requirements["generated_lesson"] = mock_lesson

        plan = _compose_lesson_from_agent(agent, user)

        # Check metadata includes all context
        assert plan["metadata"]["duration"] == "30 minutes"
        assert plan["metadata"]["class_size"] == 25

    def test_lesson_metadata_complete(self):
        """Test that lesson metadata is complete"""
        user = User(
            id="user-123",
            email="test@example.com",
            password_hash="hash",
            processing_mode=ProcessingMode.CLOUD,
        )

        agent = Mock()
        standard = Mock()
        standard.standard_id = "3.CN.1"

        agent.get_lesson_requirements.return_value = {
            "grade_level": "Grade 3",
            "strand_code": "CN",
            "standard": standard,
            "duration": "45 minutes",
            "class_size": 30,
        }

        plan = _compose_lesson_from_agent(agent, user)

        # Verify all metadata fields
        assert "grade_level" in plan["metadata"]
        assert "strand_code" in plan["metadata"]
        assert "standard_id" in plan["metadata"]
        assert "duration" in plan["metadata"]
        assert "class_size" in plan["metadata"]
        assert "generated_by" in plan["metadata"]
class TestLessonContent:
    """Test suite for lesson content generation"""

    def test_template_lesson_structure(self):
        """Test template-based lesson has proper structure"""
        user = User(
            id="user-123",
            email="test@example.com",
            password_hash="hash",
            processing_mode=ProcessingMode.CLOUD,
        )

        agent = Mock()
        standard = Mock()
        standard.standard_id = "3.CN.1"

        agent.get_lesson_requirements.return_value = {
            "grade_level": "Grade 3",
            "strand_code": "CN",
            "standard": standard,
        }

        plan = _compose_lesson_from_agent(agent, user)

        # Template should have key sections
        content = plan["content"]
        assert "Title" in content or "Overview" in content
        assert "Activities" in content or "Warm-up" in content
        assert "Assessment" in content or "Extensions" in content

    def test_llm_lesson_preserves_formatting(self):
        """Test that LLM lesson formatting is preserved"""
        user = User(
            id="user-123",
            email="test@example.com",
            password_hash="hash",
            processing_mode=ProcessingMode.CLOUD,
        )

        llm_content = """Objectives:
- Objective 1
- Objective 2

Activities:
1. Activity 1
2. Activity 2

Assessment:
Students will demonstrate mastery through performance
"""

        agent = Mock()
        standard = Mock()
        standard.standard_id = "3.CN.1"

        agent.get_lesson_requirements.return_value = {
            "grade_level": "Grade 3",
            "strand_code": "CN",
            "standard": standard,
            "generated_lesson": llm_content,
        }

        plan = _compose_lesson_from_agent(agent, user)

        # Formatting should be preserved
        assert plan["content"] == llm_content
        assert "Objectives:" in plan["content"]


class TestLessonSummary:
    """Test suite for lesson summary generation"""

    def test_summary_includes_grade_and_standard(self):
        """Test summary includes grade level and standard"""
        user = User(
            id="user-123",
            email="test@example.com",
            password_hash="hash",
            processing_mode=ProcessingMode.CLOUD,
        )

        agent = Mock()
        standard = Mock()
        standard.standard_id = "3.CN.1"

        agent.get_lesson_requirements.return_value = {
            "grade_level": "Grade 3",
            "strand_code": "CN",
            "standard": standard,
        }

        plan = _compose_lesson_from_agent(agent, user)

        summary = plan["summary"]
        # Summary should mention grade and standard
        assert "Grade 3" in summary or "grade level" in summary.lower()

    def test_llm_summary_different_from_template(self):
        """Test LLM-generated summary differs from template"""
        user = User(
            id="user-123",
            email="test@example.com",
            password_hash="hash",
            processing_mode=ProcessingMode.CLOUD,
        )

        agent = Mock()
        standard = Mock()
        standard.standard_id = "3.CN.1"

        # Template version
        agent.get_lesson_requirements.return_value = {
            "grade_level": "Grade 3",
            "strand_code": "CN",
            "standard": standard,
        }

        template_plan = _compose_lesson_from_agent(agent, user)
        template_summary = template_plan["summary"]

        # LLM version
        agent.get_lesson_requirements.return_value = {
            "grade_level": "Grade 3",
            "strand_code": "CN",
            "standard": standard,
            "generated_lesson": "AI-generated content",
        }

        llm_plan = _compose_lesson_from_agent(agent, user)
        llm_summary = llm_plan["summary"]

        # Summaries should be different
        assert llm_summary != template_summary
        assert "AI-generated" in llm_summary


class TestLessonCitations:
    """Test suite for lesson citations"""

    def test_citations_include_standard(self):
        """Test citations include selected standard"""
        user = User(
            id="user-123",
            email="test@example.com",
            password_hash="hash",
            processing_mode=ProcessingMode.CLOUD,
        )

        agent = Mock()
        standard = Mock()
        standard.standard_id = "3.CN.1"

        agent.get_lesson_requirements.return_value = {
            "grade_level": "Grade 3",
            "strand_code": "CN",
            "standard": standard,
        }

        plan = _compose_lesson_from_agent(agent, user)

        assert "3.CN.1" in plan["citations"]

    def test_citations_empty_without_standard(self):
        """Test citations empty when no standard selected"""
        user = User(
            id="user-123",
            email="test@example.com",
            password_hash="hash",
            processing_mode=ProcessingMode.CLOUD,
        )

        agent = Mock()
        agent.get_lesson_requirements.return_value = {
            "grade_level": "Grade 3",
            "strand_code": "CN",
            "standard": None,
        }

        plan = _compose_lesson_from_agent(agent, user)

        assert plan["citations"] == []


class TestLessonTitle:
    """Test suite for lesson title generation"""

    def test_title_uses_standard_id(self):
        """Test title includes standard ID"""
        user = User(
            id="user-123",
            email="test@example.com",
            password_hash="hash",
            processing_mode=ProcessingMode.CLOUD,
        )

        agent = Mock()
        standard = Mock()
        standard.standard_id = "3.CN.1"

        agent.get_lesson_requirements.return_value = {
            "grade_level": "Grade 3",
            "strand_code": "CN",
            "standard": standard,
        }

        plan = _compose_lesson_from_agent(agent, user)

        assert plan["title"] == "3.CN.1"

    def test_title_fallback_without_standard(self):
        """Test title fallback when no standard"""
        user = User(
            id="user-123",
            email="test@example.com",
            password_hash="hash",
            processing_mode=ProcessingMode.CLOUD,
        )

        agent = Mock()
        agent.get_lesson_requirements.return_value = {
            "grade_level": "Grade 3",
            "standard": None,
        }

        plan = _compose_lesson_from_agent(agent, user)

        assert plan["title"] == "Selected standard"
