"""Tests for LessonAgent class"""

import pytest
from unittest.mock import Mock, patch
from backend.pocketflow.lesson_agent import LessonAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.repositories.models import Standard, Objective
from backend.llm.chutes_client import ChutesClient
from backend.llm.prompt_templates import LessonPromptContext


class TestLessonAgent:
    """Test suite for LessonAgent"""
    
    @pytest.fixture
    def mock_flow(self):
        """Create a mock Flow object"""
        return Mock(spec=Flow)
    
    @pytest.fixture
    def mock_store(self):
        """Create a mock Store object"""
        store = Mock(spec=Store)
        store.get = Mock(return_value=None)
        store.set = Mock()
        return store
    
    @pytest.fixture
    def mock_standards_repo(self):
        """Create a mock StandardsRepository"""
        repo = Mock()
        repo.get_grade_levels.return_value = ["Kindergarten", "1st Grade", "2nd Grade"]
        repo.get_strand_info.return_value = {
            "CN": {"name": "Musical Creativity", "description": "Creating music"},
            "PR": {"name": "Musical Performance", "description": "Performing music"}
        }
        repo.get_standards_by_grade_and_strand.return_value = []
        return repo
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock ChutesClient"""
        client = Mock(spec=ChutesClient)
        client.generate_lesson_plan.return_value = "Generated lesson plan content"
        return client
    
    @pytest.fixture
    def lesson_agent(self, mock_flow, mock_store, mock_standards_repo, mock_llm_client):
        """Create a LessonAgent instance with mocked dependencies"""
        return LessonAgent(mock_flow, mock_store, mock_standards_repo, mock_llm_client)
    
    def test_initialization(self, lesson_agent):
        """Test LessonAgent initialization"""
        assert lesson_agent.name == "LessonAgent"
        assert lesson_agent.get_state() == "welcome"
        assert lesson_agent.lesson_requirements == {}
        assert len(lesson_agent.state_handlers) == 8
    
    def test_setup_state_handlers(self, lesson_agent):
        """Test that all state handlers are properly set up"""
        expected_handlers = [
            "welcome", "grade_selection", "strand_selection",
            "standard_selection", "objective_refinement", 
            "context_collection", "lesson_generation", "complete"
        ]
        
        for state in expected_handlers:
            assert state in lesson_agent.state_handlers
    
    def test_handle_welcome_quit(self, lesson_agent):
        """Test quit command in welcome state"""
        response = lesson_agent.chat("quit")
        assert "Lesson generation cancelled" in response
        assert lesson_agent.get_state() == "complete"
    
    def test_handle_welcome_exit(self, lesson_agent):
        """Test exit command in welcome state"""
        response = lesson_agent.chat("exit")
        assert "Lesson generation cancelled" in response
        assert lesson_agent.get_state() == "complete"
    
    def test_handle_welcome_grade_options(self, lesson_agent):
        """Test grade level options display"""
        response = lesson_agent.chat("")
        assert "Welcome to PocketMusec" in response
        assert "Kindergarten" in response
        assert "1st Grade" in response
        assert "2nd Grade" in response
        assert lesson_agent.get_state() == "grade_selection"
    
    def test_handle_grade_selection_valid(self, lesson_agent, mock_standards_repo):
        """Test valid grade selection"""
        # Mock standards for grade
        mock_standard = Mock()
        mock_standard.strand_code = "CN"
        mock_standards_repo.get_standards_by_grade.return_value = [mock_standard]
        
        lesson_agent.set_state("grade_selection")
        response = lesson_agent.chat("1")
        
        assert lesson_agent.lesson_requirements['grade_level'] == "Kindergarten"
        assert lesson_agent.get_state() == "strand_selection"
    
    def test_handle_grade_selection_invalid_number(self, lesson_agent):
        """Test invalid grade number selection"""
        lesson_agent.set_state("grade_selection")
        response = lesson_agent.chat("99")
        assert "Please enter a number between" in response
        assert lesson_agent.get_state() == "grade_selection"
    
    def test_handle_grade_selection_invalid_input(self, lesson_agent):
        """Test invalid grade input"""
        lesson_agent.set_state("grade_selection")
        response = lesson_agent.chat("abc")
        assert "Please enter a valid number" in response
        assert lesson_agent.get_state() == "grade_selection"
    
    def test_handle_grade_selection_back(self, lesson_agent):
        """Test back navigation from grade selection"""
        lesson_agent.set_state("grade_selection")
        response = lesson_agent.chat("back")
        assert lesson_agent.get_state() == "welcome"
    
    def test_handle_strand_selection_first_time(self, lesson_agent, mock_standards_repo):
        """Test strand selection first time display"""
        lesson_agent.lesson_requirements['grade_level'] = "Kindergarten"
        lesson_agent.set_state("strand_selection")
        
        # Mock standards for grade
        mock_standard = Mock()
        mock_standard.strand_code = "CN"
        mock_standards_repo.get_standards_by_grade.return_value = [mock_standard]
        
        response = lesson_agent.chat("")
        assert "Grade Kindergarten - Select a Strand" in response
        assert "Musical Creativity" in response
    
    def test_handle_strand_selection_valid(self, lesson_agent, mock_standards_repo):
        """Test valid strand selection"""
        lesson_agent.lesson_requirements['grade_level'] = "Kindergarten"
        lesson_agent.set_state("strand_selection")
        
        # Mock standards for grade
        mock_standard = Mock()
        mock_standard.strand_code = "CN"
        mock_standards_repo.get_standards_by_grade.return_value = [mock_standard]
        
        response = lesson_agent.chat("1")
        
        assert lesson_agent.lesson_requirements['strand_code'] == "CN"
        assert lesson_agent.get_state() == "standard_selection"
    
    def test_handle_standard_selection_with_topic(self, lesson_agent, mock_standards_repo):
        """Test standard selection with topic recommendation"""
        lesson_agent.lesson_requirements.update({
            'grade_level': 'Kindergarten',
            'strand_code': 'CN'
        })
        lesson_agent.set_state("standard_selection")
        
        # Mock recommendations
        mock_standard = Mock()
        mock_standard.standard_id = "K.CN.1"
        mock_standard.standard_text = "Create music"
        mock_standards_repo.recommend_standards_for_topic.return_value = [
            (mock_standard, 0.85)
        ]
        
        response = lesson_agent.chat("rhythm")
        
        assert "Recommended standards for 'rhythm'" in response
        assert "K.CN.1" in response
    
    def test_handle_standard_selection_valid_number(self, lesson_agent, mock_standards_repo):
        """Test standard selection with valid number"""
        lesson_agent.lesson_requirements.update({
            'grade_level': 'Kindergarten',
            'strand_code': 'CN'
        })
        lesson_agent.set_state("standard_selection")
        
        # Mock standards
        mock_standard = Mock()
        mock_standard.standard_id = "K.CN.1"
        mock_standard.standard_text = "Create music"
        mock_standards_repo.get_standards_by_grade_and_strand.return_value = [mock_standard]
        mock_objective = Mock()
        mock_objective.objective_text = "Create rhythmic patterns"
        mock_standards_repo.get_objectives_for_standard.return_value = [mock_objective]
        
        response = lesson_agent.chat("1")
        
        assert lesson_agent.lesson_requirements['standard'] == mock_standard
        assert lesson_agent.get_state() == "objective_refinement"
    
    def test_handle_objective_refinement_no_objectives(self, lesson_agent):
        """Test objective refinement when no objectives available"""
        lesson_agent.lesson_requirements.update({
            'standard': Mock(),
            'objectives': []
        })
        lesson_agent.set_state("objective_refinement")
        
        response = lesson_agent.chat("")
        
        assert lesson_agent.get_state() == "context_collection"
    
    def test_handle_objective_refinement_with_objectives(self, lesson_agent):
        """Test objective refinement with objectives available"""
        mock_objective = Mock()
        mock_objective.objective_text = "Create rhythmic patterns"
        
        lesson_agent.lesson_requirements.update({
            'standard': Mock(),
            'objectives': [mock_objective]
        })
        lesson_agent.set_state("objective_refinement")
        
        response = lesson_agent.chat("")
        
        assert "Learning Objectives" in response
        assert "Create rhythmic patterns" in response
    
    def test_handle_objective_refinement_select_all(self, lesson_agent):
        """Test selecting all objectives"""
        mock_objective = Mock()
        mock_objective.objective_text = "Create rhythmic patterns"
        
        lesson_agent.lesson_requirements.update({
            'standard': Mock(),
            'objectives': [mock_objective]
        })
        lesson_agent.set_state("objective_refinement")
        
        response = lesson_agent.chat("all")
        
        assert lesson_agent.lesson_requirements['selected_objectives'] == [mock_objective]
        assert lesson_agent.get_state() == "context_collection"
    
    def test_handle_objective_refinement_skip(self, lesson_agent):
        """Test skipping objective selection"""
        mock_objective = Mock()
        mock_objective.objective_text = "Create rhythmic patterns"
        lesson_agent.lesson_requirements.update({
            'standard': Mock(),
            'objectives': [mock_objective]
        })
        lesson_agent.set_state("objective_refinement")
        
        response = lesson_agent.chat("skip")
        
        assert lesson_agent.lesson_requirements['selected_objectives'] == []
        assert lesson_agent.get_state() == "context_collection"
    
    def test_handle_context_collection_first_time(self, lesson_agent):
        """Test context collection first time display"""
        lesson_agent.set_state("context_collection")
        
        response = lesson_agent.chat("")
        
        assert "Additional Context (Optional)" in response
        assert "Specific topics or themes" in response
    
    def test_handle_context_collection_with_input(self, lesson_agent, mock_llm_client):
        """Test context collection with user input"""
        lesson_agent.lesson_requirements.update({
            'grade_level': 'Kindergarten',
            'strand_code': 'CN',
            'strand_info': {'name': 'Creativity', 'description': 'Creating music'},
            'standard': Mock(),
            'selected_objectives': []
        })
        lesson_agent.set_state("context_collection")
        
        response = lesson_agent.chat("Focus on rhythm using classroom instruments")
        
        assert lesson_agent.lesson_requirements['additional_context'] == "Focus on rhythm using classroom instruments"
        assert lesson_agent.get_state() == "complete"
    
    def test_handle_context_collection_skip(self, lesson_agent, mock_llm_client):
        """Test skipping context collection"""
        lesson_agent.lesson_requirements.update({
            'grade_level': 'Kindergarten',
            'strand_code': 'CN',
            'strand_info': {'name': 'Creativity', 'description': 'Creating music'},
            'standard': Mock(),
            'selected_objectives': []
        })
        lesson_agent.set_state("context_collection")
        
        response = lesson_agent.chat("skip")
        
        assert lesson_agent.get_state() == "complete"
    
    def test_generate_lesson_success(self, lesson_agent, mock_llm_client):
        """Test successful lesson generation"""
        mock_standard = Mock()
        mock_standard.standard_id = "K.CN.1"
        mock_standard.standard_text = "Create music"
        
        lesson_agent.lesson_requirements.update({
            'grade_level': 'Kindergarten',
            'strand_code': 'CN',
            'strand_info': {'name': 'Creativity', 'description': 'Creating music'},
            'standard': mock_standard,
            'selected_objectives': []
        })
        lesson_agent.set_state("lesson_generation")
        
        response = lesson_agent.chat("")
        
        assert "Lesson Generated Successfully" in response
        assert "Generated lesson plan content" in response
        assert lesson_agent.get_state() == "complete"
        assert lesson_agent.lesson_requirements['generated_lesson'] == "Generated lesson plan content"
    
    def test_generate_lesson_error(self, lesson_agent, mock_llm_client):
        """Test lesson generation with error"""
        mock_llm_client.generate_lesson_plan.side_effect = Exception("API Error")
        
        lesson_agent.lesson_requirements.update({
            'grade_level': 'Kindergarten',
            'strand_code': 'CN',
            'strand_info': {'name': 'Creativity', 'description': 'Creating music'},
            'standard': Mock(),
            'selected_objectives': []
        })
        lesson_agent.set_state("lesson_generation")
        
        response = lesson_agent.chat("")
        
        assert "Error generating lesson" in response
        assert "API Error" in response

    def test_regenerate_lesson_plan_success(self, lesson_agent, mock_llm_client):
        """Test the regenerate_lesson_plan helper"""
        mock_standard = Mock()
        mock_standard.standard_id = "K.CN.1"
        mock_standard.standard_text = "Create music"
        
        lesson_agent.lesson_requirements.update({
            'grade_level': 'Kindergarten',
            'strand_code': 'CN',
            'strand_info': {'name': 'Creativity', 'description': 'Creating music'},
            'standard': mock_standard,
            'selected_objectives': []
        })
        lesson_agent.set_state("complete")

        plan = lesson_agent.regenerate_lesson_plan()

        assert plan == "Generated lesson plan content"
        assert lesson_agent.get_generated_lesson() == "Generated lesson plan content"
        assert lesson_agent.get_state() == "complete"

    def test_regenerate_lesson_plan_error(self, lesson_agent, mock_llm_client):
        """Test regenerate path when the LLM client fails"""
        mock_llm_client.generate_lesson_plan.side_effect = Exception("API failure")

        lesson_agent.lesson_requirements.update({
            'grade_level': 'Kindergarten',
            'strand_code': 'CN',
            'strand_info': {'name': 'Creativity', 'description': 'Creating music'},
            'standard': Mock(),
            'selected_objectives': []
        })
        lesson_agent.set_state("complete")

        with pytest.raises(Exception):
            lesson_agent.regenerate_lesson_plan()
    
    def test_build_lesson_context(self, lesson_agent):
        """Test building lesson context for LLM"""
        mock_standard = Mock()
        mock_standard.standard_id = "K.CN.1"
        mock_standard.standard_text = "Create music"
        
        mock_objective = Mock()
        mock_objective.objective_text = "Create rhythmic patterns"
        
        lesson_agent.lesson_requirements.update({
            'grade_level': 'Kindergarten',
            'strand_code': 'CN',
            'strand_info': {'name': 'Creativity', 'description': 'Creating music'},
            'standard': mock_standard,
            'selected_objectives': [mock_objective],
            'additional_context': 'Focus on rhythm'
        })
        
        context = lesson_agent._build_lesson_context()
        
        assert isinstance(context, LessonPromptContext)
        assert context.grade_level == 'Kindergarten'
        assert context.strand_code == 'CN'
        assert context.strand_name == 'Creativity'
        assert context.strand_description == 'Creating music'
        assert context.standard_id == 'K.CN.1'
        assert context.standard_text == 'Create music'
        assert context.objectives == ['Create rhythmic patterns']
        assert context.additional_context == 'Focus on rhythm'
    
    def test_get_lesson_requirements(self, lesson_agent):
        """Test getting lesson requirements"""
        lesson_agent.lesson_requirements = {'grade_level': 'Kindergarten'}
        
        requirements = lesson_agent.get_lesson_requirements()
        
        assert requirements == {'grade_level': 'Kindergarten'}
        # Ensure it's a copy, not the original
        requirements['test'] = 'value'
        assert 'test' not in lesson_agent.lesson_requirements
    
    def test_get_generated_lesson(self, lesson_agent):
        """Test getting generated lesson"""
        lesson_agent.lesson_requirements['generated_lesson'] = "Test lesson"
        
        lesson = lesson_agent.get_generated_lesson()
        
        assert lesson == "Test lesson"
    
    def test_reset_conversation(self, lesson_agent):
        """Test resetting conversation"""
        lesson_agent.lesson_requirements = {'grade_level': 'Kindergarten'}
        lesson_agent.conversation_history = [{'test': 'message'}]
        lesson_agent.set_state("complete")
        
        lesson_agent.reset_conversation()
        
        assert lesson_agent.lesson_requirements == {}
        assert lesson_agent.conversation_history == []
        assert lesson_agent.get_state() == "welcome"
    
    def test_conversation_history_tracking(self, lesson_agent):
        """Test that conversation history is properly tracked"""
        lesson_agent.chat("quit")
        
        history = lesson_agent.get_conversation_history()
        
        assert len(history) == 2  # User message + assistant response
        assert history[0]['role'] == 'user'
        assert history[0]['content'] == 'quit'
        assert history[1]['role'] == 'assistant'
        assert 'Lesson generation cancelled' in history[1]['content']
