"""Citation repository for database operations"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..auth.models import Citation


class CitationRepository:
    """Handles database operations for citations"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_citation(
        self,
        lesson_id: str,
        source_type: str,
        source_id: str,
        source_title: str,
        citation_number: int,
        page_number: Optional[int] = None,
        excerpt: Optional[str] = None,
        citation_text: str = ""
    ) -> Citation:
        """
        Save citation to database

        Args:
            lesson_id: Lesson ID this citation belongs to
            source_type: Type of source
            source_id: Source identifier
            source_title: Source title
            citation_number: Citation number in lesson
            page_number: Optional page number
            excerpt: Optional text excerpt
            citation_text: Formatted citation text

        Returns:
            Created Citation model
        """
        citation_id = str(uuid.uuid4())
        now = datetime.utcnow()

        conn = self.get_connection()
        try:
            conn.execute("""
                INSERT INTO citations (
                    id, lesson_id, source_type, source_id, source_title,
                    page_number, excerpt, citation_text, citation_number, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                citation_id, lesson_id, source_type, source_id, source_title,
                page_number, excerpt, citation_text, citation_number, now
            ))
            conn.commit()

            return self.get_citation_by_id(citation_id)

        finally:
            conn.close()

    def save_citations_batch(
        self,
        lesson_id: str,
        citations: List[dict]
    ) -> List[Citation]:
        """
        Save multiple citations in batch

        Args:
            lesson_id: Lesson ID
            citations: List of citation dictionaries

        Returns:
            List of created Citation models
        """
        conn = self.get_connection()
        try:
            citation_ids = []
            now = datetime.utcnow()

            for citation_data in citations:
                citation_id = str(uuid.uuid4())
                citation_ids.append(citation_id)

                conn.execute("""
                    INSERT INTO citations (
                        id, lesson_id, source_type, source_id, source_title,
                        page_number, excerpt, citation_text, citation_number, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    citation_id,
                    lesson_id,
                    citation_data['source_type'],
                    citation_data['source_id'],
                    citation_data['source_title'],
                    citation_data.get('page_number'),
                    citation_data.get('excerpt'),
                    citation_data['citation_text'],
                    citation_data['citation_number'],
                    now
                ))

            conn.commit()

            # Retrieve all created citations
            return [self.get_citation_by_id(cid) for cid in citation_ids]

        finally:
            conn.close()

    def get_citation_by_id(self, citation_id: str) -> Optional[Citation]:
        """Get citation by ID"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM citations WHERE id = ?",
                (citation_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_citation(row)

        finally:
            conn.close()

    def get_lesson_citations(self, lesson_id: str) -> List[Citation]:
        """
        Get all citations for a lesson

        Args:
            lesson_id: Lesson ID

        Returns:
            List of citations ordered by citation number
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM citations
                WHERE lesson_id = ?
                ORDER BY citation_number ASC
            """, (lesson_id,))

            rows = cursor.fetchall()
            return [self._row_to_citation(row) for row in rows]

        finally:
            conn.close()

    def get_citations_by_source(
        self,
        source_type: str,
        source_id: str
    ) -> List[Citation]:
        """
        Get all citations for a specific source

        Args:
            source_type: Type of source
            source_id: Source identifier

        Returns:
            List of citations
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM citations
                WHERE source_type = ? AND source_id = ?
                ORDER BY created_at DESC
            """, (source_type, source_id))

            rows = cursor.fetchall()
            return [self._row_to_citation(row) for row in rows]

        finally:
            conn.close()

    def delete_lesson_citations(self, lesson_id: str) -> int:
        """
        Delete all citations for a lesson

        Args:
            lesson_id: Lesson ID

        Returns:
            Number of citations deleted
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM citations WHERE lesson_id = ?",
                (lesson_id,)
            )
            conn.commit()
            return cursor.rowcount

        finally:
            conn.close()

    def get_citation_count(self, lesson_id: str) -> int:
        """Get count of citations for a lesson"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM citations WHERE lesson_id = ?",
                (lesson_id,)
            )
            row = cursor.fetchone()
            return row['count']

        finally:
            conn.close()

    def _row_to_citation(self, row: sqlite3.Row) -> Citation:
        """Convert database row to Citation model"""
        return Citation(
            id=row['id'],
            lesson_id=row['lesson_id'],
            source_type=row['source_type'],
            source_id=row['source_id'],
            source_title=row['source_title'],
            page_number=row['page_number'],
            excerpt=row['excerpt'],
            citation_text=row['citation_text'],
            citation_number=row['citation_number'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
