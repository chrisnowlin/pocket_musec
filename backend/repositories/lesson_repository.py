"""Lesson persistence helpers"""

import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List

from .database import DatabaseManager
from backend.auth import Lesson


class LessonRepository:
    """Handles CRUD for generated lessons"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager()

    def create_lesson(
        self,
        session_id: str,
        user_id: str,
        title: str,
        content: str,
        metadata: Optional[str] = None,
        processing_mode: str = "cloud",
        is_draft: bool = False,
    ) -> Lesson:
        lesson_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                """
                INSERT INTO lessons (id, session_id, user_id, title, content, metadata, processing_mode, is_draft, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lesson_id,
                    session_id,
                    user_id,
                    title,
                    content,
                    metadata,
                    processing_mode,
                    1 if is_draft else 0,
                    now,
                    now,
                ),
            )
            conn.commit()
            return self.get_lesson(lesson_id)
        finally:
            conn.close()

    def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_lesson(row)
        finally:
            conn.close()

    def list_lessons_for_user(
        self,
        user_id: str,
        limit: int = 20,
        is_draft: Optional[bool] = None,
        session_id: Optional[str] = None,
    ) -> List[Lesson]:
        conn = self.db_manager.get_connection()
        try:
            base_query = [
                "SELECT * FROM lessons",
                "WHERE user_id = ?",
            ]
            params: List[object] = [user_id]

            if is_draft is not None:
                base_query.append("AND is_draft = ?")
                params.append(1 if is_draft else 0)

            if session_id:
                base_query.append("AND session_id = ?")
                params.append(session_id)

            base_query.append("ORDER BY updated_at DESC LIMIT ?")
            params.append(limit)

            cursor = conn.execute(" ".join(base_query), tuple(params))
            return [self._row_to_lesson(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def list_lessons_for_session(
        self, session_id: str, limit: int = 20
    ) -> List[Lesson]:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT * FROM lessons WHERE session_id = ? ORDER BY created_at DESC LIMIT ?
                """,
                (session_id, limit),
            )
            return [self._row_to_lesson(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def count_lessons_for_user(
        self, user_id: str, is_draft: Optional[bool] = None
    ) -> int:
        """Count lessons for a user, optionally filtering drafts."""

        conn = self.db_manager.get_connection()
        try:
            query = "SELECT COUNT(*) as count FROM lessons WHERE user_id = ?"
            params: List[object] = [user_id]

            if is_draft is not None:
                query += " AND is_draft = ?"
                params.append(1 if is_draft else 0)

            cursor = conn.execute(query, tuple(params))
            row = cursor.fetchone()
            return int(row["count"] if row else 0)
        finally:
            conn.close()

    def update_lesson(
        self,
        lesson_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[str] = None,
        is_draft: Optional[bool] = None,
    ) -> Optional[Lesson]:
        assignments = []
        params: List[Optional[str]] = []
        if title is not None:
            assignments.append("title = ?")
            params.append(title)
        if content is not None:
            assignments.append("content = ?")
            params.append(content)
        if metadata is not None:
            assignments.append("metadata = ?")
            params.append(metadata)
        if is_draft is not None:
            assignments.append("is_draft = ?")
            params.append(1 if is_draft else 0)

        if not assignments:
            return self.get_lesson(lesson_id)

        assignments.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(lesson_id)

        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                f"UPDATE lessons SET {', '.join(assignments)} WHERE id = ?",
                tuple(params),
            )
            conn.commit()
            return self.get_lesson(lesson_id)
        finally:
            conn.close()

    def promote_lesson(self, lesson_id: str) -> Optional[Lesson]:
        """Promote a draft lesson to a permanent lesson by toggling is_draft=False"""
        return self.update_lesson(lesson_id, is_draft=False)

    def demote_lesson(self, lesson_id: str) -> Optional[Lesson]:
        """Demote a permanent lesson to a draft by toggling is_draft=True"""
        return self.update_lesson(lesson_id, is_draft=True)

    def delete_lesson(self, lesson_id: str) -> bool:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def _row_to_lesson(self, row: sqlite3.Row) -> Lesson:
        return Lesson(
            id=row["id"],
            session_id=row["session_id"],
            user_id=row["user_id"],
            title=row["title"],
            content=row["content"],
            metadata=row["metadata"],
            processing_mode=row["processing_mode"],
            is_draft=bool(row["is_draft"]),
            created_at=datetime.fromisoformat(row["created_at"])
            if row["created_at"]
            else None,
            updated_at=datetime.fromisoformat(row["updated_at"])
            if row["updated_at"]
            else None,
        )

    # Field normalization helpers for REST standardization
    def parse_metadata(self, lesson: Lesson) -> dict:
        """Parse lesson metadata JSON safely"""
        import json
        if not lesson.metadata:
            return {}

        try:
            return json.loads(lesson.metadata)
        except (json.JSONDecodeError, TypeError):
            return {}

    def normalize_lesson_for_response(self, lesson, session_repo=None) -> dict:
        """Convert lesson database model to normalized response format"""
        metadata = self.parse_metadata(lesson)

        # Get session information for fallbacks
        session = None
        if session_repo and lesson.session_id:
            session = session_repo.get_session(lesson.session_id)

        # Normalize dates to ISO format strings
        created_at_iso = lesson.created_at.isoformat() if lesson.created_at else None
        updated_at_iso = lesson.updated_at.isoformat() if lesson.updated_at else None

        # Extract and normalize session-related fields
        raw_grade = metadata.get("grade_level") or (session.grade_level if session else None)
        strand = metadata.get("strand_code") or (session.strand_code if session else None)
        standard = metadata.get("standard_id")

        # Format the grade for frontend display
        from backend.utils.standards import format_grade_display
        grade = format_grade_display(raw_grade) or "Unknown Grade"

        # Handle standards array normalization if present in metadata
        selected_standards = None
        if "selected_standards" in metadata:
            # Could be string or array in metadata
            standards_data = metadata["selected_standards"]
            if isinstance(standards_data, str):
                # Parse comma-separated string
                selected_standards = [
                    s.strip() for s in standards_data.split(',') if s.strip()
                ]
            elif isinstance(standards_data, list):
                selected_standards = standards_data

        # Handle objectives array normalization if present in metadata
        selected_objectives = None
        if "selected_objectives" in metadata:
            # Could be string or array in metadata
            objectives_data = metadata["selected_objectives"]
            if isinstance(objectives_data, str):
                # Parse comma-separated string
                selected_objectives = [
                    o.strip() for o in objectives_data.split(',') if o.strip()
                ]
            elif isinstance(objectives_data, list):
                selected_objectives = objectives_data

        return {
            "id": lesson.id,
            "title": lesson.title,
            "content": lesson.content,
            "metadata": metadata,
            "grade": grade,
            "strand": strand,
            "standard": standard,
            "selectedStandards": selected_standards,
            "selectedObjectives": selected_objectives,
            "createdAt": created_at_iso,
            "updatedAt": updated_at_iso,
            "processingMode": lesson.processing_mode,
            "isDraft": lesson.is_draft,
            "sessionId": lesson.session_id,
            "userId": lesson.user_id,
        }
