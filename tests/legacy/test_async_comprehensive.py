"""
Comprehensive test suite for async improvements in lesson_agent.py

Tests:
1. Event loop handling in sync wrappers
2. Error handling and fallbacks
3. Method signature compatibility
4. Integration with state handlers
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.pocketflow.lesson_agent import LessonAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store


class TestAsyncWrappers:
    """Test async wrapper methods"""

    def test_async_methods_are_coroutines(self):
        """Verify async methods are actually coroutines"""
        flow = Flow("test_flow")
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)

        # Check that async methods are coroutine functions
        assert asyncio.iscoroutinefunction(agent._async_llm_chat_completion)
        assert asyncio.iscoroutinefunction(agent._async_llm_generate_lesson_plan)
        assert asyncio.iscoroutinefunction(agent._async_analyze_user_message)
        assert asyncio.iscoroutinefunction(agent._generate_conversational_response)
        assert asyncio.iscoroutinefunction(agent._generate_lesson_plan)
        assert asyncio.iscoroutinefunction(agent._handle_conversational_welcome)

    def test_sync_wrappers_are_not_coroutines(self):
        """Verify sync wrappers are normal functions"""
        flow = Flow("test_flow")
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)

        # Check that sync wrappers are NOT coroutine functions
        assert not asyncio.iscoroutinefunction(
            agent._generate_conversational_response_sync
        )
        assert not asyncio.iscoroutinefunction(agent._generate_lesson_plan_sync)
        assert not asyncio.iscoroutinefunction(
            agent._handle_conversational_welcome_sync
        )
        assert not asyncio.iscoroutinefunction(agent._handle_generation_sync)


class TestLLMClientHandling:
    """Test LLM client availability handling"""

    @pytest.mark.asyncio
    async def test_async_llm_with_unavailable_client(self):
        """Test async LLM wrapper when client is unavailable"""
        flow = Flow("test_flow")
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)

        # Mock unavailable client
        agent.llm_client = None

        messages = [{"role": "user", "content": "test"}]
        response = await agent._async_llm_chat_completion(messages)

        # Should return a fallback response with content attribute
        assert hasattr(response, "content")
        assert "unable to process" in response.content.lower()

    @pytest.mark.asyncio
    async def test_async_llm_generate_with_unavailable_client(self):
        """Test async lesson plan generation when client is unavailable"""
        flow = Flow("test_flow")
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)

        # Mock unavailable client
        agent.llm_client = None

        from backend.llm.prompt_templates import LessonPromptContext

        context = LessonPromptContext(
            grade_level="Third Grade",
            strand_code="CR",
            strand_name="Create",
            strand_description="Creating music",
            standard_id="3.CR.1",
            standard_text="Test standard",
            objectives=["Test objective"],
        )

        response = await agent._async_llm_generate_lesson_plan(context)

        # Should return a fallback message
        assert isinstance(response, str)
        assert "unable to generate" in response.lower()


class TestSyncWrapperEventLoopHandling:
    """Test sync wrappers handle event loops correctly"""

    def test_sync_wrapper_with_no_running_loop(self):
        """Test sync wrapper when no event loop is running"""
        flow = Flow("test_flow")
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)

        # Mock the LLM client to avoid actual API calls
        agent.llm_client = None

        message = "Test message"
        extracted_info = {"grade_level": "Third Grade", "musical_topics": ["rhythm"]}
        relevant_standards = []

        # This should not raise an exception
        result = agent._generate_conversational_response_sync(
            message, extracted_info, relevant_standards
        )

        assert isinstance(result, str)
        assert len(result) > 0


class TestFallbackMethods:
    """Test fallback methods when async operations fail"""

    def test_fallback_lesson_generation(self):
        """Test fallback lesson generation"""
        flow = Flow("test_flow")
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)

        fallback = agent._generate_fallback_lesson()

        assert isinstance(fallback, str)
        assert "lesson plan" in fallback.lower()
        assert len(fallback) > 100  # Should have substantial content

    def test_fallback_welcome(self):
        """Test fallback welcome message"""
        flow = Flow("test_flow")
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)

        message = "I need help with a lesson"
        fallback = agent._generate_fallback_welcome(message)

        assert isinstance(fallback, str)
        assert "welcome" in fallback.lower()
        assert message in fallback


class TestStateHandlerIntegration:
    """Test integration with state handler system"""

    def test_state_handlers_registered(self):
        """Verify all state handlers are properly registered"""
        flow = Flow("test_flow")
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)

        # Check conversational mode handlers are registered
        assert "conversational_welcome" in agent.state_handlers
        assert "lesson_planning" in agent.state_handlers
        assert "generation" in agent.state_handlers
        assert "refinement" in agent.state_handlers

    def test_state_handlers_are_callable(self):
        """Verify state handlers are callable (not coroutines)"""
        flow = Flow("test_flow")
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)

        # State handlers should be callable sync functions
        for state, handler in agent.state_handlers.items():
            assert callable(handler)
            # Should NOT be coroutine functions (sync interface required)
            assert not asyncio.iscoroutinefunction(handler), (
                f"Handler for {state} should be sync"
            )


class TestErrorHandling:
    """Test error handling throughout async operations"""

    def test_sync_wrapper_handles_exceptions(self):
        """Test sync wrapper gracefully handles exceptions"""
        flow = Flow("test_flow")
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)

        # Force an error by mocking the async method to raise an exception
        async def mock_error(*args, **kwargs):
            raise RuntimeError("Test error")

        agent._generate_conversational_response = mock_error

        message = "Test"
        extracted_info = {}
        relevant_standards = []

        # Should not raise - should return fallback
        result = agent._generate_conversational_response_sync(
            message, extracted_info, relevant_standards
        )

        assert isinstance(result, str)
        assert len(result) > 0


class TestBackwardCompatibility:
    """Test backward compatibility with existing code"""

    def test_chat_method_is_sync(self):
        """Verify chat() method remains synchronous"""
        flow = Flow("test_flow")
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)

        # chat() should NOT be a coroutine function
        assert not asyncio.iscoroutinefunction(agent.chat)

    def test_chat_returns_string(self):
        """Verify chat() returns a string (not a coroutine)"""
        flow = Flow("test_flow")
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)

        # Mock LLM client to avoid API calls
        agent.llm_client = None

        result = agent.chat("Hello")

        # Should return a string immediately, not a coroutine
        assert isinstance(result, str)
        assert not asyncio.iscoroutine(result)


class TestAsyncToThreadUsage:
    """Test that asyncio.to_thread is used correctly"""

    @pytest.mark.asyncio
    async def test_async_llm_uses_to_thread(self):
        """Verify async wrappers use asyncio.to_thread for blocking calls"""
        flow = Flow("test_flow")
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)

        # Mock the LLM client
        mock_client = Mock()
        mock_client.is_available = Mock(return_value=True)
        mock_client.chat_completion = Mock(return_value=Mock(content="Test response"))

        agent.llm_client = mock_client

        messages = [{"role": "user", "content": "test"}]

        # This should complete without blocking
        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = Mock(content="Mocked response")
            await agent._async_llm_chat_completion(messages)

            # Verify asyncio.to_thread was called
            assert mock_to_thread.called


def test_all_async_improvements():
    """Meta-test to verify all improvements are in place"""
    flow = Flow("test_flow")
    store = Store()
    agent = LessonAgent(flow, store, conversational_mode=True)

    improvements = {
        "async_llm_chat_completion": hasattr(agent, "_async_llm_chat_completion"),
        "async_llm_generate_lesson_plan": hasattr(
            agent, "_async_llm_generate_lesson_plan"
        ),
        "async_analyze_user_message": hasattr(agent, "_async_analyze_user_message"),
        "generate_conversational_response_sync": hasattr(
            agent, "_generate_conversational_response_sync"
        ),
        "generate_lesson_plan_sync": hasattr(agent, "_generate_lesson_plan_sync"),
        "handle_conversational_welcome_sync": hasattr(
            agent, "_handle_conversational_welcome_sync"
        ),
        "handle_generation_sync": hasattr(agent, "_handle_generation_sync"),
        "generate_fallback_lesson": hasattr(agent, "_generate_fallback_lesson"),
        "generate_fallback_welcome": hasattr(agent, "_generate_fallback_welcome"),
    }

    missing = [name for name, exists in improvements.items() if not exists]
    assert not missing, f"Missing improvements: {missing}"

    print("\n✓ All async improvements verified:")
    for name in improvements.keys():
        print(f"  ✓ {name}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
