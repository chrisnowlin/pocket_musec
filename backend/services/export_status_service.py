"""Export status tracking and feedback service."""

import logging
import uuid
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, Future

from backend.lessons.presentation_schema import PresentationDocument, PresentationExport

logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    """Supported export formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    PPTX = "pptx"
    PDF = "pdf"


class ExportStatus(str, Enum):
    """Export operation status."""

    PENDING = "pending"
    PROCESSING = "processing"
    VALIDATING = "validating"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportStep(str, Enum):
    """Export generation steps."""

    INITIALIZING = "initializing"
    EXTRACTING_DATA = "extracting_data"
    FORMATTING_CONTENT = "formatting_content"
    GENERATING_FILE = "generating_file"
    VALIDATING_OUTPUT = "validating_output"
    SAVING_ASSET = "saving_asset"


@dataclass
class ExportProgress:
    """Progress tracking for individual export operation."""

    current_step: ExportStep = ExportStep.INITIALIZING
    progress_percentage: float = 0.0
    estimated_time_remaining: int = 0  # seconds
    processed_bytes: int = 0
    total_bytes: Optional[int] = None
    step_start_time: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExportJob:
    """Export job tracking data."""

    job_id: str
    presentation_id: str
    export_format: ExportFormat
    status: ExportStatus = ExportStatus.PENDING
    progress: ExportProgress = field(default_factory=ExportProgress)
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    export_asset: Optional[PresentationExport] = None
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 1  # Higher number = higher priority


class ExportStatusService:
    """Manages export job status tracking and provides real-time feedback."""

    def __init__(self, max_concurrent_exports: int = 3):
        self.active_jobs: Dict[str, ExportJob] = {}
        self.completed_jobs: Dict[str, ExportJob] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_exports)
        self._lock = threading.Lock()
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_old_jobs, daemon=True
        )
        self._cleanup_thread.start()

    def create_export_job(
        self, presentation_id: str, export_format: ExportFormat, priority: int = 1
    ) -> str:
        """Create a new export job and return its ID."""
        job_id = str(uuid.uuid4())

        job = ExportJob(
            job_id=job_id,
            presentation_id=presentation_id,
            export_format=export_format,
            priority=priority,
        )

        with self._lock:
            self.active_jobs[job_id] = job

        logger.info(
            f"Created export job {job_id} for presentation {presentation_id} in {export_format.value} format (priority: {priority})"
        )
        self._notify_subscribers(job_id, job)
        return job_id

    def update_job_progress(
        self,
        job_id: str,
        step: ExportStep,
        progress_percentage: float,
        estimated_time_remaining: Optional[int] = None,
        processed_bytes: int = 0,
        total_bytes: Optional[int] = None,
    ) -> None:
        """Update the progress of an export job."""
        with self._lock:
            if job_id not in self.active_jobs:
                logger.warning(
                    f"Attempted to update non-existent job {job_id}. Job may have been completed or cancelled."
                )
                return

            job = self.active_jobs[job_id]

            # Update progress
            job.progress.current_step = step
            job.progress.progress_percentage = min(max(progress_percentage, 0.0), 100.0)

            if estimated_time_remaining is not None:
                job.progress.estimated_time_remaining = estimated_time_remaining

            job.progress.processed_bytes = processed_bytes

            if total_bytes is not None:
                job.progress.total_bytes = total_bytes

            # Update job status if needed
            if job.status == ExportStatus.PENDING and step != ExportStep.INITIALIZING:
                job.status = ExportStatus.PROCESSING
                job.started_at = datetime.utcnow()

        logger.debug(
            f"Updated job {job_id} progress: {progress_percentage}% - {step.value}"
        )
        self._notify_subscribers(job_id, job)

    def complete_job_success(
        self, job_id: str, export_asset: PresentationExport
    ) -> None:
        """Mark an export job as successfully completed."""
        with self._lock:
            if job_id not in self.active_jobs:
                logger.warning(
                    f"Attempted to complete non-existent job {job_id}. Job may have already been completed or cancelled."
                )
                return

            job = self.active_jobs[job_id]
            job.status = ExportStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.export_asset = export_asset
            job.progress.progress_percentage = 100.0
            job.progress.current_step = ExportStep.SAVING_ASSET

            # Move to completed jobs
            self.completed_jobs[job_id] = job
            del self.active_jobs[job_id]

        logger.info(
            f"Export job {job_id} completed successfully for presentation {job.presentation_id} in {job.export_format.value} format"
        )
        self._notify_subscribers(job_id, job)

    def complete_job_failure(
        self, job_id: str, error_message: str, retryable: bool = True
    ) -> None:
        """Mark an export job as failed, with retry option if retryable."""
        with self._lock:
            if job_id not in self.active_jobs:
                logger.warning(
                    f"Attempted to fail non-existent job {job_id}. Job may have already been completed or cancelled."
                )
                return

            job = self.active_jobs[job_id]
            job.status = ExportStatus.FAILED
            job.error_message = error_message
            job.completed_at = datetime.utcnow()

            # Check if we should retry
            if retryable and job.retry_count < job.max_retries:
                logger.info(
                    f"Scheduling retry for job {job_id} (attempt {job.retry_count + 1}/{job.max_retries})"
                )
                job.retry_count += 1
                job.status = ExportStatus.PENDING
                # Schedule retry after exponential backoff
                delay = 2**job.retry_count
                threading.Timer(delay, self._schedule_retry, args=[job_id]).start()
            else:
                # Move to completed jobs
                self.completed_jobs[job_id] = job
                del self.active_jobs[job_id]

        logger.error(
            f"Export job {job_id} failed for presentation {job.presentation_id} in {job.export_format.value} format: {error_message}"
        )
        self._notify_subscribers(job_id, job)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel an active export job."""
        with self._lock:
            if job_id not in self.active_jobs:
                logger.warning(
                    f"Attempted to cancel non-existent or already completed job {job_id}"
                )
                return False

            job = self.active_jobs[job_id]
            job.status = ExportStatus.CANCELLED
            job.completed_at = datetime.utcnow()

            self.completed_jobs[job_id] = job
            del self.active_jobs[job_id]

        logger.info(
            f"Export job {job_id} was cancelled for presentation {job.presentation_id} in {job.export_format.value} format"
        )
        self._notify_subscribers(job_id, job)
        return True

    def get_job_status(self, job_id: str) -> Optional[ExportJob]:
        """Get the current status of an export job."""
        with self._lock:
            return self.active_jobs.get(job_id) or self.completed_jobs.get(job_id)

    def get_jobs_for_presentation(self, presentation_id: str) -> List[ExportJob]:
        """Get all export jobs for a specific presentation."""
        with self._lock:
            jobs = []
            for job in self.active_jobs.values():
                if job.presentation_id == presentation_id:
                    jobs.append(job)
            for job in self.completed_jobs.values():
                if job.presentation_id == presentation_id:
                    jobs.append(job)
            return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def subscribe_to_updates(
        self, job_id: str, callback: Callable[[ExportJob], None]
    ) -> None:
        """Subscribe to real-time updates for a specific job."""
        with self._lock:
            if job_id not in self.subscribers:
                self.subscribers[job_id] = []
            self.subscribers[job_id].append(callback)

    def unsubscribe_from_updates(
        self, job_id: str, callback: Callable[[ExportJob], None]
    ) -> None:
        """Unsubscribe from updates for a specific job."""
        with self._lock:
            if job_id in self.subscribers:
                self.subscribers[job_id] = [
                    cb for cb in self.subscribers[job_id] if cb != callback
                ]
                if not self.subscribers[job_id]:
                    del self.subscribers[job_id]

    def _notify_subscribers(self, job_id: str, job: ExportJob) -> None:
        """Notify all subscribers of job updates."""
        if job_id in self.subscribers:
            for callback in self.subscribers[job_id]:
                try:
                    callback(job)
                except Exception as e:
                    logger.error(
                        f"Error notifying subscriber for job {job_id}: {e}. Subscriber callback may be malformed."
                    )

    def _schedule_retry(self, job_id: str) -> None:
        """Schedule a retry for a failed job."""
        # This would integrate with the presentation service to restart the export
        logger.info(f"Retrying export job {job_id}")
        # The actual retry logic would be handled by the presentation service

    def _cleanup_old_jobs(self) -> None:
        """Background thread to clean up old completed jobs."""
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes
                cutoff_time = datetime.utcnow() - timedelta(hours=24)

                with self._lock:
                    old_jobs = [
                        job_id
                        for job_id, job in self.completed_jobs.items()
                        if job.created_at < cutoff_time
                    ]

                    for job_id in old_jobs:
                        del self.completed_jobs[job_id]
                        if job_id in self.subscribers:
                            del self.subscribers[job_id]

                if old_jobs:
                    logger.info(f"Cleaned up {len(old_jobs)} old export jobs")

            except Exception as e:
                logger.error(
                    f"Error in export job cleanup thread: {e}. Cleanup may be incomplete."
                )

    def queue_export_job(
        self,
        presentation_id: str,
        export_format: ExportFormat,
        executor_callback: Callable[[], PresentationExport],
        priority: int = 1,
    ) -> str:
        """Queue and execute an export job with progress tracking."""
        job_id = self.create_export_job(presentation_id, export_format, priority)

        def execute_with_progress():
            try:
                self.update_job_progress(job_id, ExportStep.INITIALIZING, 5, 60)

                # Execute the export function with progress updates
                export_asset = executor_callback()

                self.update_job_progress(job_id, ExportStep.VALIDATING_OUTPUT, 90, 5)
                self.update_job_progress(job_id, ExportStep.SAVING_ASSET, 95, 2)

                self.complete_job_success(job_id, export_asset)

            except Exception as e:
                error_message = f"Export failed: {str(e)}"
                # Don't retry timeouts, permission errors, or invalid format errors
                non_retryable_keywords = [
                    "timeout",
                    "permission",
                    "access denied",
                    "invalid format",
                    "not found",
                ]
                retryable = not any(
                    keyword in error_message.lower()
                    for keyword in non_retryable_keywords
                )
                self.complete_job_failure(job_id, error_message, retryable)

        # Submit to executor
        self.executor.submit(execute_with_progress)
        return job_id

    def get_statistics(self) -> Dict[str, Any]:
        """Get export job statistics."""
        with self._lock:
            total_active = len(self.active_jobs)
            total_completed = len(self.completed_jobs)

            # Count by status
            status_counts = {}
            for job in self.active_jobs.values():
                status_counts[job.status.value] = (
                    status_counts.get(job.status.value, 0) + 1
                )

            for job in self.completed_jobs.values():
                status_counts[job.status.value] = (
                    status_counts.get(job.status.value, 0) + 1
                )

            # Count by format
            format_counts = {}
            for job in list(self.active_jobs.values()) + list(
                self.completed_jobs.values()
            ):
                format_counts[job.export_format.value] = (
                    format_counts.get(job.export_format.value, 0) + 1
                )

            # Recent performance metrics
            recent_jobs = [
                job
                for job in self.completed_jobs.values()
                if job.completed_at
                and job.completed_at > datetime.utcnow() - timedelta(hours=1)
            ]

            avg_duration = 0
            success_rate = 0
            if recent_jobs:
                durations = []
                successful = 0
                for job in recent_jobs:
                    if job.started_at and job.completed_at:
                        duration = (job.completed_at - job.started_at).total_seconds()
                        durations.append(duration)
                    if job.status == ExportStatus.COMPLETED:
                        successful += 1

                if durations:
                    avg_duration = sum(durations) / len(durations)
                if recent_jobs:
                    success_rate = successful / len(recent_jobs) * 100

            return {
                "active_jobs": total_active,
                "completed_jobs": total_completed,
                "status_counts": status_counts,
                "format_counts": format_counts,
                "average_duration_seconds": round(avg_duration, 2),
                "success_rate_percent": round(success_rate, 1),
                "max_concurrent_exports": self.executor._max_workers,
            }


# Global instance
export_status_service = ExportStatusService()
