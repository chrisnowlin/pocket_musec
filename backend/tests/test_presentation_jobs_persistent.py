"""Tests for the persistent presentation jobs system."""

import pytest
import tempfile
import sqlite3
import os
from datetime import datetime, timedelta
from typing import List

from backend.repositories.presentation_job_repository import PresentationJobRepository
from backend.models.presentation_jobs import PresentationJob, JobStatus, JobPriority
from backend.services.presentation_jobs_persistent import PresentationJobManager
from backend.repositories.database import DatabaseManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    # Initialize database
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_database()

    yield db_path

    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def job_repository(temp_db):
    """Create a job repository with temporary database."""
    return PresentationJobRepository(DatabaseManager(temp_db))


@pytest.fixture
def job_manager(temp_db):
    """Create a job manager with temporary database."""
    return PresentationJobManager(
        job_repository=PresentationJobRepository(DatabaseManager(temp_db))
    )


class TestPresentationJobRepository:
    """Test the presentation job repository."""

    def test_create_job(self, job_repository):
        """Test creating a new job."""
        job = job_repository.create_job(
            lesson_id="test_lesson",
            user_id="test_user",
            style="test_style",
            use_llm_polish=False,
            timeout_seconds=60,
            priority=JobPriority.HIGH,
            max_retries=3,
        )

        assert job.id is not None
        assert job.lesson_id == "test_lesson"
        assert job.user_id == "test_user"
        assert job.style == "test_style"
        assert job.use_llm_polish is False
        assert job.timeout_seconds == 60
        assert job.priority == JobPriority.HIGH
        assert job.max_retries == 3
        assert job.status == JobStatus.PENDING
        assert job.progress == 0
        assert job.retry_count == 0

    def test_get_job(self, job_repository):
        """Test retrieving a job by ID."""
        created_job = job_repository.create_job(
            lesson_id="test_lesson",
            user_id="test_user"
        )

        retrieved_job = job_repository.get_job(created_job.id)
        assert retrieved_job is not None
        assert retrieved_job.id == created_job.id
        assert retrieved_job.lesson_id == created_job.lesson_id
        assert retrieved_job.user_id == created_job.user_id

    def test_get_nonexistent_job(self, job_repository):
        """Test retrieving a non-existent job."""
        job = job_repository.get_job("nonexistent_id")
        assert job is None

    def test_update_job(self, job_repository):
        """Test updating an existing job."""
        job = job_repository.create_job(
            lesson_id="test_lesson",
            user_id="test_user"
        )

        # Update job status
        job.start()
        job.update_progress(50, "Processing slide 2")
        success = job_repository.update_job(job)

        assert success is True

        # Verify update
        updated_job = job_repository.get_job(job.id)
        assert updated_job.status == JobStatus.RUNNING
        assert updated_job.progress == 50
        assert updated_job.message == "Processing slide 2"
        assert updated_job.started_at is not None

    def test_complete_job(self, job_repository):
        """Test marking a job as completed."""
        job = job_repository.create_job(
            lesson_id="test_lesson",
            user_id="test_user"
        )
        job.start()

        success = job_repository.complete_job(
            job_id=job.id,
            presentation_id="test_presentation",
            slide_count=10,
            result_data={"test": "data"}
        )

        assert success is True

        completed_job = job_repository.get_job(job.id)
        assert completed_job.status == JobStatus.COMPLETED
        assert completed_job.presentation_id == "test_presentation"
        assert completed_job.slide_count == 10
        assert completed_job.progress == 100
        assert completed_job.processing_time_seconds is not None

    def test_fail_job(self, job_repository):
        """Test marking a job as failed."""
        job = job_repository.create_job(
            lesson_id="test_lesson",
            user_id="test_user"
        )

        success = job_repository.fail_job(
            job_id=job.id,
            error_code="TEST_ERROR",
            error_message="Test error message",
            error_details={"test": "detail"}
        )

        assert success is True

        failed_job = job_repository.get_job(job.id)
        assert failed_job.status == JobStatus.FAILED
        assert failed_job.error_code == "TEST_ERROR"
        assert failed_job.error_message == "Test error message"
        assert failed_job.error_details["test"] == "detail"

    def test_cancel_job(self, job_repository):
        """Test cancelling a job."""
        job = job_repository.create_job(
            lesson_id="test_lesson",
            user_id="test_user"
        )

        success = job_repository.cancel_job(job.id, "Test cancellation")
        assert success is True

        cancelled_job = job_repository.get_job(job.id)
        assert cancelled_job.status == JobStatus.CANCELLED
        assert cancelled_job.error_code == "CANCELLED"

    def test_retry_job(self, job_repository):
        """Test retrying a failed job."""
        job = job_repository.create_job(
            lesson_id="test_lesson",
            user_id="test_user",
            max_retries=2
        )

        # Fail the job first
        job_repository.fail_job(job.id, "TEST_ERROR", "Test error")

        # Retry the job
        success = job_repository.retry_job(job.id)
        assert success is True

        retried_job = job_repository.get_job(job.id)
        assert retried_job.status == JobStatus.PENDING
        assert retried_job.retry_count == 1

        # Exhaust retries
        job_repository.fail_job(job.id, "TEST_ERROR", "Test error")
        job_repository.retry_job(job.id)
        job_repository.fail_job(job.id, "TEST_ERROR", "Test error")

        # Should not be able to retry anymore
        success = job_repository.retry_job(job.id)
        assert success is False

    def test_get_user_jobs(self, job_repository):
        """Test retrieving jobs for a specific user."""
        # Create jobs for different users
        job1 = job_repository.create_job("lesson1", "user1")
        job2 = job_repository.create_job("lesson2", "user1")
        job3 = job_repository.create_job("lesson3", "user2")

        user1_jobs = job_repository.get_user_jobs("user1")
        user2_jobs = job_repository.get_user_jobs("user2")

        assert len(user1_jobs) == 2
        assert len(user2_jobs) == 1

        job_ids = [job.id for job in user1_jobs]
        assert job1.id in job_ids
        assert job2.id in job_ids
        assert job3.id not in job_ids

    def test_get_pending_jobs(self, job_repository):
        """Test retrieving pending jobs."""
        # Create jobs with different statuses
        job1 = job_repository.create_job("lesson1", "user1", priority=JobPriority.HIGH)
        job2 = job_repository.create_job("lesson2", "user1", priority=JobPriority.NORMAL)
        job3 = job_repository.create_job("lesson3", "user1", priority=JobPriority.HIGH)

        # Start one job
        job2.start()
        job_repository.update_job(job2)

        # Get pending jobs
        pending_jobs = job_repository.get_pending_jobs()
        assert len(pending_jobs) == 2

        # Should be ordered by priority then creation time
        assert pending_jobs[0].priority == JobPriority.HIGH
        assert pending_jobs[1].priority == JobPriority.HIGH

        # Filter by priority
        high_priority_jobs = job_repository.get_pending_jobs(priority=JobPriority.HIGH)
        assert len(high_priority_jobs) == 2

    def test_cleanup_old_jobs(self, job_repository):
        """Test cleaning up old finished jobs."""
        # Create some jobs
        job1 = job_repository.create_job("lesson1", "user1")
        job2 = job_repository.create_job("lesson2", "user1")

        # Complete one job, leave one pending
        job_repository.complete_job(job1.id, "pres1", 5)
        # Manually set completed_at to be old
        old_time = (datetime.utcnow() - timedelta(hours=25)).isoformat()
        conn = job_repository.db_manager.get_connection()
        conn.execute(
            "UPDATE presentation_jobs SET completed_at = ? WHERE id = ?",
            (old_time, job1.id)
        )
        conn.commit()
        conn.close()

        # Clean up old jobs
        deleted_count = job_repository.cleanup_old_jobs(max_age_hours=24)
        assert deleted_count == 1

        # Verify only the pending job remains
        remaining_jobs = job_repository.get_pending_jobs()
        assert len(remaining_jobs) == 1
        assert remaining_jobs[0].id == job2.id

    def test_get_job_statistics(self, job_repository):
        """Test getting job statistics."""
        # Create some jobs with different statuses
        job1 = job_repository.create_job("lesson1", "user1")
        job2 = job_repository.create_job("lesson2", "user1")
        job3 = job_repository.create_job("lesson3", "user1")

        # Complete some jobs
        job_repository.complete_job(job1.id, "pres1", 5)
        job_repository.fail_job(job2.id, "ERROR", "Failed")

        stats = job_repository.get_job_statistics(hours=24)

        assert stats["total"] == 3
        assert stats["pending"] == 1
        assert stats["completed"] == 1
        assert stats["failed"] == 1
        assert "failure_rate" in stats

    def test_recover_orphaned_jobs(self, job_repository):
        """Test recovering orphaned running jobs."""
        # Create a job and mark it as running with old timestamp
        job = job_repository.create_job("lesson1", "user1")
        job.start()
        job_repository.update_job(job)

        # Manually set started_at to be very old
        old_time = (datetime.utcnow() - timedelta(minutes=35)).isoformat()
        conn = job_repository.db_manager.get_connection()
        conn.execute(
            "UPDATE presentation_jobs SET started_at = ? WHERE id = ?",
            (old_time, job.id)
        )
        conn.commit()
        conn.close()

        # Recover orphaned jobs
        recovered_count = job_repository.recover_orphaned_jobs(timeout_minutes=30)
        assert recovered_count == 1

        # Verify job is now failed
        recovered_job = job_repository.get_job(job.id)
        assert recovered_job.status == JobStatus.FAILED
        assert recovered_job.error_code == "ORPHANED"


