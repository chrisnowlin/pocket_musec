"""Tests for model selection API endpoints"""

import pytest
from unittest.mock import Mock, patch
from backend.api.routes.sessions import router
from backend.llm.model_router import ModelRouter


class TestModelSelection:
    """Test model selection endpoints"""

    def test_available_cloud_models(self):
        """Test that available cloud models are returned"""
        router_instance = ModelRouter()
        models = router_instance.get_available_cloud_models()

        assert isinstance(models, list)
        assert len(models) >= 2  # At least Qwen3-VL and Kimi-K2-Thinking

        # Check that each model has required fields
        for model in models:
            assert "id" in model
            assert "name" in model
            assert "description" in model
            assert "capabilities" in model
            assert "available" in model

    def test_kimi_k2_thinking_model_present(self):
        """Test that Kimi-K2-Thinking model is in the list"""
        router_instance = ModelRouter()
        models = router_instance.get_available_cloud_models()

        kimi_model = next((m for m in models if "Kimi-K2-Thinking" in m["id"]), None)

        assert kimi_model is not None
        assert kimi_model["name"] == "Kimi K2 Thinking"
        assert "reasoning" in kimi_model["capabilities"]

    def test_default_model_present(self):
        """Test that default Qwen3-VL model is in the list"""
        router_instance = ModelRouter()
        models = router_instance.get_available_cloud_models()

        qwen_model = next((m for m in models if "Qwen3-VL" in m["id"]), None)

        assert qwen_model is not None
        assert qwen_model["recommended"] is True
        assert "vision" in qwen_model["capabilities"]

    def test_model_availability_check(self):
        """Test model availability checking"""
        router_instance = ModelRouter()

        # Test with valid model
        assert (
            router_instance.is_model_available("Qwen/Qwen3-VL-235B-A22B-Instruct")
            is True
        )
        assert router_instance.is_model_available("moonshotai/Kimi-K2-Thinking") is True

        # Test with invalid model
        assert router_instance.is_model_available("invalid-model") is False

    def test_cloud_mode_required(self):
        """Test that models are only available in cloud mode"""
        with patch(
            "backend.llm.model_router.config.is_cloud_enabled", return_value=False
        ):
            router_instance = ModelRouter()
            models = router_instance.get_available_cloud_models()

            assert models == []

    @pytest.mark.skip(
        reason="TestClient incompatibility - pre-existing issue affecting all integration tests"
    )
    def test_get_available_models_endpoint(self, authenticated_client, test_session):
        """Test GET /api/sessions/{session_id}/models endpoint"""
        # Get available models
        response = authenticated_client.get(f"/api/sessions/{test_session.id}/models")

        assert response.status_code == 200
        data = response.json()

        assert "available_models" in data
        assert "current_model" in data
        assert "processing_mode" in data
        assert isinstance(data["available_models"], list)

    @pytest.mark.skip(
        reason="TestClient incompatibility - pre-existing issue affecting all integration tests"
    )
    def test_update_selected_model_endpoint(self, authenticated_client, test_session):
        """Test PUT /api/sessions/{session_id}/models endpoint"""
        # Update selected model
        response = authenticated_client.put(
            f"/api/sessions/{test_session.id}/models",
            json={"selected_model": "moonshotai/Kimi-K2-Thinking"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["selected_model"] == "moonshotai/Kimi-K2-Thinking"

    @pytest.mark.skip(
        reason="TestClient incompatibility - pre-existing issue affecting all integration tests"
    )
    def test_update_invalid_model_fails(self, authenticated_client, test_session):
        """Test that updating to invalid model fails"""
        # Try to update to invalid model
        response = authenticated_client.put(
            f"/api/sessions/{test_session.id}/models",
            json={"selected_model": "invalid-model-id"},
        )

        assert response.status_code == 400
        assert "not available" in response.json()["detail"].lower()

    def test_model_parameter_passed_to_llm(self):
        """Test that selected model is passed to LLM client"""
        from backend.pocketflow.lesson_agent import LessonAgent
        from backend.pocketflow.flow import Flow
        from backend.pocketflow.store import Store

        flow = Flow(name="test")
        store = Store()

        # Create agent with selected model
        agent = LessonAgent(
            flow=flow, store=store, selected_model="moonshotai/Kimi-K2-Thinking"
        )

        assert agent.selected_model == "moonshotai/Kimi-K2-Thinking"
