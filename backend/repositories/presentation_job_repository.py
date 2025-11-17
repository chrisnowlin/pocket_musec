"""Repository for presentation job persistence with advanced job management"""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import logging

from .database import DatabaseManager
from backend.models.presentation_jobs import PresentationJob, JobStatus, JobPriority

logger = logging.getLogger(__name__)


class PresentationJobRepository:
    """Handles CRUD and advanced operations for presentation jobs"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager()
        self._ensure_table_exists()

    def _ensure_table_exists(self) -> None:
        """Ensure the presentation_jobs table exists"""
        conn = self.db_manager.get_connection()
        try:
            # Create the table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS presentation_jobs (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority TEXT NOT NULL DEFAULT 'normal',
                    progress INTEGER DEFAULT 0,
                    message TEXT DEFAULT '',
                    created_at TIMESTAMP NOT NULL,
                    started_at TIMESTAMP NULL,
                    completed_at TIMESTAMP NULL,
                    timeout_seconds INTEGER DEFAULT 30,
                    presentation_id TEXT NULL,
                    slide_count INTEGER NULL,
                    result_data TEXT NULL,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 2,
                    error_code TEXT NULL,
                    error_message TEXT NULL,
                    error_details TEXT NULL,
                    style TEXT DEFAULT 'default',
                    use_llm_polish INTEGER DEFAULT 1,
                    worker_id TEXT NULL,
                    queue_position INTEGER NULL,
                    processing_time_seconds REAL NULL,

                    -- Foreign keys
                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
                );
            """)

            # Create indexes separately (SQLite doesn't support inline INDEX in CREATE TABLE)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON presentation_jobs(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_user_status ON presentation_jobs(user_id, status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created ON presentation_jobs(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_priority_status ON presentation_jobs(priority, status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_lesson ON presentation_jobs(lesson_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_worker ON presentation_jobs(worker_id)")

            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to create presentation_jobs table: {e}")
            raise
        finally:
            conn.close()

    def create_job(
        self,
        lesson_id: str,
        user_id: str,
        style: str = "default",
        use_llm_polish: bool = True,
        timeout_seconds: int = 30,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 2,
    ) -> PresentationJob:
        """Create a new presentation job"""
        job_id = str(uuid.uuid4())

        job = PresentationJob(
            id=job_id,
            lesson_id=lesson_id,
            user_id=user_id,
            style=style,
            use_llm_polish=use_llm_polish,
            timeout_seconds=timeout_seconds,
            priority=priority,
            max_retries=max_retries,
        )

        conn = self.db_manager.get_connection()
        try:
            data = job.to_dict()
            columns = list(data.keys())
            placeholders = ", ".join(["?"] * len(columns))
            values = list(data.values())

            conn.execute(
                f"INSERT INTO presentation_jobs ({', '.join(columns)}) VALUES ({placeholders})",
                values
            )
            conn.commit()

            logger.info(f"Created presentation job {job_id} for lesson {lesson_id}")
            return job

        except sqlite3.Error as e:
            logger.error(f"Failed to create presentation job: {e}")
            raise
        finally:
            conn.close()

    def get_job(self, job_id: str) -> Optional[PresentationJob]:
        """Get a job by ID"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM presentation_jobs WHERE id = ?", (job_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_job(row)
        finally:
            conn.close()

    def update_job(self, job: PresentationJob) -> bool:
        """Update an existing job"""
        conn = self.db_manager.get_connection()
        try:
            data = job.to_dict()
            columns = list(data.keys())

            # Build UPDATE statement
            set_clause = ", ".join([f"{col} = ?" for col in columns])
            values = list(data.values()) + [job.id]

            cursor = conn.execute(
                f"UPDATE presentation_jobs SET {set_clause} WHERE id = ?",
                values
            )
            conn.commit()

            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Failed to update job {job.id}: {e}")
            raise
        finally:
            conn.close()

    def get_user_jobs(
        self,
        user_id: str,
        limit: int = 50,
        status: Optional[JobStatus] = None,
        include_finished: bool = True,
    ) -> List[PresentationJob]:
        """Get jobs for a specific user"""
        conn = self.db_manager.get_connection()
        try:
            query = """
                SELECT * FROM presentation_jobs
                WHERE user_id = ?
            """
            params = [user_id]

            if not include_finished:
                query += " AND status NOT IN ('completed', 'failed', 'cancelled', 'timeout')"

            if status:
                query += " AND status = ?"
                params.append(status.value)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            return [self._row_to_job(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def get_pending_jobs(
        self,
        limit: int = 100,
        priority: Optional[JobPriority] = None,
        worker_id: Optional[str] = None,
    ) -> List[PresentationJob]:
        """Get pending jobs for processing"""
        conn = self.db_manager.get_connection()
        try:
            query = """
                SELECT * FROM presentation_jobs
                WHERE status = 'pending'
            """
            params = []

            if priority:
                query += " AND priority = ?"
                params.append(priority.value)

            if worker_id:
                query += " AND worker_id = ?"
                params.append(worker_id)

            query += """
                ORDER BY
                    CASE priority
                        WHEN 'urgent' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'normal' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    created_at ASC
                LIMIT ?
            """
            params.append(limit)

            cursor = conn.execute(query, params)
            return [self._row_to_job(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def get_running_jobs(self, worker_id: Optional[str] = None) -> List[PresentationJob]:
        """Get currently running jobs"""
        conn = self.db_manager.get_connection()
        try:
            query = """
                SELECT * FROM presentation_jobs
                WHERE status = 'running'
            """
            params = []

            if worker_id:
                query += " AND worker_id = ?"
                params.append(worker_id)

            query += " ORDER BY started_at ASC"

            cursor = conn.execute(query, params)
            return [self._row_to_job(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def update_queue_positions(self, jobs: List[PresentationJob]) -> int:
        """Update queue positions for a list of jobs"""
        if not jobs:
            return 0

        conn = self.db_manager.get_connection()
        try:
            updated_count = 0
            for position, job in enumerate(jobs, 1):
                if job.queue_position != position:
                    cursor = conn.execute(
                        "UPDATE presentation_jobs SET queue_position = ? WHERE id = ?",
                        (position, job.id)
                    )
                    updated_count += cursor.rowcount
                    job.queue_position = position

            conn.commit()
            return updated_count

        except sqlite3.Error as e:
            logger.error(f"Failed to update queue positions: {e}")
            raise
        finally:
            conn.close()

    def cancel_job(self, job_id: str, reason: str = "User cancelled") -> bool:
        """Cancel a job if it's cancellable"""
        job = self.get_job(job_id)
        if not job or not job.can_cancel():
            return False

        job.cancel(reason)
        return self.update_job(job)

    def fail_job(self, job_id: str, error_code: str, error_message: str,
                 error_details: Optional[Dict[str, Any]] = None) -> bool:
        """Mark a job as failed with error details"""
        job = self.get_job(job_id)
        if not job:
            return False

        job.fail(error_code, error_message, error_details)
        return self.update_job(job)

    def complete_job(self, job_id: str, presentation_id: str, slide_count: int,
                     result_data: Optional[Dict[str, Any]] = None) -> bool:
        """Mark a job as completed"""
        job = self.get_job(job_id)
        if not job:
            return False

        job.complete(presentation_id, slide_count, result_data)
        return self.update_job(job)

    def retry_job(self, job_id: str) -> bool:
        """Retry a failed job if retries are available"""
        job = self.get_job(job_id)
        if not job or not job.retry():
            return False

        return self.update_job(job)

    def cleanup_old_jobs(self, max_age_hours: int = 24,
                         exclude_statuses: Optional[List[JobStatus]] = None) -> int:
        """Clean up old finished jobs"""
        exclude_statuses = exclude_statuses or [JobStatus.RUNNING, JobStatus.PENDING]
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        conn = self.db_manager.get_connection()
        try:
            status_placeholders = ", ".join(["?"] * len(exclude_statuses))
            status_values = [status.value for status in exclude_statuses]

            cursor = conn.execute(
                f"""
                DELETE FROM presentation_jobs
                WHERE completed_at IS NOT NULL
                AND completed_at < ?
                AND status NOT IN ({status_placeholders})
                """,
                [cutoff_time.isoformat()] + status_values
            )
            conn.commit()
            deleted_count = cursor.rowcount

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old presentation jobs")

            return deleted_count

        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup old jobs: {e}")
            raise
        finally:
            conn.close()

    def get_job_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get job statistics for monitoring"""
        since = datetime.utcnow() - timedelta(hours=hours)

        conn = self.db_manager.get_connection()
        try:
            # Total counts
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                    COUNT(CASE WHEN status = 'running' THEN 1 END) as running,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled,
                    COUNT(CASE WHEN status = 'timeout' THEN 1 END) as timeout,
                    AVG(CASE WHEN processing_time_seconds IS NOT NULL THEN processing_time_seconds END) as avg_processing_time
                FROM presentation_jobs
                WHERE created_at >= ?
            """, (since.isoformat(),))

            row = cursor.fetchone()
            stats = dict(row) if row else {}

            # Recent jobs (last hour)
            recent_since = datetime.utcnow() - timedelta(hours=1)
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as recent_total,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as recent_completed,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as recent_failed
                FROM presentation_jobs
                WHERE created_at >= ?
            """, (recent_since.isoformat(),))

            recent_row = cursor.fetchone()
            if recent_row:
                stats['recent_total'] = recent_row['recent_total']
                stats['recent_completed'] = recent_row['recent_completed']
                stats['recent_failed'] = recent_row['recent_failed']

                # Calculate failure rates
                if stats['total'] > 0:
                    stats['failure_rate'] = (stats['failed'] / stats['total']) * 100
                if stats['recent_total'] > 0:
                    stats['recent_failure_rate'] = (stats['recent_failed'] / stats['recent_total']) * 100

            # Priority distribution
            cursor = conn.execute("""
                SELECT priority, COUNT(*) as count
                FROM presentation_jobs
                WHERE created_at >= ? AND status IN ('pending', 'running')
                GROUP BY priority
            """, (since.isoformat(),))

            priority_stats = {row['priority']: row['count'] for row in cursor.fetchall()}
            stats['priority_distribution'] = priority_stats

            # Oldest pending job
            cursor = conn.execute("""
                SELECT id, created_at
                FROM presentation_jobs
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT 1
            """)
            oldest_row = cursor.fetchone()
            if oldest_row:
                oldest_job = self._row_to_job(oldest_row)
                stats['oldest_pending_job_age_minutes'] = oldest_job.get_age_minutes()
                stats['oldest_pending_job_id'] = oldest_job.id

            return stats

        except sqlite3.Error as e:
            logger.error(f"Failed to get job statistics: {e}")
            raise
        finally:
            conn.close()

    def recover_orphaned_jobs(self, timeout_minutes: int = 30) -> int:
        """Recover jobs that were running but appear to be orphaned"""
        timeout_since = datetime.utcnow() - timedelta(minutes=timeout_minutes)

        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                UPDATE presentation_jobs
                SET status = 'failed',
                    error_code = 'ORPHANED',
                    error_message = 'Job was orphaned during system restart',
                    completed_at = ?
                WHERE status = 'running' AND started_at < ?
            """, (datetime.utcnow().isoformat(), timeout_since.isoformat()))

            conn.commit()
            recovered_count = cursor.rowcount

            if recovered_count > 0:
                logger.warning(f"Recovered {recovered_count} orphaned presentation jobs")

            return recovered_count

        except sqlite3.Error as e:
            logger.error(f"Failed to recover orphaned jobs: {e}")
            raise
        finally:
            conn.close()

    def bulk_update_status(self, job_ids: List[str], new_status: JobStatus) -> int:
        """Update status for multiple jobs at once"""
        if not job_ids:
            return 0

        conn = self.db_manager.get_connection()
        try:
            placeholders = ", ".join(["?"] * len(job_ids))
            cursor = conn.execute(
                f"""
                UPDATE presentation_jobs
                SET status = ?, completed_at = ?
                WHERE id IN ({placeholders})
                """,
                [new_status.value, datetime.utcnow().isoformat()] + job_ids
            )
            conn.commit()
            return cursor.rowcount

        except sqlite3.Error as e:
            logger.error(f"Failed to bulk update job status: {e}")
            raise
        finally:
            conn.close()

    def delete_job(self, job_id: str) -> bool:
        """Delete a job completely"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM presentation_jobs WHERE id = ?", (job_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            raise
        finally:
            conn.close()

    def _row_to_job(self, row: sqlite3.Row) -> PresentationJob:
        """Convert database row to PresentationJob"""
        return PresentationJob.from_dict(dict(row))