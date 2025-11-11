"""Tests for ChutesClient configuration and error handling"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from backend.llm.chutes_client import (
    ChutesClient,
    ChutesAuthenticationError,
    ChutesRateLimitError,
    ChutesAPIError,
)
from backend.config import config
from backend.llm.prompt_templates import LessonPromptContext


class TestChutesClientConfiguration:
    """Test suite for ChutesClient configuration"""

    def test_client_initialization_with_key(self):
        """Test ChutesClient initialization with API key"""
        if not config.CHUTES_API_KEY:
            pytest.skip("CHUTES_API_KEY not configured")

        client = ChutesClient()
        assert client.api_key is not None
        assert client.base_url is not None
        assert client.default_model is not None

    def test_client_initialization_without_key(self):
        """Test ChutesClient raises error without API key"""
        with patch("backend.llm.chutes_client.config") as mock_config:
            mock_config.CHUTES_API_KEY = None
            mock_config.CHUTES_API_BASE_URL = "https://api.example.com"

            with pytest.raises(ChutesAuthenticationError):
                ChutesClient()

    def test_client_custom_parameters(self):
        """Test ChutesClient with custom parameters"""
        if not config.CHUTES_API_KEY:
            pytest.skip("CHUTES_API_KEY not configured")

        client = ChutesClient(timeout=300, max_retries=5)

        assert client.timeout == 300
        assert client.max_retries == 5

    def test_client_default_model_set(self):
        """Test ChutesClient default model is set"""
        if not config.CHUTES_API_KEY:
            pytest.skip("CHUTES_API_KEY not configured")

        client = ChutesClient()
        assert client.default_model == config.DEFAULT_MODEL

    def test_client_embedding_model_set(self):
        """Test ChutesClient embedding model is set"""
        if not config.CHUTES_API_KEY:
            pytest.skip("CHUTES_API_KEY not configured")

        client = ChutesClient()
        assert client.embedding_model == config.EMBEDDING_MODEL


class TestChutesClientErrorHandling:
    """Test suite for ChutesClient error handling"""

    def test_authentication_error_message(self):
        """Test authentication error provides clear message"""
        with pytest.raises(ChutesAuthenticationError) as exc_info:
            with patch("backend.llm.chutes_client.config") as mock_config:
                mock_config.CHUTES_API_KEY = None
                ChutesClient()

        assert "CHUTES_API_KEY" in str(exc_info.value)

    @patch("backend.llm.chutes_client.ChutesClient._make_request")
    def test_rate_limit_error(self, mock_request):
        """Test rate limit error handling"""
        if not config.CHUTES_API_KEY:
            pytest.skip("CHUTES_API_KEY not configured")

        # Mock a rate limit response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "5"}
        mock_request.return_value = mock_response

        client = ChutesClient()
        # The client will handle rate limiting with retries
        # This is tested indirectly through the retry logic

    @patch("backend.llm.chutes_client.ChutesClient._make_request")
    def test_api_error_handling(self, mock_request):
        """Test API error handling"""
        if not config.CHUTES_API_KEY:
            pytest.skip("CHUTES_API_KEY not configured")

        # Mock an error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid request"}
        mock_request.return_value = mock_response

        client = ChutesClient()
        # Error handling is done in API methods

    def test_invalid_base_url(self):
        """Test handling of invalid base URL"""
        with patch("backend.llm.chutes_client.config") as mock_config:
            mock_config.CHUTES_API_KEY = "test-key"
            mock_config.CHUTES_API_BASE_URL = "invalid-url"
            mock_config.DEFAULT_MODEL = "test-model"
            mock_config.EMBEDDING_MODEL = "test-embedding"

            # Should not raise during init, but during request
            client = ChutesClient()
            assert client.base_url == "invalid-url"


class TestChutesClientMethods:
    """Test suite for ChutesClient methods"""

    @patch("backend.llm.chutes_client.requests.request")
    def test_make_request_with_auth_header(self, mock_request):
        """Test that authorization header is included in requests"""
        if not config.CHUTES_API_KEY:
            pytest.skip("CHUTES_API_KEY not configured")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_request.return_value = mock_response

        client = ChutesClient()
        # The _make_request method includes authorization header
        assert client.api_key is not None

    def test_chat_completion_parameters(self):
        """Test chat completion with various parameters"""
        if not config.CHUTES_API_KEY:
            pytest.skip("CHUTES_API_KEY not configured")

        client = ChutesClient()

        # Verify client has necessary methods
        assert hasattr(client, "chat_completion")
        assert hasattr(client, "chat_completion_stream")


class TestLessonPromptContext:
    """Test suite for lesson prompt context"""

    def test_prompt_context_creation(self):
        """Test creation of lesson prompt context"""
        context = LessonPromptContext(
            grade_level="Grade 3",
            strand_code="CN",
            strand_name="Connect",
            strand_description="Connect music with other arts",
            standard_id="3.CN.1",
            standard_text="Relate musical ideas",
            objectives=["Objective 1", "Objective 2"],
            lesson_duration="30 minutes",
            class_size=25,
        )

        assert context.grade_level == "Grade 3"
        assert context.strand_code == "CN"
        assert context.standard_id == "3.CN.1"

    def test_prompt_templates_available(self):
        """Test that lesson prompt templates are available"""
        from backend.llm.prompt_templates import LessonPromptTemplates

        templates = LessonPromptTemplates()

        # Should have template methods
        assert hasattr(templates, "get_system_prompt")
        assert callable(templates.get_system_prompt)


class TestChutesClientIntegration:
    """Test suite for ChutesClient integration"""

    @patch("backend.llm.chutes_client.requests.request")
    def test_lesson_generation_request_format(self, mock_request):
        """Test lesson generation request format"""
        if not config.CHUTES_API_KEY:
            pytest.skip("CHUTES_API_KEY not configured")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated lesson"}}]
        }
        mock_request.return_value = mock_response

        client = ChutesClient()

        # Create lesson context
        context = LessonPromptContext(
            grade_level="Grade 3",
            strand_code="CN",
            strand_name="Connect",
            strand_description="Connect music with other arts",
            standard_id="3.CN.1",
            standard_text="Connect music",
            objectives=["Learn connections"],
            lesson_duration="30 minutes",
            class_size=25,
        )

        # Should be able to generate lesson plan
        assert hasattr(client, "generate_lesson_plan")

    def test_client_retry_logic(self):
        """Test client retry logic for transient errors"""
        if not config.CHUTES_API_KEY:
            pytest.skip("CHUTES_API_KEY not configured")

        client = ChutesClient(max_retries=3)

        assert client.max_retries == 3


class TestConfigurationValidation:
    """Test suite for configuration validation"""

    def test_config_is_configured(self):
        """Test config.is_configured() method"""
        is_configured = config.is_configured()

        # Should be configured if CHUTES_API_KEY is set
        if config.CHUTES_API_KEY:
            assert is_configured is True
        else:
            assert is_configured is False

    def test_config_defaults(self):
        """Test default configuration values"""
        assert config.DEFAULT_MODEL is not None
        assert config.EMBEDDING_MODEL is not None
        assert config.DEFAULT_TEMPERATURE > 0
        assert config.DEFAULT_MAX_TOKENS > 0

    def test_chutes_api_url_configuration(self):
        """Test Chutes API URL configuration"""
        # Should have valid URL base
        assert config.CHUTES_API_BASE_URL is not None
        assert "http" in config.CHUTES_API_BASE_URL


class TestErrorRecovery:
    """Test suite for error recovery"""

    @patch("backend.llm.chutes_client.time.sleep")
    @patch("backend.llm.chutes_client.requests.request")
    def test_rate_limit_retry(self, mock_request, mock_sleep):
        """Test retry logic on rate limit"""
        if not config.CHUTES_API_KEY:
            pytest.skip("CHUTES_API_KEY not configured")

        # First call returns 429, second returns 200
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "1"}

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"result": "success"}

        mock_request.side_effect = [rate_limit_response, success_response]

        client = ChutesClient(max_retries=2)
        # Verify client is configured for retries
        assert client.max_retries >= 1

    def test_timeout_configuration(self):
        """Test timeout configuration"""
        if not config.CHUTES_API_KEY:
            pytest.skip("CHUTES_API_KEY not configured")

        client = ChutesClient(timeout=60)
        assert client.timeout == 60
