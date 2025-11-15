"""Streaming image upload handler with efficient quota management"""

import os
import hashlib
import tempfile
from pathlib import Path
from typing import Optional, Tuple, BinaryIO
from fastapi import UploadFile, HTTPException, status
import logging

from backend.services.user_storage_manager import get_storage_manager
from backend.config import config

logger = logging.getLogger(__name__)


class StreamingImageHandler:
    """Handles image uploads with streaming and efficient quota tracking"""

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize handler with storage path"""
        self.storage_path = Path(storage_path or config.image_processing.storage_path)
        self.storage_manager = get_storage_manager()
        self.max_file_size = config.image_processing.max_file_size
        self.allowed_types = config.image_processing.allowed_formats

    async def save_uploaded_file(
        self, file: UploadFile, user_id: str
    ) -> Tuple[str, int]:
        """
        Save uploaded file with streaming and quota checking

        Args:
            file: UploadFile from FastAPI
            user_id: User ID for quota tracking

        Returns:
            Tuple of (file_path, file_size)

        Raises:
            HTTPException: If file invalid, too large, or quota exceeded
        """
        # Validate file type
        if not self._is_allowed_type(file.filename or "", file.content_type or ""):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(self.allowed_types)}",
            )

        # Create user directory
        user_dir = self.storage_path / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_id = self._generate_file_id()
        file_extension = Path(file.filename or "").suffix or ".jpg"
        safe_filename = f"{file_id}{file_extension}"
        file_path = user_dir / safe_filename

        # Stream file to temporary location first
        temp_file_path, file_size = await self._stream_to_temp(file)

        try:
            # Check quota before final save
            if not self.storage_manager.can_add_file(user_id, file_size):
                os.unlink(temp_file_path)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File would exceed user quota. Available: {self.storage_manager.get_user_usage(user_id).available_mb:.1f}MB",
                )

            # Move to final location
            os.rename(temp_file_path, file_path)

            # Update storage tracking
            self.storage_manager.add_file(user_id, file_size)

            logger.info(
                f"Saved file {safe_filename} for user {user_id} ({file_size} bytes)"
            )
            return str(file_path), file_size

        except Exception as e:
            # Clean up temp file if something went wrong
            if temp_file_path.exists():
                os.unlink(temp_file_path)
            raise e

    async def _stream_to_temp(self, file: UploadFile) -> Tuple[str, int]:
        """
        Stream upload to temporary file with size limit

        Args:
            file: UploadFile to stream

        Returns:
            Tuple of (temp_file_path, file_size)

        Raises:
            HTTPException: If file too large
        """
        # Create temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix=".tmp")

        try:
            file_size = 0
            chunk_size = 64 * 1024  # 64KB chunks

            with os.fdopen(temp_fd, "wb") as temp_file:
                while chunk := await file.read(chunk_size):
                    file_size += len(chunk)

                    # Check size limit during streaming
                    if file_size > self.max_file_size:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File too large. Maximum: {self.max_file_size / (1024 * 1024):.1f}MB",
                        )

                    temp_file.write(chunk)

            return temp_path, file_size

        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise e

    def _is_allowed_type(self, filename: str, content_type: str) -> bool:
        """Check if file type is allowed"""
        # Check by content type
        allowed_content_types = {
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/tiff",
            "image/tif",
        }

        if content_type.lower() in allowed_content_types:
            return True

        # Check by file extension
        file_ext = Path(filename).suffix.lower()
        return file_ext in self.allowed_types

    def _generate_file_id(self) -> str:
        """Generate unique file ID"""
        import uuid

        return str(uuid.uuid4())

    def delete_file(self, file_path: str, user_id: str) -> bool:
        """
        Delete file and update quota tracking

        Args:
            file_path: Path to file to delete
            user_id: User ID for quota tracking

        Returns:
            True if file deleted successfully
        """
        try:
            path = Path(file_path)
            if path.exists():
                file_size = path.stat().st_size
                path.unlink()

                # Update storage tracking
                self.storage_manager.remove_file(user_id, file_size)

                logger.info(
                    f"Deleted file {file_path} for user {user_id} ({file_size} bytes)"
                )
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    def get_user_quota_info(self, user_id: str) -> dict:
        """Get quota information for user"""
        return self.storage_manager.get_quota_info(user_id)

    def get_file_info(self, file_path: str) -> Optional[dict]:
        """Get information about a file"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            stat = path.stat()
            return {
                "path": str(path),
                "size_bytes": stat.st_size,
                "size_mb": stat.st_size / (1024 * 1024),
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
                "filename": path.name,
                "extension": path.suffix,
            }

        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return None

    def cleanup_temp_files(self) -> int:
        """Clean up any temporary files left behind"""
        cleaned_count = 0

        try:
            for temp_file in self.storage_path.rglob("*.tmp"):
                try:
                    temp_file.unlink()
                    cleaned_count += 1
                except OSError:
                    pass

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} temporary files")

        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")

        return cleaned_count
