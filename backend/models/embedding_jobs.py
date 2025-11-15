"""Models for tracking embedding generation jobs"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import json


class JobStatus(str, Enum):
    """Embedding job status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class EmbeddingJob:
    """Model for tracking embedding generation jobs"""

    id: str
    status: JobStatus
    progress: int = 0  # 0-100
    message: str = ""
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    error_details: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "id": self.id,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "successful_items": self.successful_items,
            "failed_items": self.failed_items,
            "error_details": self.error_details,
            "metadata": json.dumps(self.metadata) if self.metadata else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmbeddingJob":
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

        # Parse metadata
        metadata = None
        if data.get("metadata"):
            try:
                metadata = json.loads(data["metadata"])
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        return cls(
            id=data["id"],
            status=JobStatus(data["status"]),
            progress=data.get("progress", 0),
            message=data.get("message", ""),
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            total_items=data.get("total_items", 0),
            processed_items=data.get("processed_items", 0),
            successful_items=data.get("successful_items", 0),
            failed_items=data.get("failed_items", 0),
            error_details=data.get("error_details"),
            metadata=metadata,
        )

    def start(self):
        """Mark job as started"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.message = "Embedding generation started"

    def update_progress(
        self, processed: int, successful: int, failed: int, message: str = ""
    ):
        """Update job progress"""
        self.processed_items = processed
        self.successful_items = successful
        self.failed_items = failed
        if self.total_items > 0:
            self.progress = int((processed / self.total_items) * 100)
        if message:
            self.message = message

    def complete(
        self,
        success_count: int,
        failed_count: int,
        message: str = "Embedding generation completed",
    ):
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.successful_items = success_count
        self.failed_items = failed_count
        self.processed_items = success_count + failed_count
        self.progress = 100
        self.message = message

    def fail(self, error_message: str):
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_details = error_message
        self.message = f"Embedding generation failed: {error_message}"

    def cancel(self):
        """Mark job as cancelled"""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.message = "Embedding generation cancelled"

    def get_duration(self) -> Optional[float]:
        """Get job duration in seconds"""
        if not self.started_at:
            return None

        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()

    def is_finished(self) -> bool:
        """Check if job is finished (completed, failed, or cancelled)"""
        return self.status in [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        ]

    def is_active(self) -> bool:
        """Check if job is currently running"""
        return self.status == JobStatus.RUNNING
