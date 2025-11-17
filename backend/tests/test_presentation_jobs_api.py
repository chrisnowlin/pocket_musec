"""Tests for the presentation jobs API endpoints."""

import pytest
import tempfile
import os
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.api.routes.presentations import router
from backend.services.presentation_jobs_persistent import PresentationJobManager
from backend.models.presentation_jobs import JobStatus, JobPriority
from backend.repositories.database import DatabaseManager
from backend.auth import User, ProcessingMode, Lesson as LessonModel


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    db_manager = DatabaseManager(db_path)
    db_manager.initialize_database()

    yield db_path

    os.unlink(db_path)


@pytest.fixture
def client(temp_db, mock_user):
    """Create a test client with temporary database."""
    from fastapi import FastAPI
    from backend.api.dependencies import get_current_user
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # Mock the database to use our temp database
    with patch('backend.config.config.database.path', temp_db):
        yield TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return User(
        id="test_user_id",
        email="test@example.com",
        password_hash="hashed",
        full_name="Test User",
        processing_mode=ProcessingMode.CLOUD,
    )


@pytest.fixture
def job_manager(temp_db):
    """Create a job manager for testing."""
    db_manager = DatabaseManager(temp_db)
    from backend.repositories.presentation_job_repository import PresentationJobRepository
    repo = PresentationJobRepository(db_manager)
    return PresentationJobManager(job_repository=repo)


