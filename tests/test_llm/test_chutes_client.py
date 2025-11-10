"""Tests for Chutes LLM client integration"""

import pytest
import os
import requests
from unittest.mock import Mock, patch, MagicMock
from backend.llm.chutes_client import ChutesClient
from backend.llm.prompt_templates import LessonPromptContext, LessonPromptTemplates


class TestChutesClient:
    """Test cases for ChutesClient"""

    @pytest.fixture
    def client(self):
        """Create a ChutesClient instance for testing"""
        # Use test API key if available, otherwise mock
        api_key = os.getenv("CHUTES_API_KEY", "test-key")
        return ChutesClient(api_key=api_key)

    @pytest.fixture
    def sample_context(self):
        """Create sample lesson context for testing"""
        return LessonPromptContext(
            grade_level="3rd Grade",
            strand_code="M.CR",
            strand_name="Musical Creation",
            strand_description="Creating, composing, and improvising music",
            standard_id="3.M.CR.1",
            standard_text="Create rhythmic patterns using quarter notes and eighth notes",
            objectives=["Create simple rhythmic patterns", "Perform rhythmic patterns accurately"],
            lesson_duration="45 minutes",
            class_size=25,
            available_resources=["classroom percussion instruments", "whiteboard"]
        )

    def test_client_initialization(self, client):
        """Test that ChutesClient initializes correctly"""
        assert client.api_key is not None
        assert client.base_url == "https://api.chutes.ai/v1"
        assert client.default_model == "Qwen/Qwen3-VL-235B-A22B-Instruct"
        assert client.embedding_model == "Qwen/Qwen3-Embedding-8B"

    def test_client_initialization_with_custom_config(self):
        """Test client initialization with custom configuration"""
        client = ChutesClient(
            api_key="custom-key",
            base_url="https://custom.api.com",
            default_model="custom-model"
        )
        assert client.api_key == "custom-key"
        assert client.base_url == "https://custom.api.com"
        assert client.default_model == "custom-model"

    @patch('backend.llm.chutes_client.requests.request')
    def test_generate_lesson_plan_success(self, mock_request, client, sample_context):
        """Test successful lesson plan generation"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "## Lesson Overview\n\nThis is a test lesson plan..."
                }
            }],
            "model": client.default_model
        }
        mock_request.return_value = mock_response
        client.max_retries = 2

        # Generate lesson plan
        result = client.generate_lesson_plan(sample_context)

        # Verify result
        assert result is not None
        assert "Lesson Overview" in result
        assert "test lesson plan" in result

        # Verify API call was made correctly
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]["method"] == 'POST'
        assert "chat/completions" in call_args[1]["url"]
        assert call_args[1]["headers"]["Authorization"] == f"Bearer {client.api_key}"

    @patch('backend.llm.chutes_client.requests.request')
    def test_generate_lesson_plan_with_streaming(self, mock_request, client, sample_context):
        """Test lesson plan generation with streaming"""
        # Mock streaming response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"content": "## "}}]}',
            b'data: {"choices": [{"delta": {"content": "Lesson"}}]}',
            b'data: {"choices": [{"delta": {"content": " Overview"}}]}',
            b'data: [DONE]'
        ]
        mock_request.return_value = mock_response

        # Generate with streaming
        result = client.generate_lesson_plan(sample_context, stream=True)

        # Verify streaming result
        assert result is not None
        chunks = list(result)
        assert len(chunks) > 0
        assert any("Lesson" in chunk for chunk in chunks)

    @patch('backend.llm.chutes_client.requests.request')
    def test_generate_lesson_plan_retry_logic(self, mock_request, client, sample_context):
        """Test retry logic on API failure"""
        # Mock failed response then success
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.HTTPError("Server error")

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Success after retry"
                }
            }],
            "model": client.default_model
        }

        mock_request.side_effect = [mock_response_fail, mock_response_success]

        # Generate lesson plan
        result = client.generate_lesson_plan(sample_context)

        # Verify retry happened and result is successful
        assert result == "Success after retry"
        assert mock_request.call_count == 2

    @patch('backend.llm.chutes_client.requests.request')
    def test_generate_lesson_plan_max_retries_exceeded(self, mock_request, client, sample_context):
        """Test behavior when max retries are exceeded"""
        # Mock always failing response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Persistent server error")
        mock_request.return_value = mock_response

        # Should raise exception after max retries
        with pytest.raises(Exception, match="Persistent server error"):
            client.generate_lesson_plan(sample_context, max_retries=2)

        # Verify retry attempts
        assert mock_request.call_count == client.max_retries

    @patch('backend.llm.chutes_client.requests.request')
    def test_generate_embeddings_success(self, mock_request, client):
        """Test successful embedding generation"""
        # Mock successful embedding response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                    "index": 0
                },
                {
                    "embedding": [0.6, 0.7, 0.8, 0.9, 1.0],
                    "index": 1
                }
            ]
        }
        mock_request.return_value = mock_response

        # Generate embeddings
        texts = ["Create rhythmic patterns", "Perform musical compositions"]
        result = client.generate_embeddings(texts)

        # Verify result
        assert result is not None
        assert len(result) == 2
        assert len(result[0]) == 5  # 5-dimensional embedding
        assert result[0] == [0.1, 0.2, 0.3, 0.4, 0.5]

    @patch('backend.llm.chutes_client.requests.request')
    def test_generate_embeddings_batch_processing(self, mock_request, client):
        """Test embedding generation with batch processing"""
        # Mock response for multiple texts
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1, 0.2, 0.3], "index": 0},
                {"embedding": [0.4, 0.5, 0.6], "index": 1},
                {"embedding": [0.7, 0.8, 0.9], "index": 2}
            ]
        }
        mock_request.return_value = mock_response

        # Generate embeddings for multiple texts
        texts = ["text1", "text2", "text3"]
        result = client.generate_embeddings(texts)

        # Verify batch processing
        assert len(result) == 3
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        assert result[2] == [0.7, 0.8, 0.9]

    def test_prepare_messages(self, client, sample_context):
        """Test message preparation for API calls"""
        messages = client._prepare_messages(sample_context)

        # Verify message structure
        assert len(messages) == 2  # System and user messages
        assert messages[0].role == "system"
        assert messages[1].role == "user"
        assert "expert music education curriculum specialist" in messages[0].content
        assert "3rd Grade" in messages[1].content
        assert "M.CR" in messages[1].content

    def test_prepare_messages_with_custom_template(self, client, sample_context):
        """Test message preparation with custom template"""
        messages = client._prepare_messages(
            sample_context, 
            template_type="activity_ideas"
        )

        # Verify custom template is used
        assert len(messages) == 2
        assert "creative, engaging music activities" in messages[1].content

    def test_prepare_messages_invalid_template(self, client, sample_context):
        """Test error handling for invalid template type"""
        with pytest.raises(ValueError, match="Unknown template type"):
            client._prepare_messages(sample_context, template_type="invalid")

    def test_build_prompt_context(self, client):
        """Test building prompt context from standard data"""
        standard_data = {
            "grade_level": "5th Grade",
            "strand_code": "M.PR",
            "strand_name": "Musical Performance",
            "strand_description": "Performing music with technical accuracy and expression",
            "standard_id": "5.M.PR.1",
            "standard_text": "Perform melodies with accurate pitch and rhythm",
            "objectives": [
                "Perform simple melodies with accurate pitch",
                "Maintain steady tempo while performing"
            ],
            "lesson_duration": "50 minutes",
            "class_size": 30,
            "available_resources": ["recorders", "piano", "sheet music"]
        }

        context = client.build_prompt_context(standard_data)

        # Verify context creation
        assert isinstance(context, LessonPromptContext)
        assert context.grade_level == "5th Grade"
        assert context.strand_code == "M.PR"
        assert len(context.objectives) == 2
        assert context.lesson_duration == "50 minutes"
        assert context.class_size == 30

    def test_build_prompt_context_with_minimal_data(self, client):
        """Test building context with minimal required data"""
        minimal_data = {
            "grade_level": "2nd Grade",
            "strand_code": "M.RE",
            "strand_name": "Musical Response",
            "strand_description": "Responding to music through analysis and evaluation",
            "standard_id": "2.M.RE.1",
            "standard_text": "Identify high and low sounds in music",
            "objectives": ["Distinguish between high and low pitches"]
        }

        context = client.build_prompt_context(minimal_data)

        # Verify minimal context
        assert context.grade_level == "2nd Grade"
        assert context.lesson_duration is None  # Should use default
        assert context.class_size is None
        assert context.available_resources is None

    @patch('backend.llm.chutes_client.requests.request')
    def test_api_error_handling(self, mock_request, client, sample_context):
        """Test handling of API errors"""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid request format",
                "type": "invalid_request_error"
            }
        }
        mock_request.return_value = mock_response

        # Should handle error gracefully
        with pytest.raises(Exception):
            client.generate_lesson_plan(sample_context)

    def test_rate_limiting_configuration(self, client):
        """Test rate limiting configuration"""
        # Verify rate limiting parameters
        assert hasattr(client, 'rate_limit_delay')
        assert client.rate_limit_delay > 0

    @patch('backend.llm.chutes_client.requests.request')
    def test_custom_parameters(self, mock_request, client, sample_context):
        """Test API calls with custom parameters"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Custom parameter response"
                }
            }],
            "model": client.default_model
        }
        mock_request.return_value = mock_response

        # Generate with custom parameters
        client.generate_lesson_plan(
            sample_context,
            temperature=0.8,
            max_tokens=1500,
            top_p=0.95
        )

        # Verify custom parameters were passed
        call_args = mock_request.call_args
        request_data = call_args[1]["json"]
        assert request_data["temperature"] == 0.8
        assert request_data["max_tokens"] == 1500
        assert request_data["top_p"] == 0.95

    def test_model_validation(self):
        """Test model validation during initialization"""
        # Should accept valid model names
        client1 = ChutesClient(api_key="test", default_model="Qwen/Qwen3-VL-235B-A22B-Instruct")
        client2 = ChutesClient(api_key="test", default_model="custom-model-name")
        
        assert client1.default_model == "Qwen/Qwen3-VL-235B-A22B-Instruct"
        assert client2.default_model == "custom-model-name"

    @patch('backend.llm.chutes_client.requests.request')
    def test_streaming_parsing(self, mock_request, client, sample_context):
        """Test proper parsing of streaming responses"""
        # Mock streaming with various formats
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"content": "Hello"}}]}',
            b'data: {"choices": [{"delta": {"content": " world"}}]}',
            b'',  # Empty line
            b'data: {"choices": [{"delta": {"content": "!"}}]}',
            b'data: [DONE]'
        ]
        mock_request.return_value = mock_response

        # Generate with streaming
        result = client.generate_lesson_plan(sample_context, stream=True)
        chunks = list(result)

        # Verify proper parsing
        assert len(chunks) == 3
        assert chunks[0] == "Hello"
        assert chunks[1] == " world"
        assert chunks[2] == "!"


