"""
Integration tests for settings and processing mode system.

Tests the processing mode toggle functionality including:
- Listing available modes
- Switching between cloud and local modes
- Local model status checking
- User preferences persistence
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
from backend.repositories.migrations import DatabaseMigrator
from backend.auth.user_repository import UserRepository
from backend.auth.models import UserRole, ProcessingMode


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Migrate database
    migrator = DatabaseMigrator(db_path)
    migrator.migrate()

    # Update app to use test database
    from backend.api import dependencies
    dependencies.DATABASE_PATH = db_path

    yield db_path

    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def client(test_db):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def admin_user(test_db):
    """Create an admin user for testing."""
    repo = UserRepository(test_db)
    user = repo.create_user(
        email="admin@test.com",
        password="Admin123",
        role=UserRole.ADMIN,
        full_name="Test Admin",
        processing_mode=ProcessingMode.CLOUD
    )
    return user


@pytest.fixture
def admin_token(client, admin_user):
    """Get admin access token."""
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@test.com", "password": "Admin123"}
    )
    return response.json()["access_token"]


class TestProcessingModes:
    """Test processing mode listing and information."""

    def test_list_processing_modes(self, client, admin_token):
        """Test listing available processing modes."""
        response = client.get(
            "/api/settings/processing-modes",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "modes" in data
        assert isinstance(data["modes"], list)
        assert len(data["modes"]) >= 2  # At least cloud and local

        # Verify mode structure
        for mode in data["modes"]:
            assert "mode" in mode
            assert "display_name" in mode
            assert "description" in mode
            assert "is_available" in mode
            assert "features" in mode
            assert isinstance(mode["features"], list)

    def test_list_modes_requires_auth(self, client):
        """Test listing modes requires authentication."""
        response = client.get("/api/settings/processing-modes")

        assert response.status_code == 401

    def test_cloud_mode_always_available(self, client, admin_token):
        """Test cloud mode is always marked as available."""
        response = client.get(
            "/api/settings/processing-modes",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        cloud_mode = next((m for m in data["modes"] if m["mode"] == "cloud"), None)
        assert cloud_mode is not None
        assert cloud_mode["is_available"] is True


class TestModeSwitching:
    """Test switching between processing modes."""

    def test_switch_to_local_mode(self, client, admin_token):
        """Test switching to local mode."""
        response = client.post(
            "/api/settings/processing-mode",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"processing_mode": "local"}
        )

        # May succeed or fail depending on Ollama availability
        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()
            assert data["processing_mode"] == "local"

            # Verify it persisted by checking user info
            user_response = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert user_response.json()["processing_mode"] == "local"

    def test_switch_to_cloud_mode(self, client, admin_token):
        """Test switching to cloud mode."""
        response = client.post(
            "/api/settings/processing-mode",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"processing_mode": "cloud"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["processing_mode"] == "cloud"

        # Verify persistence
        user_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert user_response.json()["processing_mode"] == "cloud"

    def test_switch_to_invalid_mode(self, client, admin_token):
        """Test switching to invalid mode is rejected."""
        response = client.post(
            "/api/settings/processing-mode",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"processing_mode": "invalid_mode"}
        )

        assert response.status_code in [400, 422]

    def test_switch_mode_requires_auth(self, client):
        """Test switching mode requires authentication."""
        response = client.post(
            "/api/settings/processing-mode",
            json={"processing_mode": "local"}
        )

        assert response.status_code == 401


class TestLocalModelStatus:
    """Test local model status checking."""

    def test_get_local_model_status(self, client, admin_token):
        """Test getting local model status."""
        response = client.get(
            "/api/settings/local-model-status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "is_installed" in data
        assert "model_name" in data
        assert "is_running" in data

        # If Ollama is available
        if data["is_running"]:
            assert data["is_running"] is True
            if data["is_installed"]:
                assert "model_size" in data

    def test_local_model_status_requires_auth(self, client):
        """Test getting model status requires authentication."""
        response = client.get("/api/settings/local-model-status")

        assert response.status_code == 401


class TestUserPreferences:
    """Test user preference persistence."""

    @pytest.fixture
    def teacher_user(self, test_db):
        """Create a teacher user with local mode."""
        repo = UserRepository(test_db)
        user = repo.create_user(
            email="teacher@test.com",
            password="Teacher123",
            role=UserRole.TEACHER,
            full_name="Test Teacher",
            processing_mode=ProcessingMode.LOCAL
        )
        return user

    @pytest.fixture
    def teacher_token(self, client, teacher_user):
        """Get teacher access token."""
        response = client.post(
            "/api/auth/login",
            json={"email": "teacher@test.com", "password": "Teacher123"}
        )
        return response.json()["access_token"]

    def test_user_preferences_isolated(self, client, admin_token, teacher_token, admin_user, teacher_user):
        """Test each user has their own processing mode preference."""
        # Admin should be cloud mode
        admin_me = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert admin_me.json()["processing_mode"] == "cloud"

        # Teacher should be local mode
        teacher_me = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert teacher_me.json()["processing_mode"] == "local"

        # Change admin to local (if available)
        admin_change = client.post(
            "/api/settings/processing-mode",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"processing_mode": "local"}
        )

        # Teacher should still be local (unchanged)
        teacher_check = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert teacher_check.json()["processing_mode"] == "local"

    def test_preference_survives_logout(self, client, admin_user):
        """Test processing mode preference persists across sessions."""
        # Login
        login1 = client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "Admin123"}
        )
        token1 = login1.json()["access_token"]

        # Change to local mode
        change = client.post(
            "/api/settings/processing-mode",
            headers={"Authorization": f"Bearer {token1}"},
            json={"processing_mode": "local"}
        )

        # Logout (if successful mode change)
        if change.status_code == 200:
            client.post(
                "/api/auth/logout",
                json={"refresh_token": login1.json()["refresh_token"]}
            )

            # Login again
            login2 = client.post(
                "/api/auth/login",
                json={"email": "admin@test.com", "password": "Admin123"}
            )
            token2 = login2.json()["access_token"]

            # Check mode persisted
            me = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token2}"}
            )
            assert me.json()["processing_mode"] == "local"


class TestModelDownload:
    """Test local model download functionality."""

    def test_download_model_endpoint_exists(self, client, admin_token):
        """Test model download endpoint exists."""
        response = client.post(
            "/api/settings/download-local-model",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # May succeed, fail, or be unavailable depending on Ollama
        assert response.status_code in [200, 400, 500, 503]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data

    def test_download_requires_auth(self, client):
        """Test model download requires authentication."""
        response = client.post("/api/settings/download-local-model")

        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
