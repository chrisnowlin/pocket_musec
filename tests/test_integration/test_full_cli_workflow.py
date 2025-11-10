#!/usr/bin/env python3
"""Integration tests for the full CLI workflow"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cli.commands.generate import run_interactive_lesson_generation
from cli.commands.ingest import ingest_standards
from cli.commands.embed import generate_embeddings
from backend.utils.draft_history import DraftHistoryManager
from backend.repositories.standards_repository import StandardsRepository
from backend.pocketflow.lesson_agent import LessonAgent


class TestFullCLIWorkflow:
    """Test the complete CLI workflow from ingestion to lesson generation"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_standards_data(self):
        """Mock standards data for testing"""
        return [
            {
                'grade_level': 'Kindergarten',
                'strand_code': 'CN',
                'strand_name': 'Connect',
                'standard_id': 'K.CN.1.1',
                'standard_text': 'Execute rhythmic patterns',
                'objectives': [
                    'Students will clap quarter note patterns',
                    'Students will identify rhythmic patterns',
                    'Students will create simple rhythmic patterns'
                ]
            },
            {
                'grade_level': '1st Grade', 
                'strand_code': 'CR',
                'strand_name': 'Create and Respond',
                'standard_id': '1.CR.1.1',
                'standard_text': 'Create musical compositions',
                'objectives': [
                    'Students will compose simple melodies',
                    'Students will use musical notation',
                    'Students will perform original compositions'
                ]
            }
        ]
    
    def test_standards_ingestion_workflow(self, temp_workspace, mock_standards_data):
        """Test the complete standards ingestion workflow"""
        
        print("\n🧪 Testing Standards Ingestion Workflow...")
        
        # Mock the PDF parsing and database operations
        with patch('backend.ingestion.standards_parser.StandardsParser') as mock_parser, \
             patch('backend.repositories.database.DatabaseManager') as mock_db:
            
            # Configure mocks
            mock_parser_instance = Mock()
            mock_parser.return_value = mock_parser_instance
            mock_parser_instance.parse_standards.return_value = mock_standards_data
            
            mock_db_instance = Mock()
            mock_db.return_value = mock_db_instance
            
            # Test ingestion
            try:
                ingest_standards(
                    pdf_path=Path("test_standards.pdf"),
                    force_reingest=True
                )
                print("✅ Standards ingestion completed successfully")
                
                # Verify parser was called
                mock_parser_instance.parse_standards.assert_called_once()
                print("✅ Standards parser called correctly")
                
                # Verify database operations
                mock_db_instance.save_standards.assert_called_once_with(mock_standards_data)
                print("✅ Database save operations called correctly")
                
            except Exception as e:
                pytest.fail(f"Standards ingestion failed: {e}")
    
    def test_lesson_generation_workflow(self, temp_workspace, mock_standards_data):
        """Test the complete lesson generation workflow"""
        
        print("\n🧪 Testing Lesson Generation Workflow...")
        
        # Mock the lesson agent and its dependencies
        with patch('backend.pocketflow.lesson_agent.LessonAgent') as mock_agent_class, \
             patch('backend.repositories.standards_repository.StandardsRepository') as mock_repo_class, \
             patch('backend.llm.chutes_client.ChutesClient') as mock_client_class:
            
            # Configure mocks
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            # Mock conversation states
            mock_agent.get_state.side_effect = [
                "welcome", "grade_selection", "strand_selection", 
                "standard_selection", "objective_refinement", 
                "context_collection", "complete"
            ]
            
            # Mock responses
            mock_agent.chat.side_effect = [
                "Welcome to PocketMusec! Please select a grade level.",
                "Grade selected. Please select a strand.",
                "Strand selected. Please select a standard.",
                "Standard selected. Please select objectives.",
                "Objectives selected. Please provide additional context.",
                "Context received. Generating lesson...",
                "# Generated Lesson\n\n## Lesson Content\n\nThis is a test lesson."
            ]
            
            # Mock generated lesson and requirements
            mock_agent.get_generated_lesson.return_value = "# Generated Lesson\n\n## Lesson Content\n\nThis is a test lesson."
            mock_agent.get_lesson_requirements.return_value = {
                'grade_level': 'Kindergarten',
                'strand_code': 'CN',
                'strand_info': {'name': 'Connect'},
                'standard': {'standard_id': 'K.CN.1.1', 'standard_text': 'Execute rhythmic patterns'},
                'selected_objectives': mock_standards_data[0]['objectives'][:2],
                'additional_context': 'Test context for music lesson'
            }
            
            # Mock standards repository
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_grades.return_value = ['Kindergarten', '1st Grade', '2nd Grade']
            mock_repo.get_strands.return_value = [
                {'code': 'CN', 'name': 'Connect'},
                {'code': 'CR', 'name': 'Create and Respond'}
            ]
            mock_repo.get_standards_for_grade_strand.return_value = mock_standards_data
            
            # Test lesson generation
            try:
                with patch('rich.prompt.Prompt.ask', side_effect=[
                    '1',  # Select Kindergarten
                    '1',  # Select CN strand
                    '1',  # Select first standard
                    '1,2',  # Select first two objectives
                    'skip'  # Skip additional context
                ]), patch('rich.prompt.Confirm.ask', side_effect=[
                    True,  # View complete lesson
                    False,  # Don't edit
                    False   # Don't save to file
                ]):
                    
                    run_interactive_lesson_generation()
                    print("✅ Lesson generation completed successfully")
                
                # Verify agent was called through conversation
                assert mock_agent.chat.call_count > 0
                print("✅ Lesson agent interaction completed")
                
                # Verify lesson was generated
                mock_agent.get_generated_lesson.assert_called()
                print("✅ Lesson generation method called")
                
            except Exception as e:
                pytest.fail(f"Lesson generation failed: {e}")
    
    def test_draft_history_integration(self, temp_workspace):
        """Test draft history integration with lesson generation"""
        
        print("\n🧪 Testing Draft History Integration...")
        
        # Create draft manager
        draft_manager = DraftHistoryManager()
        
        # Test creating original draft
        original_content = """# Test Lesson

## Grade Level
Kindergarten

## Standard
K.CN.1.1

## Content
This is the original lesson content.
"""
        
        original_draft = draft_manager.create_draft(
            content=original_content,
            grade_level="Kindergarten",
            strand_code="CN",
            strand_name="Connect",
            standard_id="K.CN.1.1",
            objectives_count=3,
            is_original=True
        )
        
        assert original_draft.draft_id == "original"
        assert original_draft.has_edits == False
        print("✅ Original draft created successfully")
        
        # Test creating edited drafts
        edited_content = """# Test Lesson (Edited)

## Grade Level
Kindergarten

## Standard
K.CN.1.1

## Content
This is the edited lesson content with additions.
"""
        
        edited_draft = draft_manager.create_draft(
            content=edited_content,
            grade_level="Kindergarten",
            strand_code="CN",
            strand_name="Connect",
            standard_id="K.CN.1.1",
            objectives_count=3,
            is_original=False
        )
        
        assert edited_draft.draft_id == "draft_1"
        assert edited_draft.has_edits == True
        print("✅ Edited draft created successfully")
        
        # Test draft retrieval
        retrieved_content = draft_manager.get_draft_content("original")
        assert retrieved_content == original_content
        print("✅ Draft content retrieval working")
        
        # Test workspace cleanup
        draft_manager.cleanup_workspace()
        assert not draft_manager.workspace.exists()
        print("✅ Workspace cleanup working")
    
    def test_embeddings_generation_workflow(self, temp_workspace, mock_standards_data):
        """Test the embeddings generation workflow"""
        
        print("\n🧪 Testing Embeddings Generation Workflow...")
        
        with patch('backend.repositories.standards_repository.StandardsRepository') as mock_repo_class, \
             patch('backend.llm.embeddings.EmbeddingsGenerator') as mock_embed_class:
            
            # Configure mocks
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_all_standards.return_value = mock_standards_data
            
            mock_embed = Mock()
            mock_embed_class.return_value = mock_embed
            mock_embed.generate_embeddings.return_value = [[0.1, 0.2, 0.3] for _ in mock_standards_data]
            
            # Test embeddings generation
            try:
                generate_embeddings()
                print("✅ Embeddings generation completed successfully")
                
                # Verify repository was queried
                mock_repo.get_all_standards.assert_called_once()
                print("✅ Standards repository queried correctly")
                
                # Verify embeddings were generated
                mock_embed.generate_embeddings.assert_called_once_with(mock_standards_data)
                print("✅ Embeddings generated correctly")
                
            except Exception as e:
                pytest.fail(f"Embeddings generation failed: {e}")
    
    def test_error_handling_workflow(self, temp_workspace):
        """Test error handling throughout the workflow"""
        
        print("\n🧪 Testing Error Handling Workflow...")
        
        # Test draft manager error handling
        try:
            # Create draft manager with invalid session ID (should handle gracefully)
            draft_manager = DraftHistoryManager("invalid_session")
            
            # Try to get non-existent draft
            result = draft_manager.get_draft("non_existent")
            assert result is None
            print("✅ Non-existent draft handled gracefully")
            
            # Try to get content from non-existent draft
            content = draft_manager.get_draft_content("non_existent")
            assert content is None
            print("✅ Non-existent draft content handled gracefully")
            
        except Exception as e:
            pytest.fail(f"Error handling test failed: {e}")
        
        # Test cleanup error handling
        try:
            draft_manager = DraftHistoryManager()
            # Manually remove workspace to test cleanup error handling
            if draft_manager.workspace.exists():
                shutil.rmtree(draft_manager.workspace)
            
            # Should not raise exception
            draft_manager.cleanup_workspace()
            print("✅ Cleanup error handling working")
            
        except Exception as e:
            pytest.fail(f"Cleanup error handling failed: {e}")
    
    def test_full_integration_scenario(self, temp_workspace, mock_standards_data):
        """Test a complete integration scenario"""
        
        print("\n🧪 Testing Full Integration Scenario...")
        
        try:
            # Step 1: Initialize draft manager
            draft_manager = DraftHistoryManager()
            print("✅ Step 1: Draft manager initialized")
            
            # Step 2: Create original lesson draft
            lesson_content = """# Music Lesson: Rhythm and Movement

## Grade Level
Kindergarten

## Strand
Connect (CN)

## Standard
K.CN.1.1 - Execute rhythmic patterns

## Learning Objectives
1. Students will clap quarter note and eighth note patterns
2. Students will identify rhythmic patterns in music
3. Students will create their own rhythmic patterns

## Lesson Activities
1. Warm-up: Call and response clapping
2. Introduction: Quarter and eighth note notation
3. Practice: Rhythm reading exercises
4. Creation: Student composition time
5. Performance: Share student compositions

## Assessment
- Observation of participation
- Rhythm reading accuracy
- Original rhythm pattern creation
"""
            
            original_draft = draft_manager.create_draft(
                content=lesson_content,
                grade_level="Kindergarten",
                strand_code="CN",
                strand_name="Connect",
                standard_id="K.CN.1.1",
                objectives_count=3,
                is_original=True
            )
            print("✅ Step 2: Original lesson draft created")
            
            # Step 3: Simulate editing workflow
            edited_lesson = lesson_content + """

## Modifications
- Added instrument exploration activity
- Extended assessment criteria
- Added differentiation strategies
"""
            
            edited_draft = draft_manager.create_draft(
                content=edited_lesson,
                grade_level="Kindergarten",
                strand_code="CN",
                strand_name="Connect",
                standard_id="K.CN.1.1",
                objectives_count=4,
                is_original=False
            )
            print("✅ Step 3: Edited lesson draft created")
            
            # Step 4: Verify draft history
            all_drafts = draft_manager.list_drafts()
            assert len(all_drafts) == 2
            assert all_drafts[0].draft_id == "original"
            assert all_drafts[1].draft_id == "draft_1"
            print("✅ Step 4: Draft history verified")
            
            # Step 5: Test content retrieval
            retrieved_original = draft_manager.get_draft_content("original")
            retrieved_edited = draft_manager.get_draft_content("draft_1")
            
            assert lesson_content in retrieved_original
            assert "Modifications" in retrieved_edited
            print("✅ Step 5: Content retrieval verified")
            
            # Step 6: Test workspace info
            workspace_info = draft_manager.get_workspace_info()
            assert workspace_info['total_drafts'] == 2
            assert workspace_info['session_id'] == draft_manager.session_id
            print("✅ Step 6: Workspace info verified")
            
            # Step 7: Cleanup
            draft_manager.cleanup_workspace()
            print("✅ Step 7: Workspace cleanup completed")
            
            print("🎉 Full integration scenario completed successfully!")
            
        except Exception as e:
            pytest.fail(f"Full integration scenario failed: {e}")


if __name__ == "__main__":
    # Run tests manually if called directly
    import unittest
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFullCLIWorkflow)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)