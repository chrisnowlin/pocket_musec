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
        assert "modes" in data
        assert "current" in data
        assert isinstance(data["modes"], list)
        mode_ids = [mode["id"] for mode in data["modes"]]
        assert "cloud" in mode_ids
        assert "local" in mode_ids
        assert data["current"] in ["cloud", "local"]

    def test_get_current_processing_mode(self, client):
        """Test getting current processing mode via processing-modes endpoint."""
        response = client.get("/api/settings/processing-modes")
        assert response.status_code == 200
        data = response.json()
        assert data["current"] in ["cloud", "local"]

    def test_switch_to_cloud_mode(self, client):
        """Test switching to cloud processing mode."""
        response = client.put("/api/settings/processing-mode", json={"mode": "cloud"})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "cloud" in data["message"].lower()

    def test_switch_to_local_mode(self, client):
        """Test switching to local processing mode."""
        response = client.put("/api/settings/processing-mode", json={"mode": "local"})
        assert response.status_code == 400

    def test_invalid_processing_mode(self, client):
        """Test switching to invalid processing mode."""
        response = client.put("/api/settings/processing-mode", json={"mode": "invalid"})
        assert response.status_code == 400


class TestLocalModelStatus:
    """Test local model status checking."""

    def test_get_model_status(self, client):
        """Test getting local model status."""
        response = client.get("/api/settings/models/local/status")
        assert response.status_code == 200
        data = response.json()
        assert "installed" in data
        assert "available" in data
        assert "model" in data
        assert "health" in data
        assert isinstance(data["installed"], bool)
        assert isinstance(data["available"], bool)


class TestDemoMode:
    """Test demo mode functionality."""

    def test_no_auth_required(self, client):
        """Test that authentication is not required for settings endpoints."""
        endpoints = [
            "/api/settings/processing-modes",
            "/api/settings/models/local/status",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200

    def test_demo_user_context(self, client):
        """Test that demo user is used for all requests."""
        response = client.get("/api/settings/processing-modes")
        assert response.status_code == 200