class TestPresentationJobsAPI:
    """Test the presentation jobs API endpoints."""

    def test_create_job(self, client, mock_user):
        """Test creating a new presentation generation job."""

        # Mock lesson access check
        with patch('backend.api.routes.presentations.LessonRepository') as mock_lesson_repo, \
             patch('backend.api.routes.presentations.create_presentation_job', return_value="job-123"), \
             patch('backend.api.routes.presentations.get_job_manager') as mock_get_manager:
            mock_lesson_repo.return_value.get_lesson.return_value = LessonModel(
                id="test_lesson_id",
                session_id="session",
                user_id=mock_user.id,
                title="Sample",
                content="Lesson content"
            )
            mock_get_manager.return_value.execute_job = MagicMock()

            request_data = {
                "lesson_id": "test_lesson_id",
                "style": "default",
                "use_llm_polish": True,
                "timeout_seconds": 30,
                "priority": "high",
                "max_retries": 2
            }

            response = client.post("/api/presentations/generate", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "job-123"
            assert data["status"] == "pending"
            assert "message" in data

    def test_create_job_with_invalid_priority(self, client, mock_user):
        """Test creating a job with invalid priority."""

        request_data = {
            "lesson_id": "test_lesson_id",
            "priority": "invalid_priority"
        }

        response = client.post("/api/presentations/generate", json=request_data)
        assert response.status_code == 400

    def test_get_job_status(self, client, mock_user, job_manager):
        """Test getting job status."""
        
        # Create a job first
        job_id = job_manager.create_job("test_lesson", mock_user.id)

        # Mock the job manager in the API
        with patch('backend.api.routes.presentations.get_job_manager', return_value=job_manager):
            response = client.get(f"/api/presentations/jobs/{job_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == job_id
            assert data["status"] == JobStatus.PENDING.value
            assert data["lesson_id"] == "test_lesson"
            assert data["progress"] == 0
            assert "priority" in data
            assert "retry_count" in data

    def test_get_nonexistent_job_status(self, client, mock_user, job_manager):
        """Test getting status of non-existent job."""
        
        with patch('backend.api.routes.presentations.get_job_manager', return_value=job_manager):
            response = client.get("/api/presentations/jobs/nonexistent_job_id")

            assert response.status_code == 404

    def test_list_user_jobs(self, client, mock_user, job_manager):
        """Test listing jobs for current user."""
        
        # Create some jobs
        job_manager.create_job("lesson1", mock_user.id)
        job_manager.create_job("lesson2", mock_user.id)
        job_manager.create_job("lesson3", "other_user")

        with patch('backend.api.routes.presentations.get_job_manager', return_value=job_manager):
            response = client.get("/api/presentations/jobs")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2  # Only user's jobs
            assert all(job["lesson_id"] in ["lesson1", "lesson2"] for job in data)

    def test_list_jobs_with_filters(self, client, mock_user, job_manager):
        """Test listing jobs with status and priority filters."""
        
        # Create jobs with different statuses and priorities
        job_id1 = job_manager.create_job("lesson1", mock_user.id, priority=JobPriority.HIGH)
        job_id2 = job_manager.create_job("lesson2", mock_user.id, priority=JobPriority.NORMAL)

        # Complete one job
        job_manager.job_repository.complete_job(job_id1, "pres1", 5)

        with patch('backend.api.routes.presentations.get_job_manager', return_value=job_manager):
            # Filter by status
            response = client.get("/api/presentations/jobs?status=completed")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["status"] == JobStatus.COMPLETED.value

            # Filter by priority
            response = client.get("/api/presentations/jobs?priority=high")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["priority"] == JobPriority.HIGH.value

    def test_cancel_job(self, client, mock_user, job_manager):
        """Test cancelling a job."""
        
        # Create a job
        job_id = job_manager.create_job("test_lesson", mock_user.id)

        with patch('backend.api.routes.presentations.get_job_manager', return_value=job_manager):
            response = client.delete(f"/api/presentations/jobs/{job_id}?reason=Test cancellation")

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == job_id
            assert data["reason"] == "Test cancellation"

            # Verify job is cancelled
            job = job_manager.get_job(job_id)
            assert job.status == JobStatus.CANCELLED

    def test_retry_job(self, client, mock_user, job_manager):
        """Test retrying a failed job."""
        
        # Create and fail a job
        job_id = job_manager.create_job("test_lesson", mock_user.id, max_retries=2)
        job_manager.job_repository.fail_job(job_id, "ERROR", "Test error")

        with patch('backend.api.routes.presentations.get_job_manager', return_value=job_manager):
            request_data = {"force_retry": False}
            response = client.post(f"/api/presentations/jobs/{job_id}/retry", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == job_id

            # Verify job is pending for retry
            job = job_manager.get_job(job_id)
            assert job.status == JobStatus.PENDING
            assert job.retry_count == 1

    def test_bulk_cancel_jobs(self, client, mock_user, job_manager):
        """Test bulk cancelling jobs."""
        
        # Create multiple jobs
        job_id1 = job_manager.create_job("lesson1", mock_user.id)
        job_id2 = job_manager.create_job("lesson2", mock_user.id)
        job_id3 = job_manager.create_job("lesson3", "other_user")  # Different user

        with patch('backend.api.routes.presentations.get_job_manager', return_value=job_manager):
            request_data = {"job_ids": [job_id1, job_id2, job_id3]}
            response = client.post("/api/presentations/jobs/bulk-cancel?reason=Bulk test", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["total_requested"] == 3
            assert data["total_cancelled"] == 2  # Only user's jobs
            assert len(data["cancelled_jobs"]) == 2
            assert len(data["failed_jobs"]) == 1
            assert data["failed_jobs"][0]["error"] == "Access denied"

    def test_cleanup_old_jobs(self, client, mock_user, job_manager):
        """Test cleaning up old jobs."""
        
        with patch('backend.api.routes.presentations.get_job_manager', return_value=job_manager):
            response = client.delete("/api/presentations/jobs/cleanup?max_age_hours=24")

            assert response.status_code == 200
            data = response.json()
            assert "deleted_jobs" in data
            assert "max_age_hours" in data
            assert data["max_age_hours"] == 24

    def test_get_job_health_metrics(self, client, mock_user, job_manager):
        """Test getting job health metrics."""
        
        # Create some test jobs
        job_manager.create_job("lesson1", mock_user.id)
        job_manager.create_job("lesson2", mock_user.id)

        with patch('backend.api.routes.presentations.get_job_manager', return_value=job_manager):
            response = client.get("/api/presentations/jobs/health?hours=24")

            assert response.status_code == 200
            data = response.json()
            assert "total" in data
            assert "pending" in data
            assert "total_user_jobs" in data
            assert "user_success_rate" in data
            assert "worker_id" in data

    def test_get_job_statistics(self, client, mock_user, job_manager):
        """Test getting detailed job statistics."""
        
        # Create jobs with different outcomes
        job_id1 = job_manager.create_job("lesson1", mock_user.id)
        job_id2 = job_manager.create_job("lesson2", mock_user.id)

        job_manager.job_repository.complete_job(job_id1, "pres1", 5)
        job_manager.job_repository.fail_job(job_id2, "ERROR", "Failed")

        with patch('backend.api.routes.presentations.get_job_manager', return_value=job_manager):
            response = client.get("/api/presentations/jobs/statistics?hours=24")

            assert response.status_code == 200
            data = response.json()
            assert "total" in data
            assert "completed" in data
            assert "failed" in data
            assert "failure_rate" in data
            assert "priority_distribution" in data

    def test_trigger_job_recovery(self, client, mock_user, job_manager):
        """Test triggering job recovery."""
        
        with patch('backend.api.routes.presentations.get_job_manager', return_value=job_manager):
            response = client.post("/api/presentations/jobs/system/recovery?timeout_minutes=30")

            assert response.status_code == 200
            data = response.json()
            assert "recovered_jobs" in data
            assert "timeout_minutes" in data
            assert "timestamp" in data
            assert data["timeout_minutes"] == 30

    def test_unauthorized_job_access(self, client, mock_user, job_manager):
        """Test that users cannot access jobs belonging to other users."""
        
        # Create a job for another user
        other_user_id = "other_user_id"
        job_id = job_manager.create_job("test_lesson", other_user_id)

        with patch('backend.api.routes.presentations.get_job_manager', return_value=job_manager):
            # Try to get job status for other user's job
            response = client.get(f"/api/presentations/jobs/{job_id}")
            assert response.status_code == 403

            # Try to cancel other user's job
            response = client.delete(f"/api/presentations/jobs/{job_id}")
            assert response.status_code == 403

            # Try to retry other user's job
            response = client.post(f"/api/presentations/jobs/{job_id}/retry", json={"force_retry": False})
            assert response.status_code == 403


class TestAPIErrorHandling:
    """Test API error handling scenarios."""

    def test_invalid_job_id_format(self, client, mock_user):
        """Test handling of invalid job ID format."""
        
        # Test with empty job ID
        response = client.get("/api/presentations/jobs/")
        assert response.status_code == 404  # Route not found

        # Test with None (should be handled by path parameter validation)
        # This would typically be caught by FastAPI's path parameter validation

    def test_invalid_status_filter(self, client, mock_user):
        """Test handling of invalid status filter."""
        
        response = client.get("/api/presentations/jobs?status=invalid_status")
        assert response.status_code == 400
        data = response.json()
        assert "Invalid status" in data["detail"]

    def test_invalid_time_parameters(self, client, mock_user):
        """Test handling of invalid time parameters."""
        
        # Test negative hours
        response = client.get("/api/presentations/jobs/health?hours=-1")
        assert response.status_code == 422

        # Test hours too large
        response = client.get("/api/presentations/jobs/health?hours=200")
        assert response.status_code == 422

    def test_database_error_handling(self, client, mock_user):
        """Test handling of database errors."""
        
        # Mock a database error
        with patch('backend.api.routes.presentations.get_job_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_job_health_metrics.side_effect = Exception("Database connection failed")
            mock_get_manager.return_value = mock_manager

            response = client.get("/api/presentations/jobs/health")
            assert response.status_code == 500
            data = response.json()
            assert "Failed to retrieve job health metrics" in data["detail"]


if __name__ == "__main__":
    pytest.main([__file__])
