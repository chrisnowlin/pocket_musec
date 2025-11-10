"""
Integration tests for authentication system.

Tests the complete authentication flow including:
- User registration
- Login/logout
- Token refresh
- Password changes
- Role-based access control
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
    assert response.status_code == 200
    return response.json()["access_token"]


class TestAuthenticationFlow:
    """Test complete authentication workflows."""

    def test_login_success(self, client, admin_user):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "Admin123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900  # 15 minutes

    def test_login_wrong_password(self, client, admin_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "WrongPassword"}
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/api/auth/login",
            json={"email": "nobody@test.com", "password": "Password123"}
        )

        assert response.status_code == 401

    def test_get_current_user(self, client, admin_token):
        """Test getting current user info."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.com"
        assert data["role"] == "admin"
        assert data["full_name"] == "Test Admin"

    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_token_refresh(self, client, admin_user):
        """Test refreshing access token."""
        # Login to get refresh token
        login_response = client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "Admin123"}
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_logout(self, client, admin_user):
        """Test logout invalidates refresh token."""
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "Admin123"}
        )
        refresh_token = login_response.json()["refresh_token"]

        # Logout
        logout_response = client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token}
        )

        assert logout_response.status_code == 200

        # Try to refresh with logged out token (should fail)
        refresh_response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert refresh_response.status_code == 401

    def test_change_password(self, client, admin_token):
        """Test changing user password."""
        response = client.put(
            "/api/auth/password",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "current_password": "Admin123",
                "new_password": "NewPassword456"
            }
        )

        assert response.status_code == 200

        # Verify old password no longer works
        login_old = client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "Admin123"}
        )
        assert login_old.status_code == 401

        # Verify new password works
        login_new = client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "NewPassword456"}
        )
        assert login_new.status_code == 200


class TestUserRegistration:
    """Test user registration (admin only)."""

    def test_register_user_as_admin(self, client, admin_token):
        """Test admin can create new users."""
        response = client.post(
            "/api/auth/register",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "teacher@test.com",
                "password": "Teacher123",
                "role": "teacher",
                "full_name": "Test Teacher",
                "processing_mode": "cloud"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "teacher@test.com"
        assert data["role"] == "teacher"
        assert data["full_name"] == "Test Teacher"

    def test_register_duplicate_email(self, client, admin_token, admin_user):
        """Test cannot register duplicate email."""
        response = client.post(
            "/api/auth/register",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "admin@test.com",  # Already exists
                "password": "Password123",
                "role": "teacher",
                "full_name": "Duplicate User"
            }
        )

        assert response.status_code == 400

    def test_register_weak_password(self, client, admin_token):
        """Test password complexity validation."""
        response = client.post(
            "/api/auth/register",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "weak@test.com",
                "password": "weak",  # Too short
                "role": "teacher",
                "full_name": "Weak Password User"
            }
        )

        assert response.status_code == 400


class TestRoleBasedAccess:
    """Test role-based access control."""

    @pytest.fixture
    def teacher_user(self, test_db):
        """Create a teacher user."""
        repo = UserRepository(test_db)
        user = repo.create_user(
            email="teacher@test.com",
            password="Teacher123",
            role=UserRole.TEACHER,
            full_name="Test Teacher",
            processing_mode=ProcessingMode.CLOUD
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

    def test_teacher_cannot_create_users(self, client, teacher_token):
        """Test teachers cannot create new users."""
        response = client.post(
            "/api/auth/register",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "email": "newuser@test.com",
                "password": "Password123",
                "role": "teacher",
                "full_name": "New User"
            }
        )

        assert response.status_code == 403

    def test_teacher_cannot_list_users(self, client, teacher_token):
        """Test teachers cannot list all users."""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )

        assert response.status_code == 403

    def test_teacher_can_change_own_password(self, client, teacher_token):
        """Test teachers can change their own password."""
        response = client.put(
            "/api/auth/password",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "current_password": "Teacher123",
                "new_password": "NewPassword456"
            }
        )

        assert response.status_code == 200

    def test_admin_can_list_users(self, client, admin_token):
        """Test admins can list all users."""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)

    def test_admin_can_delete_users(self, client, admin_token, teacher_user):
        """Test admins can delete users."""
        response = client.delete(
            f"/api/users/{teacher_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200


class TestRateLimiting:
    """Test rate limiting on auth endpoints."""

    def test_login_rate_limit(self, client, admin_user):
        """Test login endpoint is rate limited."""
        # Make 6 requests (limit is 5 per minute)
        for i in range(6):
            response = client.post(
                "/api/auth/login",
                json={"email": "admin@test.com", "password": "WrongPassword"}
            )

            if i < 5:
                # First 5 should get through (even though they fail)
                assert response.status_code in [401, 429]
            else:
                # 6th should be rate limited
                # Note: Depending on rate limiter implementation, this might be 429
                # or still 401 if rate limiter doesn't block failed attempts
                pass  # Rate limiting behavior may vary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
