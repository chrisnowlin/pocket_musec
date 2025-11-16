"""File storage utility for PocketMusec

Handles permanent file storage with duplicate detection, hash calculation,
and directory organization by date.
"""

import os
import hashlib
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import logging

from backend.config import config

logger = logging.getLogger(__name__)


class FileStorageManager:
    """Manages permanent file storage with organization and deduplication"""

    def __init__(self, storage_root: Optional[str] = None):
        """Initialize file storage manager

        Args:
            storage_root: Root directory for file storage. If None, uses config.
        """
        self.storage_root = Path(
            storage_root or config.file_storage.storage_root
        ).resolve()
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def get_date_directory(self, date: Optional[datetime] = None) -> Path:
        """Get directory path for a specific date (YYYY/MM/DD structure)

        Args:
            date: Date to create directory for. If None, uses current date.

        Returns:
            Path object for the date directory
        """
        if date is None:
            date = datetime.now()

        year = date.strftime("%Y")
        month = date.strftime("%m")
        day = date.strftime("%d")

        return self.storage_root / year / month / day

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file

        Args:
            file_path: Path to the file to hash

        Returns:
            Hexadecimal SHA256 hash string
        """
        hash_sha256 = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files efficiently
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)

            return hash_sha256.hexdigest()

        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            raise

    def get_file_extension(self, filename: str) -> str:
        """Get file extension in lowercase with dot prefix

        Args:
            filename: Original filename

        Returns:
            File extension (e.g., '.pdf') or empty string if no extension
        """
        return Path(filename).suffix.lower()

    def is_allowed_extension(self, filename: str) -> bool:
        """Check if file extension is allowed

        Args:
            filename: Filename to check

        Returns:
            True if extension is allowed, False otherwise
        """
        extension = self.get_file_extension(filename)
        return extension in config.file_storage.allowed_extensions

    def is_valid_file_size(self, file_path: str) -> bool:
        """Check if file size is within allowed limits

        Args:
            file_path: Path to the file to check

        Returns:
            True if file size is valid, False otherwise
        """
        try:
            file_size = os.path.getsize(file_path)
            return file_size <= config.file_storage.max_file_size

        except Exception as e:
            logger.error(f"Failed to check file size for {file_path}: {e}")
            return False

    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename using UUID while preserving extension

        Args:
            original_filename: Original file name

        Returns:
            Unique filename with same extension
        """
        extension = self.get_file_extension(original_filename)
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{extension}" if extension else unique_id

    def save_file_permanently(
        self, temp_file_path: str, original_filename: str
    ) -> Tuple[str, str]:
        """Save a file permanently with proper directory structure and UUID naming

        Args:
            temp_file_path: Path to temporary file to save
            original_filename: Original filename from upload

        Returns:
            Tuple of (file_id, relative_path) where file_id is the UUID filename
            and relative_path is the path relative to storage root
        """
        try:
            # Validate file
            if not self.is_allowed_extension(original_filename):
                raise ValueError(
                    f"File extension not allowed: {self.get_file_extension(original_filename)}"
                )

            if not self.is_valid_file_size(temp_file_path):
                raise ValueError(f"File size exceeds maximum allowed size")

            # Generate unique filename and directory structure
            unique_filename = self.generate_unique_filename(original_filename)
            date_directory = self.get_date_directory()
            date_directory.mkdir(parents=True, exist_ok=True)

            # Final file path
            final_path = date_directory / unique_filename
            relative_path = final_path.relative_to(self.storage_root)

            # Copy file to permanent location
            shutil.copy2(temp_file_path, final_path)

            logger.info(f"Saved file permanently: {original_filename} -> {final_path}")

            return unique_filename, str(relative_path)

        except Exception as e:
            logger.error(f"Failed to save file permanently: {e}")
            raise

    def check_duplicate_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Check if a file with the same hash already exists

        Args:
            file_hash: SHA256 hash to search for

        Returns:
            Dictionary with file info if duplicate found, None otherwise
            This should be used with FileRepository for database lookup
        """
        # This method will work with FileRepository to check for duplicates
        # For now, return None and let the repository handle the lookup
        return None

    def _validate_and_resolve_path(self, relative_path: str) -> Path:
        """Validate and resolve a relative path to ensure it stays within storage_root

        Args:
            relative_path: Relative path from storage root

        Returns:
            Resolved absolute Path object

        Raises:
            ValueError: If path is outside storage_root or contains traversal attempts
        """
        if not relative_path:
            raise ValueError("Relative path cannot be empty")

        # Check for path traversal attempts
        if ".." in relative_path or relative_path.startswith("/"):
            raise ValueError(f"Path traversal attempt detected: {relative_path}")

        # Convert to Path object and resolve
        try:
            resolved_path = (self.storage_root / relative_path).resolve()
        except (OSError, ValueError) as e:
            raise ValueError(f"Invalid path: {relative_path}") from e

        # Ensure the resolved path is within storage_root
        try:
            resolved_path.relative_to(self.storage_root)
        except ValueError as e:
            raise ValueError(f"Path outside storage root: {relative_path}") from e

        return resolved_path

    def get_file_path(self, file_id: str, relative_path: str) -> Path:
        """Get the absolute path to a stored file

        Args:
            file_id: The UUID filename
            relative_path: Relative path from storage root

        Returns:
            Absolute Path object to the file
        """
        return self._validate_and_resolve_path(relative_path)

    def file_exists(self, relative_path: str) -> bool:
        """Check if a file exists in storage

        Args:
            relative_path: Relative path from storage root

        Returns:
            True if file exists, False otherwise
        """
        try:
            file_path = self._validate_and_resolve_path(relative_path)
            return file_path.exists() and file_path.is_file()
        except ValueError:
            # Path validation failed - treat as non-existent
            return False

    def delete_file(self, relative_path: str) -> bool:
        """Delete a file from storage

        Args:
            relative_path: Relative path from storage root

        Returns:
            True if file was deleted, False if file didn't exist
        """
        try:
            file_path = self._validate_and_resolve_path(relative_path)

            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {relative_path}")
                return True
            else:
                logger.warning(
                    f"Attempted to delete non-existent file: {relative_path}"
                )
                return False

        except ValueError as e:
            logger.error(f"Path validation failed for delete {relative_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {relative_path}: {e}")
            return False

    def cleanup_old_files(
        self, retention_days: Optional[int] = None, batch_size: int = 100
    ) -> Dict[str, Any]:
        """Clean up files older than retention period using database timestamps for efficiency

        Args:
            retention_days: Number of days to retain files. If None, uses config.
            batch_size: Number of files to process in each batch

        Returns:
            Dictionary with cleanup statistics
        """
        from .file_repository import FileRepository

        if not config.file_storage.cleanup_enabled:
            logger.info("File cleanup is disabled")
            return {"enabled": False, "deleted_count": 0, "freed_bytes": 0}

        retention_days = retention_days or config.file_storage.retention_days
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        deleted_count = 0
        freed_bytes = 0
        error_count = 0

        try:
            # Use FileRepository to get old files based on database timestamps
            file_repo = FileRepository()

            # Get old files in batches
            offset = 0
            while True:
                try:
                    with file_repo.db_manager.get_connection() as conn:
                        cursor = conn.execute(
                            """
                            SELECT relative_path, file_size
                            FROM uploaded_files
                            WHERE created_at < ? AND ingestion_status IN ('completed', 'error')
                            ORDER BY created_at
                            LIMIT ? OFFSET ?
                        """,
                            (cutoff_date.isoformat(), batch_size, offset),
                        )

                        batch_files = cursor.fetchall()

                        if not batch_files:
                            break  # No more files to process

                        # Process current batch
                        for relative_path, file_size in batch_files:
                            try:
                                if self.delete_file(relative_path):
                                    deleted_count += 1
                                    freed_bytes += file_size or 0
                            except Exception as e:
                                logger.error(
                                    f"Failed to delete file {relative_path}: {e}"
                                )
                                error_count += 1

                        offset += batch_size
                        logger.info(
                            f"Processed batch of {len(batch_files)} files (total: {deleted_count} deleted)"
                        )

                except Exception as e:
                    logger.error(f"Database error during cleanup batch: {e}")
                    error_count += 1
                    break

            logger.info(
                f"Cleanup completed: deleted {deleted_count} files, freed {freed_bytes} bytes, {error_count} errors"
            )

            return {
                "enabled": True,
                "deleted_count": deleted_count,
                "freed_bytes": freed_bytes,
                "error_count": error_count,
                "cutoff_date": cutoff_date.isoformat(),
                "method": "database_timestamps",
            }

        except Exception as e:
            logger.error(f"File cleanup failed: {e}")
            return {
                "enabled": True,
                "error": str(e),
                "deleted_count": deleted_count,
                "freed_bytes": freed_bytes,
                "error_count": error_count,
                "method": "database_timestamps",
            }

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics

        Returns:
            Dictionary with storage statistics
        """
        try:
            total_files = 0
            total_bytes = 0
            file_counts_by_extension = {}

            # Walk through all files
            for file_path in self.storage_root.rglob("*"):
                if file_path.is_file():
                    total_files += 1
                    file_size = file_path.stat().st_size
                    total_bytes += file_size

                    # Count by extension
                    extension = self.get_file_extension(file_path.name)
                    file_counts_by_extension[extension] = (
                        file_counts_by_extension.get(extension, 0) + 1
                    )

            return {
                "total_files": total_files,
                "total_bytes": total_bytes,
                "total_bytes_mb": round(total_bytes / (1024 * 1024), 2),
                "file_counts_by_extension": file_counts_by_extension,
                "storage_root": str(self.storage_root),
            }

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e), "storage_root": str(self.storage_root)}


# Global file storage manager instance
file_storage_manager = FileStorageManager()


def get_file_storage_manager() -> FileStorageManager:
    """Get the global file storage manager instance"""
    return file_storage_manager
