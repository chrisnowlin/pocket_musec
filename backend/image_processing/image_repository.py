"""Image repository for database operations"""

import sqlite3
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from ..auth import Image as ImageModel


class ImageRepository:
    """Handles database operations for images"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_image(
        self,
        user_id: str,
        filename: str,
        file_path: str,
        file_size: int,
        mime_type: str,
        extracted_text: Optional[str] = None,
        vision_summary: Optional[str] = None,
        ocr_confidence: Optional[float] = None,
        metadata: Optional[dict] = None,
    ) -> ImageModel:
        """
        Save image metadata to database

        Args:
            user_id: User ID
            filename: Original filename
            file_path: Stored file path
            file_size: File size in bytes
            mime_type: MIME type
            extracted_text: OCR extracted text
            vision_summary: Vision analysis summary
            ocr_confidence: OCR confidence score (0-1)
            metadata: Additional metadata as dict

        Returns:
            Created ImageModel
        """
        image_id = str(uuid.uuid4())
        now = datetime.utcnow()

        metadata_json = json.dumps(metadata) if metadata else None

        conn = self.get_connection()
        try:
            conn.execute(
                """
                INSERT INTO images (
                    id, user_id, filename, file_path, file_size, mime_type,
                    extracted_text, vision_summary, ocr_confidence, metadata,
                    created_at, last_accessed
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    image_id,
                    user_id,
                    filename,
                    file_path,
                    file_size,
                    mime_type,
                    extracted_text,
                    vision_summary,
                    ocr_confidence,
                    metadata_json,
                    now,
                    now,
                ),
            )
            conn.commit()

            return self.get_image_by_id(image_id)

        finally:
            conn.close()

    def get_image_by_id(self, image_id: str) -> Optional[ImageModel]:
        """Get image by ID"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT * FROM images WHERE id = ?", (image_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_image(row)

        finally:
            conn.close()

    def get_user_images(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[ImageModel]:
        """
        Get images for a user

        Args:
            user_id: User ID
            limit: Maximum number of images
            offset: Offset for pagination

        Returns:
            List of ImageModel objects
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT * FROM images
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """,
                (user_id, limit, offset),
            )

            rows = cursor.fetchall()
            return [self._row_to_image(row) for row in rows]

        finally:
            conn.close()

    def search_images(
        self, user_id: str, query: str, limit: int = 20
    ) -> List[ImageModel]:
        """
        Search images by text content

        Args:
            user_id: User ID
            query: Search query
            limit: Maximum results

        Returns:
            List of matching images
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT * FROM images
                WHERE user_id = ?
                AND (
                    extracted_text LIKE ?
                    OR vision_summary LIKE ?
                    OR filename LIKE ?
                )
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (user_id, f"%{query}%", f"%{query}%", f"%{query}%", limit),
            )

            rows = cursor.fetchall()
            return [self._row_to_image(row) for row in rows]

        finally:
            conn.close()

    def update_last_accessed(self, image_id: str) -> None:
        """Update last accessed timestamp"""
        now = datetime.utcnow()
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE images SET last_accessed = ? WHERE id = ?", (now, image_id)
            )
            conn.commit()
        finally:
            conn.close()

    def delete_image(self, image_id: str) -> bool:
        """Delete image from database"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("DELETE FROM images WHERE id = ?", (image_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_user_storage_usage(self, user_id: str) -> int:
        """Get total storage used by user in bytes"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT SUM(file_size) as total FROM images WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            return row["total"] if row["total"] else 0
        finally:
            conn.close()

    def get_image_count(self, user_id: str) -> int:
        """Get count of images for user"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM images WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()
            return row["count"]
        finally:
            conn.close()

    def get_oldest_images(self, limit: int = 10) -> List[ImageModel]:
        """Get oldest images by last access time (for LRU eviction)"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT * FROM images
                ORDER BY last_accessed ASC
                LIMIT ?
            """,
                (limit,),
            )

            rows = cursor.fetchall()
            return [self._row_to_image(row) for row in rows]

        finally:
            conn.close()

    def _row_to_image(self, row: sqlite3.Row) -> ImageModel:
        """Convert database row to ImageModel"""
        metadata = json.loads(row["metadata"]) if row["metadata"] else None

        return ImageModel(
            id=row["id"],
            user_id=row["user_id"],
            filename=row["filename"],
            file_path=row["file_path"],
            file_size=row["file_size"],
            mime_type=row["mime_type"],
            extracted_text=row["extracted_text"],
            vision_summary=row["vision_summary"],
            ocr_confidence=row["ocr_confidence"],
            metadata=json.dumps(metadata) if metadata else None,
            created_at=datetime.fromisoformat(row["created_at"])
            if row["created_at"]
            else None,
            last_accessed=datetime.fromisoformat(row["last_accessed"])
            if row["last_accessed"]
            else None,
        )
