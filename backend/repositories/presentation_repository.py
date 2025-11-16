"""Presentation persistence helpers"""

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from .database import DatabaseManager
from backend.lessons.presentation_schema import (
    PresentationDocument,
    PresentationStatus,
    PresentationSlide,
    PresentationExport,
    build_presentation_document,
)


class PresentationRepository:
    """Handles CRUD for generated presentations"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager()

    def create_presentation(
        self,
        lesson_id: str,
        lesson_revision: int,
        slides: List[PresentationSlide],
        style: str = "default",
    ) -> PresentationDocument:
        """Create a new presentation record"""
        presentation = build_presentation_document(
            lesson_id=lesson_id,
            lesson_revision=lesson_revision,
            slides=slides,
            style=style,
        )

        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                """
                INSERT INTO presentations (
                    id, lesson_id, lesson_revision, version, status, style, 
                    slides, export_assets, error_code, error_message, 
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    presentation.id,
                    presentation.lesson_id,
                    presentation.lesson_revision,
                    presentation.version,
                    presentation.status.value,
                    presentation.style,
                    json.dumps([slide.model_dump() for slide in presentation.slides]),
                    json.dumps(
                        [asset.model_dump() for asset in presentation.export_assets]
                    ),
                    presentation.error_code,
                    presentation.error_message,
                    presentation.created_at.isoformat(),
                    presentation.updated_at.isoformat(),
                ),
            )
            conn.commit()
            return self.get_presentation(presentation.id)
        finally:
            conn.close()

    def get_presentation(self, presentation_id: str) -> Optional[PresentationDocument]:
        """Get a presentation by ID"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM presentations WHERE id = ?", (presentation_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_presentation(row)
        finally:
            conn.close()

    def latest_by_lesson(self, lesson_id: str) -> Optional[PresentationDocument]:
        """Get the latest non-stale presentation for a lesson"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT * FROM presentations 
                WHERE lesson_id = ? AND status != 'stale'
                ORDER BY lesson_revision DESC, updated_at DESC 
                LIMIT 1
                """,
                (lesson_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_presentation(row)
        finally:
            conn.close()

    def list_presentations_for_lesson(
        self,
        lesson_id: str,
        include_stale: bool = False,
        limit: int = 20,
    ) -> List[PresentationDocument]:
        """List presentations for a lesson"""
        conn = self.db_manager.get_connection()
        try:
            if include_stale:
                cursor = conn.execute(
                    """
                    SELECT * FROM presentations 
                    WHERE lesson_id = ? 
                    ORDER BY lesson_revision DESC, updated_at DESC 
                    LIMIT ?
                    """,
                    (lesson_id, limit),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM presentations 
                    WHERE lesson_id = ? AND status != 'stale'
                    ORDER BY lesson_revision DESC, updated_at DESC 
                    LIMIT ?
                    """,
                    (lesson_id, limit),
                )
            return [self._row_to_presentation(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update_presentation_status(
        self,
        presentation_id: str,
        status: PresentationStatus,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[PresentationDocument]:
        """Update presentation status"""
        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                """
                UPDATE presentations 
                SET status = ?, error_code = ?, error_message = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    status.value,
                    error_code,
                    error_message,
                    datetime.utcnow().isoformat(),
                    presentation_id,
                ),
            )
            conn.commit()
            return self.get_presentation(presentation_id)
        finally:
            conn.close()

    def update_presentation_slides(
        self,
        presentation_id: str,
        slides: List[PresentationSlide],
    ) -> Optional[PresentationDocument]:
        """Update presentation slides and mark as complete"""
        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                """
                UPDATE presentations 
                SET slides = ?, status = 'complete', updated_at = ?
                WHERE id = ?
                """,
                (
                    json.dumps([slide.model_dump() for slide in slides]),
                    datetime.utcnow().isoformat(),
                    presentation_id,
                ),
            )
            conn.commit()
            return self.get_presentation(presentation_id)
        finally:
            conn.close()

    def mark_stale_for_lesson(self, lesson_id: str, current_revision: int) -> int:
        """Mark all presentations for a lesson as stale except the current revision"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                """
                UPDATE presentations 
                SET status = 'stale', updated_at = ?
                WHERE lesson_id = ? AND lesson_revision < ?
                """,
                (
                    datetime.utcnow().isoformat(),
                    lesson_id,
                    current_revision,
                ),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def add_export_asset(
        self,
        presentation_id: str,
        export_asset: PresentationExport,
    ) -> Optional[PresentationDocument]:
        """Add an export asset to a presentation"""
        presentation = self.get_presentation(presentation_id)
        if not presentation:
            return None

        presentation.export_assets.append(export_asset)

        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                """
                UPDATE presentations 
                SET export_assets = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    json.dumps(
                        [asset.model_dump() for asset in presentation.export_assets]
                    ),
                    datetime.utcnow().isoformat(),
                    presentation_id,
                ),
            )
            conn.commit()
            return self.get_presentation(presentation_id)
        finally:
            conn.close()

    def delete_presentation(self, presentation_id: str) -> bool:
        """Delete a presentation"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM presentations WHERE id = ?", (presentation_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def _row_to_presentation(self, row: sqlite3.Row) -> PresentationDocument:
        """Convert database row to PresentationDocument"""
        slides_data = json.loads(row["slides"]) if row["slides"] else []
        slides = [PresentationSlide(**slide_data) for slide_data in slides_data]

        exports_data = json.loads(row["export_assets"]) if row["export_assets"] else []
        exports = [PresentationExport(**export_data) for export_data in exports_data]

        return PresentationDocument(
            id=row["id"],
            lesson_id=row["lesson_id"],
            lesson_revision=row["lesson_revision"],
            version=row["version"],
            status=PresentationStatus(row["status"]),
            style=row["style"],
            slides=slides,
            export_assets=exports,
            error_code=row["error_code"],
            error_message=row["error_message"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
