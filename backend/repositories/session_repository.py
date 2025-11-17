"""Session repository helpers"""

import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List, Union

from backend.repositories.database import DatabaseManager
from backend.auth import Session


class SessionRepository:
    """Handles lesson generation session rows"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager()

    def create_session(
        self,
        user_id: str,
        grade_level: Optional[str] = None,
        strand_code: Optional[str] = None,
        standard_id: Optional[
            str
        ] = None,  # Can be comma-separated for multiple standards
        additional_context: Optional[str] = None,
        lesson_duration: Optional[str] = None,
        class_size: Optional[int] = None,
        selected_objectives: Optional[
            str
        ] = None,  # Can be comma-separated for multiple objectives
        additional_standards: Optional[str] = None,
        additional_objectives: Optional[str] = None,
        selected_model: Optional[str] = None,
    ) -> Session:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                """
                INSERT INTO sessions (
                    id, user_id, grade_level, strand_code,
                    selected_standards, selected_objectives,
                    additional_standards, additional_objectives,
                    additional_context, lesson_duration, class_size,
                    selected_model, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    user_id,
                    grade_level,
                    strand_code,
                    standard_id,
                    selected_objectives,
                    additional_standards,
                    additional_objectives,
                    additional_context,
                    lesson_duration,
                    class_size,
                    selected_model,
                    now,
                    now,
                ),
            )
            conn.commit()
            session = self.get_session(session_id)
            if not session:
                raise RuntimeError(f"Failed to create session {session_id}")
            return session
        finally:
            conn.close()

    def list_sessions(self, user_id: str, limit: int = 20) -> List[Session]:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT * FROM sessions
                WHERE user_id = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            return [self._row_to_session(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_session(self, session_id: str) -> Optional[Session]:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_session(row)
        finally:
            conn.close()

    def update_session(
        self,
        session_id: str,
        grade_level: Optional[str] = None,
        strand_code: Optional[str] = None,
        standard_id: Optional[str] = None,
        additional_context: Optional[str] = None,
        lesson_duration: Optional[str] = None,
        class_size: Optional[int] = None,
        selected_objective: Optional[str] = None,
        additional_standards: Optional[str] = None,
        additional_objectives: Optional[str] = None,
        selected_model: Optional[str] = None,
    ) -> Optional[Session]:
        assignments = []
        params: List[Optional[object]] = []
        if grade_level is not None:
            assignments.append("grade_level = ?")
            params.append(grade_level)
        if strand_code is not None:
            assignments.append("strand_code = ?")
            params.append(strand_code)
        if standard_id is not None:
            assignments.append("selected_standards = ?")
            params.append(standard_id)
        if additional_context is not None:
            assignments.append("additional_context = ?")
            params.append(additional_context)
        if lesson_duration is not None:
            assignments.append("lesson_duration = ?")
            params.append(lesson_duration)
        if class_size is not None:
            assignments.append("class_size = ?")
            params.append(class_size)
        if selected_objective is not None:
            assignments.append("selected_objectives = ?")
            params.append(selected_objective)
        if additional_standards is not None:
            assignments.append("additional_standards = ?")
            params.append(additional_standards)
        if additional_objectives is not None:
            assignments.append("additional_objectives = ?")
            params.append(additional_objectives)
        if selected_model is not None:
            assignments.append("selected_model = ?")
            params.append(selected_model)

        if not assignments:
            return self.get_session(session_id)

        assignments.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(session_id)

        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                f"UPDATE sessions SET {', '.join(assignments)} WHERE id = ?",
                tuple(params),
            )
            conn.commit()
            return self.get_session(session_id)
        finally:
            conn.close()

    def touch_session(self, session_id: str) -> Optional[Session]:
        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), session_id),
            )
            conn.commit()
            return self.get_session(session_id)
        finally:
            conn.close()

    def save_agent_state(
        self,
        session_id: str,
        agent_state: str,
        conversation_history: str,
        current_state: str,
    ) -> Optional[Session]:
        """Save agent state and conversation history to session"""
        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                """
                UPDATE sessions 
                SET agent_state = ?, 
                    conversation_history = ?, 
                    current_state = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    agent_state,
                    conversation_history,
                    current_state,
                    datetime.utcnow().isoformat(),
                    session_id,
                ),
            )
            conn.commit()
            return self.get_session(session_id)
        finally:
            conn.close()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID. Returns True if deleted, False if not found."""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_all_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user. Returns the number of sessions deleted."""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def _row_to_session(self, row: sqlite3.Row) -> Session:
        # Helper to safely get optional columns
        def safe_get(row, key: str, default=None):
            try:
                return row[key]
            except (KeyError, IndexError):
                return default

        return Session(
            id=row["id"],
            user_id=row["user_id"],
            grade_level=row["grade_level"],
            strand_code=row["strand_code"],
            selected_standards=row["selected_standards"],
            selected_objectives=row["selected_objectives"],
            additional_standards=safe_get(row, "additional_standards"),
            additional_objectives=safe_get(row, "additional_objectives"),
            additional_context=row["additional_context"],
            lesson_duration=safe_get(row, "lesson_duration"),
            class_size=safe_get(row, "class_size"),
            agent_state=safe_get(row, "agent_state"),
            conversation_history=safe_get(row, "conversation_history"),
            current_state=safe_get(row, "current_state", "welcome"),
            created_at=datetime.fromisoformat(row["created_at"])
            if row["created_at"]
            else None,
            updated_at=datetime.fromisoformat(row["updated_at"])
            if row["updated_at"]
            else None,
        )

    # Field normalization helpers for REST standardization
    def parse_selected_standards_list(self, session: Session) -> List[str]:
        """Convert comma-separated standards string to array"""
        if not session.selected_standards:
            return []

        # Split by comma and filter out empty strings
        standards = [
            standard.strip()
            for standard in session.selected_standards.split(',')
            if standard.strip()
        ]

        return standards

    def parse_selected_objectives_list(self, session: Session) -> List[str]:
        """Convert comma-separated objectives string to array"""
        if not session.selected_objectives:
            return []

        # Split by comma and filter out empty strings
        objectives = [
            objective.strip()
            for objective in session.selected_objectives.split(',')
            if objective.strip()
        ]

        return objectives

    def normalize_standards_for_response(self, session: Session, standards_repo) -> List[dict]:
        """Convert session standards to normalized array format for API responses"""
        standards_list = self.parse_selected_standards_list(session)
        normalized_standards = []

        # Import the grade formatting utility
        from backend.utils.standards import format_grade_display

        for standard_id in standards_list:
            standard = standards_repo.get_standard_by_id(standard_id)
            if standard:
                # Convert database grade format to frontend display format
                # Database stores: "0", "1", "2", "3", etc.
                # Frontend expects: "Kindergarten", "Grade 1", "Grade 2", "Grade 3", etc.
                grade_display = format_grade_display(standard.grade_level) or "Unknown Grade"

                # Get objectives for this standard
                try:
                    objectives = standards_repo.get_objectives_for_standard(standard.standard_id)
                    # Include objective codes in the format "code - text" to match standards display
                    learning_objectives = [
                        f"{obj.objective_id} - {obj.objective_text}" for obj in objectives
                    ][:3]
                except (AttributeError, TypeError):
                    # Fallback if repo method doesn't exist or returns unexpected format
                    learning_objectives = []

                normalized_standards.append({
                    "id": standard.standard_id,
                    "code": standard.standard_id,
                    "grade": grade_display,
                    "strandCode": standard.strand_code,
                    "strandName": standard.strand_name,
                    "title": standard.standard_text,
                    "description": standard.standard_text,
                    "objectives": len(objectives) if hasattr(objectives, '__len__') else 0,
                    "learningObjectives": learning_objectives,
                })

        return normalized_standards

    def normalize_objectives_for_response(self, session: Session) -> List[str]:
        """Convert session objectives to normalized array format for API responses"""
        return self.parse_selected_objectives_list(session)

    def convert_standards_list_to_string(self, standards_list: List[str]) -> Optional[str]:
        """Convert standards array back to comma-separated string for storage"""
        if not standards_list:
            return None
        return ",".join(standards_list)

    def convert_objectives_list_to_string(self, objectives_list: List[str]) -> Optional[str]:
        """Convert objectives array back to comma-separated string for storage"""
        if not objectives_list:
            return None
        return ",".join(objectives_list)
