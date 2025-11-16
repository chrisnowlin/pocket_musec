"""Background job management for presentation generation.

This module provides async job execution for presentation generation
using FastAPI BackgroundTasks and simple in-memory job tracking.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from .presentation_service import PresentationService

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Status of background jobs."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PresentationJob:
    """Background job for presentation generation."""

    id: str
    lesson_id: str
    user_id: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    presentation_id: Optional[str] = None


class PresentationJobManager:
    """Manages background presentation generation jobs."""

    def __init__(self, presentation_service: Optional[PresentationService] = None):
        self.presentation_service = presentation_service or PresentationService()
        self.jobs: Dict[str, PresentationJob] = {}
        self.job_timeout_minutes = 10

    def create_job(
        self,
        lesson_id: str,
        user_id: str,
        style: str = "default",
        use_llm_polish: bool = True,
        timeout_seconds: int = 30,
    ) -> str:
        """Create a new presentation generation job.

        Args:
            lesson_id: ID of the lesson to generate presentation for
            user_id: ID of the user requesting the presentation
            style: Presentation style
            use_llm_polish: Whether to use LLM polishing
            timeout_seconds: Timeout for LLM operations

        Returns:
            Job ID for tracking
        """
        job_id = str(uuid.uuid4())

        job = PresentationJob(
            id=job_id,
            lesson_id=lesson_id,
            user_id=user_id,
        )

        self.jobs[job_id] = job
        logger.info(f"Created presentation job {job_id} for lesson {lesson_id}")

        return job_id

    def get_job(self, job_id: str) -> Optional[PresentationJob]:
        """Get a job by ID."""
        return self.jobs.get(job_id)

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status as a dictionary."""
        job = self.get_job(job_id)
        if not job:
            return None

        return {
            "job_id": job.id,
            "status": job.status.value,
            "lesson_id": job.lesson_id,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "presentation_id": job.presentation_id,
            "error": job.error,
        }

    def execute_job(
        self,
        job_id: str,
        style: str = "default",
        use_llm_polish: bool = True,
        timeout_seconds: int = 30,
    ) -> None:
        """Execute a presentation generation job.

        This method is designed to be called by FastAPI BackgroundTasks.
        """
        job = self.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        if job.status != JobStatus.PENDING:
            logger.warning(f"Job {job_id} is not pending (status: {job.status})")
            return

        logger.info(f"Starting execution of presentation job {job_id}")

        # Update job status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()

        try:
            # Execute presentation generation
            presentation = self.presentation_service.generate_presentation(
                lesson_id=job.lesson_id,
                user_id=job.user_id,
                style=style,
                use_llm_polish=use_llm_polish,
                timeout_seconds=timeout_seconds,
            )

            # Update job with success result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.presentation_id = presentation.id
            job.result = {
                "presentation_id": presentation.id,
                "slide_count": len(presentation.slides),
                "status": presentation.status.value,
            }

            logger.info(f"Successfully completed presentation job {job_id}")

        except Exception as e:
            # Update job with error
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error = str(e)

            logger.error(f"Presentation job {job_id} failed: {e}")

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up old completed/failed jobs.

        Args:
            max_age_hours: Maximum age of jobs to keep

        Returns:
            Number of jobs cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        jobs_to_remove = []
        for job_id, job in self.jobs.items():
            if (
                job.status in [JobStatus.COMPLETED, JobStatus.FAILED]
                and job.completed_at
                and job.completed_at < cutoff_time
            ):
                jobs_to_remove.append(job_id)

        for job_id in jobs_to_remove:
            del self.jobs[job_id]

        logger.info(f"Cleaned up {len(jobs_to_remove)} old presentation jobs")
        return len(jobs_to_remove)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job.

        Args:
            job_id: ID of the job to cancel

        Returns:
            True if job was cancelled, False if not found or not cancellable
        """
        job = self.get_job(job_id)
        if not job:
            return False

        if job.status == JobStatus.PENDING:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error = "Job cancelled by user"
            logger.info(f"Cancelled presentation job {job_id}")
            return True

        return False

    def get_user_jobs(self, user_id: str, limit: int = 50) -> List[PresentationJob]:
        """Get all jobs for a specific user.

        Args:
            user_id: ID of the user
            limit: Maximum number of jobs to return

        Returns:
            List of jobs for the user, ordered by creation time (newest first)
        """
        user_jobs = [job for job in self.jobs.values() if job.user_id == user_id]

        # Sort by creation time (newest first)
        user_jobs.sort(key=lambda j: j.created_at, reverse=True)

        return user_jobs[:limit]


# Global job manager instance
_job_manager: Optional[PresentationJobManager] = None


def get_job_manager() -> PresentationJobManager:
    """Get the global job manager instance."""
    global _job_manager
    if _job_manager is None:
        _job_manager = PresentationJobManager()
    return _job_manager


def create_presentation_job(
    lesson_id: str,
    user_id: str,
    style: str = "default",
    use_llm_polish: bool = True,
    timeout_seconds: int = 30,
) -> str:
    """Create a new presentation generation job.

    Convenience function that uses the global job manager.
    """
    job_manager = get_job_manager()
    return job_manager.create_job(
        lesson_id=lesson_id,
        user_id=user_id,
        style=style,
        use_llm_polish=use_llm_polish,
        timeout_seconds=timeout_seconds,
    )


def get_presentation_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get the status of a presentation job.

    Convenience function that uses the global job manager.
    """
    job_manager = get_job_manager()
    return job_manager.get_job_status(job_id)
