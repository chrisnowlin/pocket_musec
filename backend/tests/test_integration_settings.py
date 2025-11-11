"""
Integration tests for settings and processing mode system.

Tests the processing mode toggle functionality including:
- Listing available modes
- Switching between cloud and local modes
- Local model status checking
"""

import pytest
import os
import tempfile
from fastapi.testclient import TestClient

# Add backend to path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestProcessingModes:
    """Test processing mode endpoints."""

    def test_list_processing_modes(self, client):
        """Test listing available processing modes."""
        response = client.get("/api/settings/processing-modes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

        # Check that cloud and local modes are available
        mode_names = [mode["name"] for mode in data]
        assert "cloud" in mode_names
        assert "local" in mode_names

    def test_get_current_processing_mode(self, client):
        """Test getting current processing mode."""
        response = client.get("/api/settings/processing-mode")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "display_name" in data
        assert "description" in data
        assert data["name"] in ["cloud", "local"]

    def test_switch_to_cloud_mode(self, client):
        """Test switching to cloud processing mode."""
        response = client.put("/api/settings/processing-mode", json={"mode": "cloud"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "cloud"

    def test_switch_to_local_mode(self, client):
        """Test switching to local processing mode."""
        response = client.put("/api/settings/processing-mode", json={"mode": "local"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "local"

    def test_invalid_processing_mode(self, client):
        """Test switching to invalid processing mode."""
        response = client.put("/api/settings/processing-mode", json={"mode": "invalid"})
        assert response.status_code == 400


class TestLocalModelStatus:
    """Test local model status checking."""

    def test_get_model_status(self, client):
        """Test getting local model status."""
        response = client.get("/api/settings/local-model-status")
        assert response.status_code == 200
        data = response.json()
        assert "installed" in data
        assert "available" in data
        assert "model_name" in data
        assert isinstance(data["installed"], bool)
        assert isinstance(data["available"], bool)


class TestDemoMode:
    """Test demo mode functionality."""

    def test_no_auth_required(self, client):
        """Test that authentication is not required for settings endpoints."""
        endpoints = [
            "/api/settings/processing-modes",
            "/api/settings/processing-mode",
            "/api/settings/local-model-status",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200

    def test_demo_user_context(self, client):
        """Test that demo user is used for all requests."""
        response = client.get("/api/settings/processing-mode")
        assert response.status_code == 200

        # The response should work without any authentication headers
        # demonstrating that the demo user context is being used