class TestLessonPromptTemplates:
    """Test cases for LessonPromptTemplates"""

    @pytest.fixture
    def sample_context(self):
        """Create sample lesson context for testing"""
        return LessonPromptContext(
            grade_level="4th Grade",
            strand_code="M.CR",
            strand_name="Musical Creation",
            strand_description="Creating and composing music",
            standard_id="4.M.CR.1",
            standard_text="Compose simple melodies using pentatonic scales",
            objectives=["Create melodies using pentatonic scales", "Notate original compositions"],
            lesson_duration="45 minutes",
            class_size=25,
            available_resources=["xylophones", "notation software"]
        )

    def test_system_prompt_structure(self):
        """Test system prompt has proper structure"""
        system_prompt = LessonPromptTemplates.get_system_prompt()
        
        # Verify XML tags are present
        assert "<role>" in system_prompt
        assert "</role>" in system_prompt
        assert "<expertise>" in system_prompt
        assert "</expertise>" in system_prompt
        assert "<instructions>" in system_prompt
        assert "</instructions>" in system_prompt
        assert "<output_format>" in system_prompt
        assert "</output_format>" in system_prompt

    def test_lesson_plan_prompt_generation(self, sample_context):
        """Test lesson plan prompt generation"""
        prompt = LessonPromptTemplates.generate_lesson_plan_prompt(sample_context)
        
        # Verify prompt contains context information
        assert "4th Grade" in prompt
        assert "M.CR" in prompt
        assert "Musical Creation" in prompt
        assert "4.M.CR.1" in prompt
        assert "pentatonic scales" in prompt
        assert "45 minutes" in prompt
        assert "<class_size>25</class_size>" in prompt

    def test_activity_ideas_prompt_generation(self, sample_context):
        """Test activity ideas prompt generation"""
        prompt = LessonPromptTemplates.generate_activity_ideas_prompt(sample_context)
        
        # Verify activity-specific content
        assert "creative, engaging music activities" in prompt
        assert "4th Grade" in prompt
        assert "pentatonic scales" in prompt

    def test_assessment_prompt_generation(self, sample_context):
        """Test assessment prompt generation"""
        prompt = LessonPromptTemplates.generate_assessment_prompt(sample_context)
        
        # Verify assessment-specific content
        assert "comprehensive assessment strategies" in prompt
        assert "Formative Assessment" in prompt
        assert "Summative Assessment" in prompt

    def test_differentiation_prompt_generation(self, sample_context):
        """Test differentiation prompt generation"""
        prompt = LessonPromptTemplates.generate_differentiation_prompt(sample_context)
        
        # Verify differentiation-specific content
        assert "differentiation strategies" in prompt
        assert "diverse learning styles" in prompt
        assert "English language learners" in prompt

    def test_cross_curricular_prompt_generation(self, sample_context):
        """Test cross-curricular prompt generation"""
        prompt = LessonPromptTemplates.generate_cross_curricular_prompt(sample_context)
        
        # Verify cross-curricular content
        assert "cross-curricular connections" in prompt
        assert "Mathematics" in prompt
        assert "Language Arts" in prompt
        assert "Social Studies" in prompt

    def test_reflection_prompt_generation(self, sample_context):
        """Test reflection prompt generation"""
        prompt = LessonPromptTemplates.generate_reflection_prompt(sample_context)
        
        # Verify reflection-specific content
        assert "reflection questions" in prompt
        assert "metacognitive activities" in prompt
        assert "Artistic Reflection" in prompt

    def test_parent_communication_prompt_generation(self, sample_context):
        """Test parent communication prompt generation"""
        prompt = LessonPromptTemplates.generate_parent_communication_prompt(sample_context)
        
        # Verify parent communication content
        assert "parent communication" in prompt
        assert "Newsletter article" in prompt
        assert "At-home practice" in prompt

    def test_technology_integration_prompt_generation(self, sample_context):
        """Test technology integration prompt generation"""
        prompt = LessonPromptTemplates.generate_technology_integration_prompt(sample_context)
        
        # Verify technology integration content
        assert "technology integration" in prompt
        assert "Digital audio tools" in prompt
        assert "Music education apps" in prompt

    def test_culturally_responsive_prompt_generation(self, sample_context):
        """Test culturally responsive prompt generation"""
        prompt = LessonPromptTemplates.generate_culturally_responsive_prompt(sample_context)
        
        # Verify culturally responsive content
        assert "culturally responsive teaching" in prompt
        assert "diverse musical traditions" in prompt
        assert "social justice" in prompt.lower()

    def test_get_all_templates(self):
        """Test getting all available templates"""
        templates = LessonPromptTemplates.get_all_templates()
        
        # Verify all expected templates are present
        expected_templates = [
            "lesson_plan",
            "activity_ideas", 
            "assessment",
            "differentiation",
            "cross_curricular",
            "reflection",
            "parent_communication",
            "technology_integration",
            "culturally_responsive"
        ]
        
        for template_name in expected_templates:
            assert template_name in templates
            assert callable(templates[template_name])

    def test_generate_prompt_with_valid_template(self, sample_context):
        """Test generating prompt with valid template type"""
        prompt = LessonPromptTemplates.generate_prompt(
            "lesson_plan", 
            sample_context
        )
        
        assert prompt is not None
        assert "4th Grade" in prompt

    def test_generate_prompt_with_invalid_template(self, sample_context):
        """Test error handling for invalid template type"""
        with pytest.raises(ValueError, match="Unknown template type"):
            LessonPromptTemplates.generate_prompt(
                "invalid_template", 
                sample_context
            )

    def test_comprehensive_lesson_prompt(self, sample_context):
        """Test comprehensive lesson prompt generation"""
        prompt = LessonPromptTemplates.create_comprehensive_lesson_prompt(sample_context)
        
        # Verify comprehensive content
        assert "comprehensive, standards-based music lesson plan" in prompt
        assert "additional_requirements" in prompt.lower()
        assert "quality_standards" in prompt.lower()

    def test_prompt_context_with_optional_fields(self):
        """Test prompt context with optional fields"""
        context = LessonPromptContext(
            grade_level="1st Grade",
            strand_code="M.RE",
            strand_name="Musical Response", 
            strand_description="Responding to music",
            standard_id="1.M.RE.1",
            standard_text="Identify steady beat",
            objectives=["Maintain steady beat"],
            additional_context="Students have previous experience with clapping rhythms",
            lesson_duration="30 minutes",
            class_size=20,
            available_resources=["drums", "rhythm sticks"]
        )
        
        prompt = LessonPromptTemplates.generate_lesson_plan_prompt(context)
        
        # Verify optional fields are included
        assert "additional_context" in prompt.lower()
        assert "30 minutes" in prompt
        assert "<class_size>20</class_size>" in prompt
        assert "drums" in prompt

    def test_prompt_context_without_optional_fields(self):
        """Test prompt context without optional fields"""
        context = LessonPromptContext(
            grade_level="Kindergarten",
            strand_code="M.PR",
            strand_name="Musical Performance",
            strand_description="Performing music",
            standard_id="K.M.PR.1", 
            standard_text="Sing simple songs",
            objectives=["Sing with accurate pitch"]
        )
        
        prompt = LessonPromptTemplates.generate_lesson_plan_prompt(context)
        
        # Verify defaults are used
        assert "45 minutes" in prompt  # Default duration
        assert "<class_size>25 students</class_size>" in prompt  # Default class size
        assert "standard classroom instruments" in prompt  # Default resources

    def test_xml_tag_formatting(self, sample_context):
        """Test proper XML tag formatting in prompts"""
        prompt = LessonPromptTemplates.generate_lesson_plan_prompt(sample_context)
        
        # Verify proper XML tag structure
        assert prompt.startswith("<task>")
        assert prompt.endswith("</quality_criteria>")
        
        # Check for properly closed tags
        open_tags = ["<task>", "<context>", "<grade_level>", "<strand>", "<code>", 
                    "<name>", "<description>", "<standard>", "<id>", "<text>",
                    "<learning_objectives>", "<lesson_parameters>", "<duration>",
                    "<class_size>", "<available_resources>", "<requirements>",
                    "<structure>", "<quality_criteria>"]
        
        for tag in open_tags:
            assert tag in prompt
            close_tag = tag.replace("<", "</")
            assert close_tag in prompt
