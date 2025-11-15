"""SQLite-based embedding job manager for persistent job tracking"""

import sqlite3
import uuid
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from backend.models.embedding_jobs import EmbeddingJob, JobStatus
from backend.config import config

logger = logging.getLogger(__name__)


class EmbeddingJobManager:
    """Manages embedding generation jobs with SQLite persistence"""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize job manager with database path"""
        if db_path is None:
            # Use same database as main app
            db_path = config.database.path

        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()

    def _init_database(self):
        """Initialize database tables for job tracking"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embedding_jobs (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    progress INTEGER DEFAULT 0,
                    message TEXT DEFAULT '',
                    created_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    total_items INTEGER DEFAULT 0,
                    processed_items INTEGER DEFAULT 0,
                    successful_items INTEGER DEFAULT 0,
                    failed_items INTEGER DEFAULT 0,
                    error_details TEXT,
                    metadata TEXT
                )
            """)

            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_embedding_jobs_status 
                ON embedding_jobs(status)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_embedding_jobs_created_at 
                ON embedding_jobs(created_at)
            """)

            conn.commit()
            logger.info("Embedding job database initialized")

    def create_job(
        self, total_items: int = 0, metadata: Optional[Dict[str, Any]] = None
    ) -> EmbeddingJob:
        """Create a new embedding job"""
        job_id = str(uuid.uuid4())

        job = EmbeddingJob(
            id=job_id,
            status=JobStatus.PENDING,
            total_items=total_items,
            metadata=metadata or {},
        )

        self._save_job(job)
        logger.info(f"Created embedding job {job_id}")
        return job

    def get_job(self, job_id: str) -> Optional[EmbeddingJob]:
        """Get job by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM embedding_jobs WHERE id = ?", (job_id,)
            )
            row = cursor.fetchone()

            if row:
                return EmbeddingJob.from_dict(dict(row))
            return None

    def update_job(self, job: EmbeddingJob):
        """Update job in database"""
        self._save_job(job)

    def _save_job(self, job: EmbeddingJob):
        """Save job to database (insert or update)"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                data = job.to_dict()
                conn.execute(
                    """
                    INSERT OR REPLACE INTO embedding_jobs 
                    (id, status, progress, message, created_at, started_at, completed_at,
                     total_items, processed_items, successful_items, failed_items, 
                     error_details, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        data["id"],
                        data["status"],
                        data["progress"],
                        data["message"],
                        data["created_at"],
                        data["started_at"],
                        data["completed_at"],
                        data["total_items"],
                        data["processed_items"],
                        data["successful_items"],
                        data["failed_items"],
                        data["error_details"],
                        data["metadata"],
                    ),
                )
                conn.commit()

    def get_active_job(self) -> Optional[EmbeddingJob]:
        """Get currently running job"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM embedding_jobs WHERE status = ? ORDER BY created_at DESC LIMIT 1",
                (JobStatus.RUNNING.value,),
            )
            row = cursor.fetchone()

            if row:
                return EmbeddingJob.from_dict(dict(row))
            return None

    def get_recent_jobs(self, limit: int = 10) -> List[EmbeddingJob]:
        """Get recent jobs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM embedding_jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()

            return [EmbeddingJob.from_dict(dict(row)) for row in rows]

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        job = self.get_job(job_id)
        if job and job.status == JobStatus.RUNNING:
            job.cancel()
            self.update_job(job)
            logger.info(f"Cancelled embedding job {job_id}")
            return True
        return False

    def cleanup_old_jobs(self, days: int = 30) -> int:
        """Clean up old completed jobs"""
        cutoff_date = datetime.utcnow().replace(day=datetime.utcnow().day - days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE FROM embedding_jobs 
                WHERE status IN (?, ?, ?) AND completed_at < ?
                """,
                (
                    JobStatus.COMPLETED.value,
                    JobStatus.FAILED.value,
                    JobStatus.CANCELLED.value,
                    cutoff_date.isoformat(),
                ),
            )
            deleted_count = cursor.rowcount
            conn.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old embedding jobs")

            return deleted_count

    def get_job_stats(self) -> Dict[str, Any]:
        """Get overall job statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Count jobs by status
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM embedding_jobs 
                GROUP BY status
            """)
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Get most recent job
            cursor = conn.execute("""
                SELECT * FROM embedding_jobs 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            recent_row = cursor.fetchone()

            return {
                "total_jobs": sum(status_counts.values()),
                "pending_jobs": status_counts.get(JobStatus.PENDING.value, 0),
                "running_jobs": status_counts.get(JobStatus.RUNNING.value, 0),
                "completed_jobs": status_counts.get(JobStatus.COMPLETED.value, 0),
                "failed_jobs": status_counts.get(JobStatus.FAILED.value, 0),
                "cancelled_jobs": status_counts.get(JobStatus.CANCELLED.value, 0),
                "most_recent_job": EmbeddingJob.from_dict(dict(recent_row)).to_dict()
                if recent_row
                else None,
            }


# Global job manager instance
_job_manager: Optional[EmbeddingJobManager] = None


def get_job_manager() -> EmbeddingJobManager:
    """Get global job manager instance"""
    global _job_manager
    if _job_manager is None:
        _job_manager = EmbeddingJobManager()
    return _job_manager
