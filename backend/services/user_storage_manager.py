"""SQLite-based user storage manager for efficient quota tracking"""

import sqlite3
import threading
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from backend.models.user_storage import UserStorageUsage
from backend.config import config

logger = logging.getLogger(__name__)


class UserStorageManager:
    """Manages user storage quotas with SQLite persistence"""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize storage manager with database path"""
        if db_path is None:
            # Use same database as main app
            db_path = config.database.path

        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()

    def _init_database(self):
        """Initialize database tables for storage tracking"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_storage_usage (
                    user_id TEXT PRIMARY KEY,
                    total_bytes INTEGER DEFAULT 0,
                    file_count INTEGER DEFAULT 0,
                    last_updated TEXT,
                    quota_bytes INTEGER DEFAULT 52428800
                )
            """)

            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_storage_user_id 
                ON user_storage_usage(user_id)
            """)

            conn.commit()
            logger.info("User storage database initialized")

    def get_user_usage(self, user_id: str) -> UserStorageUsage:
        """Get storage usage for a specific user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM user_storage_usage WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()

            if row:
                return UserStorageUsage(
                    user_id=row[0],
                    total_bytes=row[1],
                    file_count=row[2],
                    last_updated=datetime.fromisoformat(row[3]) if row[3] else None,
                    quota_bytes=row[4],
                )
            else:
                # Create new user entry
                usage = UserStorageUsage(user_id=user_id)
                self._save_usage(usage)
                return usage

    def update_user_usage(self, user_id: str, total_bytes: int, file_count: int):
        """Update user storage usage"""
        usage = UserStorageUsage(
            user_id=user_id,
            total_bytes=total_bytes,
            file_count=file_count,
            last_updated=datetime.utcnow(),
        )
        self._save_usage(usage)

    def add_file(self, user_id: str, file_size_bytes: int):
        """Add a file to user's storage usage"""
        usage = self.get_user_usage(user_id)
        usage.add_file(file_size_bytes)
        self._save_usage(usage)

    def remove_file(self, user_id: str, file_size_bytes: int):
        """Remove a file from user's storage usage"""
        usage = self.get_user_usage(user_id)
        usage.remove_file(file_size_bytes)
        self._save_usage(usage)

    def can_add_file(self, user_id: str, file_size_bytes: int) -> bool:
        """Check if user can add a file of this size"""
        usage = self.get_user_usage(user_id)
        return usage.can_add_file(file_size_bytes)

    def get_quota_info(self, user_id: str) -> Dict[str, Any]:
        """Get quota information for user"""
        usage = self.get_user_usage(user_id)
        return usage.to_dict()

    def set_user_quota(self, user_id: str, quota_bytes: int):
        """Set custom quota for a user"""
        usage = self.get_user_usage(user_id)
        usage.quota_bytes = quota_bytes
        self._save_usage(usage)

    def _save_usage(self, usage: UserStorageUsage):
        """Save usage to database"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO user_storage_usage 
                    (user_id, total_bytes, file_count, last_updated, quota_bytes)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        usage.user_id,
                        usage.total_bytes,
                        usage.file_count,
                        usage.last_updated.isoformat() if usage.last_updated else None,
                        usage.quota_bytes,
                    ),
                )
                conn.commit()

    def recalculate_usage(self, user_id: str, storage_path: str) -> int:
        """
        Recalculate usage from filesystem (for maintenance)

        Returns:
            Number of files found
        """
        from pathlib import Path

        user_dir = Path(storage_path) / user_id
        total_bytes = 0
        file_count = 0

        if user_dir.exists():
            for file_path in user_dir.rglob("*"):
                if file_path.is_file():
                    total_bytes += file_path.stat().st_size
                    file_count += 1

        self.update_user_usage(user_id, total_bytes, file_count)
        logger.info(
            f"Recalculated usage for {user_id}: {file_count} files, {total_bytes} bytes"
        )

        return file_count

    def cleanup_orphaned_records(self, storage_path: str) -> int:
        """
        Clean up usage records for users with no files

        Returns:
            Number of records cleaned up
        """
        from pathlib import Path

        storage = Path(storage_path)
        cleaned_count = 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT user_id FROM user_storage_usage")
            for row in cursor.fetchall():
                user_id = row[0]
                user_dir = storage / user_id

                if not user_dir.exists() or not any(user_dir.iterdir()):
                    # Remove the record
                    conn.execute(
                        "DELETE FROM user_storage_usage WHERE user_id = ?", (user_id,)
                    )
                    cleaned_count += 1
                    logger.info(f"Cleaned up orphaned record for user {user_id}")

            conn.commit()

        return cleaned_count

    def get_global_stats(self) -> Dict[str, Any]:
        """Get global storage statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    SUM(total_bytes) as total_bytes,
                    SUM(file_count) as total_files,
                    AVG(total_bytes) as avg_bytes_per_user,
                    MAX(total_bytes) as max_bytes_per_user
                FROM user_storage_usage
            """)
            row = cursor.fetchone()

            return {
                "total_users": row[0] or 0,
                "total_bytes": row[1] or 0,
                "total_files": row[2] or 0,
                "total_mb": (row[1] or 0) / (1024 * 1024),
                "avg_bytes_per_user": row[3] or 0,
                "avg_mb_per_user": (row[3] or 0) / (1024 * 1024),
                "max_bytes_per_user": row[4] or 0,
                "max_mb_per_user": (row[4] or 0) / (1024 * 1024),
            }


# Global storage manager instance
_storage_manager: Optional[UserStorageManager] = None


def get_storage_manager() -> UserStorageManager:
    """Get global storage manager instance"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = UserStorageManager()
    return _storage_manager
