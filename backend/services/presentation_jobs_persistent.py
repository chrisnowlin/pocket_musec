"""Background job management for presentation generation with database persistence.

This module provides async job execution for presentation generation
using FastAPI BackgroundTasks and database-backed job tracking.
"""

import logging
import time
import uuid
import asyncio
import signal
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

from .presentation_service import PresentationService
from .presentation_errors import (
    PresentationError,
    PresentationErrorCode,
    PresentationErrorLogger,
    ErrorRecoveryStrategy,
    create_error_from_exception,
)
from backend.repositories.presentation_job_repository import PresentationJobRepository
from backend.models.presentation_jobs import (
    PresentationJob,
    JobStatus,
    JobPriority,
)

logger = logging.getLogger(__name__)


class PresentationJobManager:
    """Manages background presentation generation jobs with database persistence."""

    def __init__(
        self,
        presentation_service: Optional[PresentationService] = None,
        job_repository: Optional[PresentationJobRepository] = None,
    ):
        self.presentation_service = presentation_service or PresentationService()
        self.job_repository = job_repository or PresentationJobRepository()
        self.worker_id = str(uuid.uuid4())  # Unique ID for this worker instance
        self.job_timeout_minutes = 10
        self.max_retries = 2
        self.retry_delays = [0, 5, 15]  # seconds for each retry attempt
        self._shutdown_event = asyncio.Event()
        self._setup_signal_handlers()

        # Recover any orphaned jobs on startup
        self._recover_orphaned_jobs()

    def _recover_orphaned_jobs(self) -> None:
        """Recover jobs that were running when the system shut down."""
        try:
            recovered_count = self.job_repository.recover_orphaned_jobs(
                timeout_minutes=self.job_timeout_minutes
            )
            if recovered_count > 0:
                logger.warning(
                    f"Recovered {recovered_count} orphaned presentation jobs on startup"
                )
        except Exception as e:
            logger.error(f"Failed to recover orphaned jobs: {e}")

    def create_job(
        self,
        lesson_id: str,
        user_id: str,
        style: str = "default",
        use_llm_polish: bool = True,
        timeout_seconds: int = 30,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 2,
    ) -> str:
        """Create a new presentation generation job.

        Args:
            lesson_id: ID of the lesson to generate presentation for
            user_id: ID of the user requesting the presentation
            style: Presentation style
            use_llm_polish: Whether to use LLM polishing
            timeout_seconds: Timeout for LLM operations
            priority: Job priority
            max_retries: Maximum number of retry attempts

        Returns:
            Job ID for tracking
        """
        try:
            job = self.job_repository.create_job(
                lesson_id=lesson_id,
                user_id=user_id,
                style=style,
                use_llm_polish=use_llm_polish,
                timeout_seconds=timeout_seconds,
                priority=priority,
                max_retries=max_retries,
            )

            logger.info(f"Created presentation job {job.id} for lesson {lesson_id}")
            return job.id

        except Exception as e:
            logger.error(f"Failed to create presentation job: {e}")
            error = create_error_from_exception(
                e,
                {
                    "operation": "create_job",
                    "lesson_id": lesson_id,
                    "user_id": user_id,
                },
            )
            raise error

    def get_job(self, job_id: str) -> Optional[PresentationJob]:
        """Get a job by ID."""
        try:
            return self.job_repository.get_job(job_id)
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status as a dictionary."""
        try:
            job = self.get_job(job_id)
            if not job:
                return None
            return job.to_status_dict()
        except Exception as e:
            logger.error(f"Failed to get job status {job_id}: {e}")
            return None

    def execute_job(
        self,
        job_id: str,
        style: str = "default",
        use_llm_polish: bool = True,
        timeout_seconds: int = 30,
    ) -> None:
        """Execute a presentation generation job with retry logic and timeout handling.

        This method is designed to be called by FastAPI BackgroundTasks.
        """
        if self._shutdown_event.is_set():
            logger.warning("Job manager is shutting down, skipping job execution")
            return

        job = self.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        if job.status != JobStatus.PENDING:
            logger.warning(f"Job {job_id} is not pending (status: {job.status})")
            return

        logger.info(f"Starting execution of presentation job {job_id}")

        # Mark job as started
        job.start(worker_id=self.worker_id)
        self.job_repository.update_job(job)

        # Execute with retry logic
        last_error = None
        for attempt in range(job.max_retries + 1):
            try:
                # Check if shutdown was requested
                if self._shutdown_event.is_set():
                    logger.info(f"Job execution cancelled due to shutdown: {job_id}")
                    job.fail("SHUTDOWN", "Job cancelled due to system shutdown")
                    self.job_repository.update_job(job)
                    return

                # Calculate actual timeout for this attempt
                actual_timeout = min(timeout_seconds, 300)  # Max 5 minutes per attempt

                # Execute presentation generation with timeout
                if attempt > 0:
                    logger.info(
                        f"Retry attempt {attempt} for job {job_id} after {self.retry_delays[attempt]}s delay"
                    )
                    import time

                    time.sleep(self.retry_delays[attempt])

                presentation = self._execute_with_timeout(
                    job.lesson_id,
                    job.user_id,
                    style,
                    use_llm_polish,
                    actual_timeout,
                )

                # Update job with success result
                result_data = {
                    "presentation_id": presentation.id,
                    "slide_count": len(presentation.slides),
                    "status": presentation.status.value,
                    "retry_attempts": attempt,
                    "worker_id": self.worker_id,
                }

                success = self.job_repository.complete_job(
                    job_id=job_id,
                    presentation_id=presentation.id,
                    slide_count=len(presentation.slides),
                    result_data=result_data,
                )

                if success:
                    logger.info(
                        f"Successfully completed presentation job {job_id} after {attempt} retry attempts"
                    )
                else:
                    logger.error(f"Failed to mark job {job_id} as completed")
                return

            except TimeoutError as e:
                last_error = e
                logger.warning(f"Job {job_id} timed out on attempt {attempt}: {e}")
                if attempt == job.max_retries:
                    self.job_repository.fail_job(
                        job_id=job_id,
                        error_code="TIMEOUT",
                        error_message=str(e),
                        error_details={
                            "timeout_seconds": actual_timeout,
                            "attempts": attempt,
                        },
                    )
                    return

            except PresentationError as e:
                last_error = e
                if e.retry_recommended and attempt < job.max_retries:
                    logger.warning(
                        f"Job {job_id} failed on attempt {attempt}, retrying: {e.user_message}"
                    )
                    time.sleep(e.retry_after_seconds or self.retry_delays[attempt + 1])
                else:
                    self.job_repository.fail_job(
                        job_id=job_id,
                        error_code=e.code.value,
                        error_message=e.user_message,
                        error_details={
                            "technical_message": e.technical_message,
                            "attempts": attempt,
                            "retry_recommended": e.retry_recommended,
                            "retry_after_seconds": e.retry_after_seconds,
                        },
                    )
                    return

            except Exception as e:
                last_error = e
                logger.error(
                    f"Job {job_id} failed on attempt {attempt} with unhandled error: {e}"
                )
                if attempt < job.max_retries:
                    continue
                else:
                    # Convert to structured error
                    structured_error = create_error_from_exception(
                        e,
                        {
                            "job_id": job_id,
                            "attempt": attempt,
                            "operation": "job_execution",
                        },
                    )
                    self.job_repository.fail_job(
                        job_id=job_id,
                        error_code=structured_error.code.value,
                        error_message=structured_error.user_message,
                        error_details={
                            "technical_message": structured_error.technical_message,
                            "exhausted_retries": True,
                        },
                    )
                    return

        # All attempts failed
        if last_error:
            if isinstance(last_error, PresentationError):
                self.job_repository.fail_job(
                    job_id=job_id,
                    error_code=last_error.code.value,
                    error_message=last_error.user_message,
                    error_details={"exhausted_retries": True},
                )
            else:
                structured_error = create_error_from_exception(
                    last_error,
                    {
                        "job_id": job_id,
                        "exhausted_retries": True,
                    },
                )
                self.job_repository.fail_job(
                    job_id=job_id,
                    error_code=structured_error.code.value,
                    error_message=structured_error.user_message,
                    error_details={"exhausted_retries": True},
                )

    def _execute_with_timeout(
        self,
        lesson_id: str,
        user_id: str,
        style: str,
        use_llm_polish: bool,
        timeout_seconds: int,
    ) -> Any:
        """Execute presentation generation with a timeout."""
        try:
            import concurrent.futures
            import threading

            def generate_with_timeout():
                return self.presentation_service.generate_presentation(
                    lesson_id=lesson_id,
                    user_id=user_id,
                    style=style,
                    use_llm_polish=use_llm_polish,
                    timeout_seconds=timeout_seconds,
                )

            # Use ThreadPoolExecutor to enforce timeout
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(generate_with_timeout)
                try:
                    return future.result(timeout=timeout_seconds)
                except concurrent.futures.TimeoutError:
                    future.cancel()
                    raise TimeoutError(
                        f"Presentation generation timed out after {timeout_seconds} seconds"
                    )

        except PresentationError:
            raise
        except TimeoutError:
            raise
        except Exception as e:
            error = create_error_from_exception(
                e,
                {
                    "timeout_seconds": timeout_seconds,
                    "operation": "timeout_execution",
                },
            )
            raise error

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up old completed/failed jobs.

        Args:
            max_age_hours: Maximum age of jobs to keep

        Returns:
            Number of jobs cleaned up
        """
        try:
            return self.job_repository.cleanup_old_jobs(max_age_hours=max_age_hours)
        except Exception as e:
            logger.error(f"Failed to cleanup old jobs: {e}")
            return 0

    def cancel_job(self, job_id: str, reason: str = "User cancelled") -> bool:
        """Cancel a pending or running job.

        Args:
            job_id: ID of the job to cancel
            reason: Reason for cancellation

        Returns:
            True if job was cancelled, False if not found or not cancellable
        """
        try:
            success = self.job_repository.cancel_job(job_id, reason)
            if success:
                logger.info(f"Cancelled presentation job {job_id}: {reason}")
            return success
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False

    def retry_job(self, job_id: str) -> bool:
        """Retry a failed job if retries are available.

        Args:
            job_id: ID of the job to retry

        Returns:
            True if job was queued for retry, False if not found or no retries available
        """
        try:
            success = self.job_repository.retry_job(job_id)
            if success:
                logger.info(f"Queued job {job_id} for retry")
            return success
        except Exception as e:
            logger.error(f"Failed to retry job {job_id}: {e}")
            return False

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        try:
            import signal

            def signal_handler(signum, frame):
                logger.info(f"Received signal {signum}, initiating graceful shutdown")
                self._shutdown_event.set()

            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)

        except Exception as e:
            logger.warning(f"Failed to setup signal handlers: {e}")

    def shutdown_gracefully(self):
        """Initiate graceful shutdown of the job manager."""
        logger.info("Initiating graceful job manager shutdown")
        self._shutdown_event.set()

        # Cancel all pending jobs assigned to this worker
        try:
            running_jobs = self.job_repository.get_running_jobs(
                worker_id=self.worker_id
            )
            for job in running_jobs:
                self.job_repository.fail_job(
                    job_id=job.id,
                    error_code="SHUTDOWN",
                    error_message="Job cancelled due to system shutdown",
                )
                logger.info(f"Cancelled running job {job.id} during shutdown")

            logger.info(f"Cancelled {len(running_jobs)} running jobs during shutdown")
        except Exception as e:
            logger.error(f"Failed to cancel jobs during shutdown: {e}")

    def cancel_running_job(
        self, job_id: str, reason: str = "Running job was cancelled"
    ) -> bool:
        """Attempt to cancel a running job (best effort).

        Args:
            job_id: ID of the running job to cancel
            reason: Reason for cancellation

        Returns:
            True if cancellation was attempted, False if not found or not running
        """
        try:
            success = self.job_repository.fail_job(job_id, "CANCELLED", reason)
            if success:
                logger.info(f"Cancelled running job {job_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to cancel running job {job_id}: {e}")
            return False

    def get_job_health_metrics(self) -> Dict[str, Any]:
        """Get health metrics for the job system."""
        try:
            # Get statistics from repository
            stats = self.job_repository.get_job_statistics(hours=24)

            # Add system-specific metrics
            stats.update(
                {
                    "worker_id": self.worker_id,
                    "shutdown_requested": self._shutdown_event.is_set(),
                    "job_timeout_minutes": self.job_timeout_minutes,
                    "max_retries": self.max_retries,
                }
            )

            # Get running jobs for this worker
            running_jobs = self.job_repository.get_running_jobs(
                worker_id=self.worker_id
            )
            stats["worker_running_jobs"] = len(running_jobs)

            return stats

        except Exception as e:
            logger.error(f"Failed to get job health metrics: {e}")
            return {
                "error": str(e),
                "worker_id": self.worker_id,
                "shutdown_requested": self._shutdown_event.is_set(),
            }

    def get_user_jobs(
        self,
        user_id: str,
        limit: int = 50,
        status: Optional[JobStatus] = None,
        include_finished: bool = True,
    ) -> List[PresentationJob]:
        """Get all jobs for a specific user.

        Args:
            user_id: ID of the user
            limit: Maximum number of jobs to return
            status: Filter by job status
            include_finished: Whether to include finished jobs

        Returns:
            List of jobs for the user, ordered by creation time (newest first)
        """
        try:
            return self.job_repository.get_user_jobs(
                user_id=user_id,
                limit=limit,
                status=status,
                include_finished=include_finished,
            )
        except Exception as e:
            logger.error(f"Failed to get user jobs for {user_id}: {e}")
            return []

    def get_pending_jobs(
        self, limit: int = 100, priority: Optional[JobPriority] = None
    ) -> List[PresentationJob]:
        """Get pending jobs for processing.

        Args:
            limit: Maximum number of jobs to return
            priority: Filter by priority

        Returns:
            List of pending jobs ordered by priority and creation time
        """
        try:
            return self.job_repository.get_pending_jobs(
                limit=limit,
                priority=priority,
                worker_id=self.worker_id,
            )
        except Exception as e:
            logger.error(f"Failed to get pending jobs: {e}")
            return []

    def delete_job(self, job_id: str) -> bool:
        """Delete a job completely.

        Args:
            job_id: ID of the job to delete

        Returns:
            True if job was deleted, False if not found
        """
        try:
            success = self.job_repository.delete_job(job_id)
            if success:
                logger.info(f"Deleted job {job_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            return False


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
    priority: JobPriority = JobPriority.NORMAL,
    max_retries: int = 2,
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
        priority=priority,
        max_retries=max_retries,
    )


def get_presentation_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get the status of a presentation job.

    Convenience function that uses the global job manager.
    """
    job_manager = get_job_manager()
    return job_manager.get_job_status(job_id)


def initialize_job_system() -> PresentationJobManager:
    """Initialize the job system and return the manager instance."""
    global _job_manager
    if _job_manager is None:
        _job_manager = PresentationJobManager()

    # Run startup recovery
    _job_manager._recover_orphaned_jobs()

    return _job_manager
