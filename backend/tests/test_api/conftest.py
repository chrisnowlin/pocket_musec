"""
Pytest configuration and fixtures for API tests.

Provides common fixtures for testing API endpoints including:
- Test database setup
- HTTP client
- Test user creation and authentication
- Test session creation
"""

import pytest
import os
import tempfile
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.api.main import app
from backend.repositories.migrations import MigrationManager
from backend.repositories.session_repository import SessionRepository


@pytest.fixture
def test_db():
    """Create a temporary test database with all necessary tables."""
    import sqlite3

    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Create a connection and initialize basic tables
    conn = sqlite3.connect(db_path)
    try:
        # Create users table (required for sessions)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'teacher',
                processing_mode TEXT DEFAULT 'cloud',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        # Create sessions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                grade_level TEXT,
                strand_code TEXT,
                selected_standards TEXT,
                selected_objectives TEXT,
                additional_standards TEXT,
                additional_objectives TEXT,
                additional_context TEXT,
                lesson_duration TEXT,
                class_size INTEGER,
                agent_state TEXT,
                conversation_history TEXT,
                current_state TEXT DEFAULT 'welcome',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Run v9 migration to add selected_model column
        conn.execute("ALTER TABLE sessions ADD COLUMN selected_model TEXT")

        conn.commit()
    except Exception as e:
        # Column might already exist, that's ok
        pass
    finally:
        conn.close()

    # Update app to use test database
    from backend.config import config

    original_db_path = config.database.path
    config.database.path = db_path

    yield db_path

    # Restore original config
    config.database.path = original_db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except Exception:
        pass


@pytest.fixture
def client(test_db):
    """Create a test client for synchronous API testing."""
    return TestClient(app)


@pytest.fixture
def test_user_data():
    """
    Provide test user credentials.

    Returns:
        dict: User credentials for testing
    """
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
    }


@pytest.fixture
def test_user(test_db, client, test_user_data):
    """
    Create and register a test user, return user data with ID.

    Returns:
        dict: User data including id, email, password
    """
    # Register test user
    response = client.post(
        "/api/auth/register",
        json={
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "full_name": test_user_data["full_name"],
            "role": "teacher",
        },
    )

    if response.status_code == 200:
        user_data = response.json()
        return {
            "id": user_data["user"]["id"],
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "full_name": test_user_data["full_name"],
        }
    else:
        # If registration fails, try to login (user might already exist)
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        if login_response.status_code == 200:
            user_data = login_response.json()
            return {
                "id": user_data["user"]["id"],
                "email": test_user_data["email"],
                "password": test_user_data["password"],
                "full_name": test_user_data["full_name"],
            }
        else:
            pytest.fail(f"Failed to create test user: {response.text}")


@pytest.fixture
def auth_token(client, test_user):
    """
    Get authentication token for test user.

    Returns:
        str: Bearer token for authorization
    """
    response = client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    return data["tokens"]["access_token"]


@pytest.fixture
def authenticated_client(client, auth_token):
    """
    Create a client with authentication headers set.

    Returns:
        TestClient: Client with authorization header
    """
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {auth_token}",
    }
    return client


@pytest.fixture
def test_session(test_db, test_user):
    """
    Create a test session for the test user.

    Returns:
        Session: A session object with basic configuration
    """
    session_repo = SessionRepository()

    session = session_repo.create_session(
        user_id=test_user["id"],
        grade_level="Grade 3",
        strand_code="Connect",
        standard_id=None,
        additional_context="Test context",
        lesson_duration="45 minutes",
        class_size=25,
    )

    return session