class TestPresentationJobManager:
    """Test the presentation job manager."""

    def test_create_job(self, job_manager):
        """Test creating a job through the manager."""
        job_id = job_manager.create_job(
            lesson_id="test_lesson",
            user_id="test_user",
            priority=JobPriority.HIGH,
            max_retries=3
        )

        assert job_id is not None

        job = job_manager.get_job(job_id)
        assert job is not None
        assert job.id == job_id
        assert job.lesson_id == "test_lesson"
        assert job.user_id == "test_user"
        assert job.priority == JobPriority.HIGH
        assert job.max_retries == 3

    def test_get_job_status(self, job_manager):
        """Test getting job status as dictionary."""
        job_id = job_manager.create_job("test_lesson", "test_user")

        status = job_manager.get_job_status(job_id)
        assert status is not None
        assert status["job_id"] == job_id
        assert status["status"] == JobStatus.PENDING.value
        assert status["lesson_id"] == "test_lesson"

    def test_cancel_job(self, job_manager):
        """Test cancelling a job."""
        job_id = job_manager.create_job("test_lesson", "test_user")

        success = job_manager.cancel_job(job_id, "Test cancellation")
        assert success is True

        job = job_manager.get_job(job_id)
        assert job.status == JobStatus.CANCELLED

    def test_get_user_jobs(self, job_manager):
        """Test getting user jobs with filters."""
        # Create jobs for user
        job_id1 = job_manager.create_job("lesson1", "test_user")
        job_id2 = job_manager.create_job("lesson2", "test_user")
        job_id3 = job_manager.create_job("lesson3", "other_user")

        # Get all user jobs
        user_jobs = job_manager.get_user_jobs("test_user")
        assert len(user_jobs) == 2

        # Get only pending jobs
        pending_jobs = job_manager.get_user_jobs("test_user", status=JobStatus.PENDING)
        assert len(pending_jobs) == 2

        # Exclude finished jobs (won't matter here since none are finished)
        active_jobs = job_manager.get_user_jobs("test_user", include_finished=False)
        assert len(active_jobs) == 2

    def test_get_pending_jobs(self, job_manager):
        """Test getting pending jobs."""
        # Create jobs with different priorities
        job_id1 = job_manager.create_job("lesson1", "user1", priority=JobPriority.HIGH)
        job_id2 = job_manager.create_job("lesson2", "user1", priority=JobPriority.NORMAL)
        job_id3 = job_manager.create_job("lesson3", "user1", priority=JobPriority.URGENT)

        pending_jobs = job_manager.get_pending_jobs()
        assert len(pending_jobs) == 3

        # Should be ordered by priority
        assert pending_jobs[0].priority == JobPriority.URGENT
        assert pending_jobs[1].priority == JobPriority.HIGH
        assert pending_jobs[2].priority == JobPriority.NORMAL

    def test_get_job_health_metrics(self, job_manager):
        """Test getting job health metrics."""
        # Create some jobs
        job_manager.create_job("lesson1", "user1")
        job_manager.create_job("lesson2", "user2")

        metrics = job_manager.get_job_health_metrics()

        assert "total" in metrics
        assert "pending" in metrics
        assert "worker_id" in metrics
        assert "shutdown_requested" in metrics
        assert metrics["worker_id"] == job_manager.worker_id

    def test_delete_job(self, job_manager):
        """Test deleting a job."""
        job_id = job_manager.create_job("test_lesson", "test_user")

        # Verify job exists
        job = job_manager.get_job(job_id)
        assert job is not None

        # Delete job
        success = job_manager.delete_job(job_id)
        assert success is True

        # Verify job is gone
        job = job_manager.get_job(job_id)
        assert job is None

    def test_initialization_on_startup(self, job_manager):
        """Test that initialization recovers orphaned jobs on startup."""
        # Simulate an orphaned job by creating a running job with old timestamp
        job_id = job_manager.create_job("test_lesson", "test_user")
        job = job_manager.get_job(job_id)
        job.start()
        job_manager.job_repository.update_job(job)

        # Manually set it to be old
        old_time = datetime.utcnow() - timedelta(minutes=35)
        conn = job_manager.job_repository.db_manager.get_connection()
        conn.execute(
            "UPDATE presentation_jobs SET started_at = ? WHERE id = ?",
            (old_time.isoformat(), job_id)
        )
        conn.commit()
        conn.close()

        # Create a new job manager (simulating startup)
        new_job_manager = PresentationJobManager(
            job_repository=job_manager.job_repository
        )

        # The orphaned job should have been recovered
        recovered_job = new_job_manager.get_job(job_id)
        assert recovered_job.status == JobStatus.FAILED
        assert recovered_job.error_code == "ORPHANED"


class TestJobPersistenceAcrossRestarts:
    """Test job persistence across job manager restarts."""

    def test_job_persistence(self, temp_db):
        """Test that jobs persist across job manager instances."""
        db_manager = DatabaseManager(temp_db)
        repo = PresentationJobRepository(db_manager)

        # Create job with first manager
        manager1 = PresentationJobManager(job_repository=repo)
        job_id = manager1.create_job("test_lesson", "test_user")

        # Verify job exists in first manager
        job1 = manager1.get_job(job_id)
        assert job1 is not None
        assert job1.status == JobStatus.PENDING

        # Create second manager (simulating restart)
        manager2 = PresentationJobManager(job_repository=repo)

        # Verify job is still accessible
        job2 = manager2.get_job(job_id)
        assert job2 is not None
        assert job2.id == job1.id
        assert job2.lesson_id == job1.lesson_id
        assert job2.user_id == job1.user_id
        assert job2.status == JobStatus.PENDING

        # Verify worker IDs are different (different instances)
        assert manager1.worker_id != manager2.worker_id


if __name__ == "__main__":
    pytest.main([__file__])