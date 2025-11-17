"""Models for tracking presentation generation jobs with database persistence"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import json

from .progress_tracking import DetailedProgress, ProgressStep


class JobStatus(str, Enum):
    """Presentation job status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobPriority(str, Enum):
    """Job priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class PresentationJob:
    """Model for tracking presentation generation jobs with database backing"""

    id: str
    lesson_id: str
    user_id: str
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    progress: int = 0  # 0-100
    message: str = ""

    # Timing fields
    created_at: Optional[datetime] = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: int = 30

    # Result fields
    presentation_id: Optional[str] = None
    slide_count: Optional[int] = None
    result_data: Optional[Dict[str, Any]] = None

    # Retry and error handling
    retry_count: int = 0
    max_retries: int = 2
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

    # Configuration
    style: str = "default"
    use_llm_polish: bool = True

    # Worker and tracking
    worker_id: Optional[str] = None  # ID of the worker processing this job
    queue_position: Optional[int] = None

    # Performance metrics
    processing_time_seconds: Optional[float] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.error_details is None:
            self.error_details = {}
        if self.result_data is None:
            self.result_data = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "id": self.id,
            "lesson_id": self.lesson_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "progress": self.progress,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "timeout_seconds": self.timeout_seconds,
            "presentation_id": self.presentation_id,
            "slide_count": self.slide_count,
            "result_data": json.dumps(self.result_data) if self.result_data else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "error_details": json.dumps(self.error_details) if self.error_details else None,
            "style": self.style,
            "use_llm_polish": int(self.use_llm_polish),  # Convert boolean to integer
            "worker_id": self.worker_id,
            "queue_position": self.queue_position,
            "processing_time_seconds": self.processing_time_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PresentationJob":
        """Create from dictionary from database"""
        # Parse datetime fields
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        started_at = None
        if data.get("started_at"):
            started_at = datetime.fromisoformat(data["started_at"])

        completed_at = None
        if data.get("completed_at"):
            completed_at = datetime.fromisoformat(data["completed_at"])

        # Parse JSON fields
        result_data = None
        if data.get("result_data"):
            try:
                result_data = json.loads(data["result_data"])
            except (json.JSONDecodeError, TypeError):
                result_data = {}

        error_details = None
        if data.get("error_details"):
            try:
                error_details = json.loads(data["error_details"])
            except (json.JSONDecodeError, TypeError):
                error_details = {}

        return cls(
            id=data["id"],
            lesson_id=data["lesson_id"],
            user_id=data["user_id"],
            status=JobStatus(data["status"]),
            priority=JobPriority(data.get("priority", "normal")),
            progress=data.get("progress", 0),
            message=data.get("message", ""),
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            timeout_seconds=data.get("timeout_seconds", 30),
            presentation_id=data.get("presentation_id"),
            slide_count=data.get("slide_count"),
            result_data=result_data,
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 2),
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
            error_details=error_details,
            style=data.get("style", "default"),
            use_llm_polish=bool(data.get("use_llm_polish", 1)),
            worker_id=data.get("worker_id"),
            queue_position=data.get("queue_position"),
            processing_time_seconds=data.get("processing_time_seconds"),
        )

    def start(self, worker_id: Optional[str] = None):
        """Mark job as started"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.worker_id = worker_id
        self.message = "Presentation generation started"
        self.progress = 0

    def update_progress(self, progress: int, message: str = ""):
        """Update job progress"""
        self.progress = max(0, min(100, progress))
        if message:
            self.message = message

    def get_detailed_progress(self) -> Optional[DetailedProgress]:
        """Get detailed progress information for this job."""
        if not hasattr(self, '_detailed_progress') or self._detailed_progress is None:
            self._detailed_progress = DetailedProgress(job_id=self.id)
        return self._detailed_progress

    def set_detailed_progress(self, progress: DetailedProgress):
        """Set detailed progress information for this job."""
        self._detailed_progress = progress
        # Update basic progress to match detailed progress
        self.progress = int(progress.overall_progress)
        self.message = progress.current_message or self.message

    def complete(
        self,
        presentation_id: str,
        slide_count: int,
        result_data: Optional[Dict[str, Any]] = None,
        message: str = "Presentation generation completed",
    ):
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.presentation_id = presentation_id
        self.slide_count = slide_count
        self.progress = 100
        self.message = message

        if result_data:
            self.result_data = result_data

        # Calculate processing time
        if self.started_at:
            self.processing_time_seconds = (self.completed_at - self.started_at).total_seconds()

    def fail(self, error_code: str, error_message: str, error_details: Optional[Dict[str, Any]] = None):
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_code = error_code
        self.error_message = error_message

        if error_details:
            self.error_details.update(error_details)

        self.message = f"Presentation generation failed: {error_message}"

        # Calculate processing time
        if self.started_at:
            self.processing_time_seconds = (self.completed_at - self.started_at).total_seconds()

    def timeout(self, message: str = "Presentation generation timed out"):
        """Mark job as timed out"""
        self.status = JobStatus.TIMEOUT
        self.completed_at = datetime.utcnow()
        self.error_code = "TIMEOUT"
        self.error_message = message
        self.message = message

        # Calculate processing time
        if self.started_at:
            self.processing_time_seconds = (self.completed_at - self.started_at).total_seconds()

    def cancel(self, reason: str = "Job cancelled"):
        """Mark job as cancelled"""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.error_code = "CANCELLED"
        self.error_message = reason
        self.message = reason

        # Calculate processing time if partially executed
        if self.started_at:
            self.processing_time_seconds = (self.completed_at - self.started_at).total_seconds()

    def retry(self) -> bool:
        """Check if job can be retried and prepare for retry"""
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            self.status = JobStatus.PENDING
            self.started_at = None
            self.completed_at = None
            self.error_code = None
            self.error_message = None
            self.error_details = {}
            self.progress = 0
            self.worker_id = None
            self.message = f"Retry attempt {self.retry_count}"
            return True
        return False

    def get_duration(self) -> Optional[float]:
        """Get job duration in seconds"""
        if not self.started_at:
            return None

        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()

    def is_finished(self) -> bool:
        """Check if job is finished (completed, failed, cancelled, or timed out)"""
        return self.status in [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.TIMEOUT,
        ]

    def is_active(self) -> bool:
        """Check if job is currently running"""
        return self.status == JobStatus.RUNNING

    def can_cancel(self) -> bool:
        """Check if job can be cancelled"""
        return self.status in [JobStatus.PENDING, JobStatus.RUNNING]

    def get_age_minutes(self) -> float:
        """Get job age in minutes"""
        if not self.created_at:
            return 0.0
        return (datetime.utcnow() - self.created_at).total_seconds() / 60.0

    def to_status_dict(self) -> Dict[str, Any]:
        """Convert to status dictionary for API responses"""
        return {
            "job_id": self.id,
            "status": self.status.value,
            "priority": self.priority.value,
            "lesson_id": self.lesson_id,
            "progress": self.progress,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "presentation_id": self.presentation_id,
            "slide_count": self.slide_count,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "processing_time_seconds": self.processing_time_seconds,
            "style": self.style,
            "use_llm_polish": self.use_llm_polish,
            "detailed_progress": self.get_detailed_progress().to_dict() if hasattr(self, '_detailed_progress') else None,
        }