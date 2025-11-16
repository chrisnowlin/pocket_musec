"""Repository for PresentationPreview persistence.

This module provides a lightweight repository that stores and retrieves
`PresentationPreview` objects in the SQLite database used by the
application.  The data is serialized to JSON using a custom ``DateTimeEncoder``
so that ``datetime`` fields are stored in ISO‑8601 format.

The repository follows the same pattern as the other repository classes in
the project (e.g. ``presentation_repository``) and uses ``DatabaseManager``
to obtain a connection.
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Optional

from backend.models.preview_schema import PresentationPreview
from .database import DatabaseManager


class DateTimeEncoder(json.JSONEncoder):
    """Encode ``datetime`` objects as ISO‑8601 strings for JSON storage."""

    def default(self, obj):  # pragma: no cover
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class PreviewRepository:
    """CRUD operations for :class:`PresentationPreview`.

    The underlying SQLite table ``presentation_previews`` is defined in the
    migration scripts.  Its schema roughly matches the fields of
    ``PresentationPreview`` with the ``slides`` column stored as a JSON string.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager()

    # ---------------------------------------------------------------------
    # Create
    # ---------------------------------------------------------------------
    def add_preview(self, preview: PresentationPreview) -> None:
        """Insert a new preview into the database.

        The ``slides`` list is serialized to JSON using ``DateTimeEncoder``.
        """
        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                """
                INSERT INTO presentation_previews (
                    presentation_id,
                    generated_at,
                    slides,
                    total_estimated_duration_seconds,
                    style_id
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    preview.presentation_id,
                    preview.generated_at.isoformat(),
                    json.dumps([s.model_dump() for s in preview.slides], cls=DateTimeEncoder),
                    preview.total_estimated_duration_seconds,
                    preview.style_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    # ---------------------------------------------------------------------
    # Read
    # ---------------------------------------------------------------------
    def get_preview(self, presentation_id: str) -> Optional[PresentationPreview]:
        """Retrieve a preview by its ``presentation_id``.

        Returns ``None`` if the preview does not exist.
        """
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM presentation_previews WHERE presentation_id = ?",
                (presentation_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_preview(row)
        finally:
            conn.close()

    def list_previews(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> List[PresentationPreview]:
        """List previews belonging to ``user_id`` with pagination.

        The ``presentation_previews`` table does not contain a ``user_id`` column
        directly; it is joined to the ``presentations`` table (which has a
        ``user_id`` foreign key) to filter results.
        """
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT pp.* FROM presentation_previews pp
                JOIN presentations p ON pp.presentation_id = p.id
                WHERE p.user_id = ?
                ORDER BY pp.generated_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset),
            )
            rows = cursor.fetchall()
            return [self._row_to_preview(r) for r in rows]
        finally:
            conn.close()

    # ---------------------------------------------------------------------
    # Delete
    # ---------------------------------------------------------------------
    def delete_preview(self, presentation_id: str) -> bool:
        """Delete a preview record.

        Returns ``True`` if a row was deleted, ``False`` otherwise.
        """
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM presentation_previews WHERE presentation_id = ?",
                (presentation_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # ---------------------------------------------------------------------
    # Helper
    # ---------------------------------------------------------------------
    def _row_to_preview(self, row: sqlite3.Row) -> PresentationPreview:
        """Convert a DB row into a :class:`PresentationPreview` instance."""
        slides_data = json.loads(row["slides"]) if row["slides"] else []
        # ``SlidePreview`` is defined in ``preview_schema``; we can import it lazily.
        from backend.models.preview_schema import SlidePreview

        slides = [SlidePreview(**sd) for sd in slides_data]
        generated_at = datetime.fromisoformat(row["generated_at"])
        return PresentationPreview(
            presentation_id=row["presentation_id"],
            generated_at=generated_at,
            slides=slides,
            total_estimated_duration_seconds=row["total_estimated_duration_seconds"],
            style_id=row["style_id"],
        )
