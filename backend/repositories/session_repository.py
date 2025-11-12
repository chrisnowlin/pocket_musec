"""Session repository helpers"""

import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List

from .database import DatabaseManager
from ..auth import Session


class SessionRepository:
    """Handles lesson generation session rows"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager()

    def create_session(
        self,
        user_id: str,
        grade_level: Optional[str] = None,
        strand_code: Optional[str] = None,
        standard_id: Optional[str] = None,
        additional_context: Optional[str] = None,
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
                    additional_context, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    user_id,
                    grade_level,
                    strand_code,
                    standard_id,
                    None,
                    additional_context,
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
    ) -> Optional[Session]:
        assignments = []
        params: List[Optional[str]] = []
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
            additional_context=row["additional_context"],
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
