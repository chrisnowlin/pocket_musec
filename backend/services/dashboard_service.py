"""Workspace Dashboard Service

Aggregates workspace data for efficient frontend hydration.
"""

import json
from datetime import datetime
from typing import List, Optional, Set

from backend.repositories.session_repository import SessionRepository
from backend.repositories.lesson_repository import LessonRepository
from backend.repositories.database import DatabaseManager
from backend.api.models import (
    WorkspaceDashboardResponse,
    DashboardDraftSection,
    DashboardPresentationSummary,
    DashboardStats,
    SessionResponse,
    DraftResponse,
)


class DashboardService:
    """Orchestrates repository calls to build workspace dashboard"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager()
        self.session_repo = SessionRepository(self.db_manager)
        self.lesson_repo = LessonRepository(self.db_manager)

    def get_workspace_dashboard(
        self,
        user_id: str,
        include_sections: Optional[Set[str]] = None,
        session_limit: int = 10,
        draft_limit: int = 5,
    ) -> WorkspaceDashboardResponse:
        """
        Get consolidated workspace dashboard data.

        Args:
            user_id: User ID to fetch data for
            include_sections: Optional set of sections to include (sessions, drafts, presentations, stats)
            session_limit: Maximum number of sessions to return
            draft_limit: Maximum number of drafts to return

        Returns:
            WorkspaceDashboardResponse with requested sections
        """
        # Default to all sections if not specified
        if include_sections is None:
            include_sections = {"sessions", "drafts", "presentations", "stats"}

        generated_at = datetime.utcnow().isoformat()
        response = WorkspaceDashboardResponse(
            generated_at=generated_at,
            includes=list(include_sections),
        )

        # Fetch sessions
        if "sessions" in include_sections:
            response.sessions = self._get_recent_sessions(user_id, session_limit)

        # Fetch drafts
        if "drafts" in include_sections:
            response.drafts = self._get_draft_section(user_id, draft_limit)

        # Fetch presentations
        if "presentations" in include_sections:
            response.presentations = self._get_presentation_summaries(user_id)

        # Calculate stats
        if "stats" in include_sections:
            response.stats = self._calculate_stats(user_id)

        return response

    def _get_recent_sessions(self, user_id: str, limit: int) -> List[SessionResponse]:
        """Get recent sessions for user"""
        try:
            # Use repository method to get sessions
            sessions = self.session_repo.list_sessions(user_id=user_id, limit=limit)

            # Convert to SessionResponse objects
            session_responses = []
            for session in sessions:
                session_responses.append(
                    SessionResponse(
                        id=session.id,
                        grade_level=session.grade_level,
                        strand_code=session.strand_code,
                        selected_standards=None,  # Populated separately if needed
                        selected_objectives=session.selected_objectives.split(",")
                        if session.selected_objectives
                        else None,
                        selected_model=session.selected_model,
                        additional_context=session.additional_context,
                        conversation_history=session.conversation_history,
                        created_at=session.created_at,
                        updated_at=session.updated_at,
                    )
                )

            return session_responses
        except Exception as e:
            # Log error but don't fail the entire dashboard
            print(f"[DashboardService] Error fetching sessions: {e}")
            return []

    def _get_draft_section(self, user_id: str, limit: int) -> DashboardDraftSection:
        """Get draft section with count and recent drafts"""
        try:
            # Get all drafts for count
            all_drafts = self.lesson_repo.list_lessons_for_user(
                user_id=user_id, include_drafts=True
            )

            # Filter to only drafts
            drafts = [d for d in all_drafts if d.is_draft]

            # Sort by updated_at descending
            drafts_sorted = sorted(
                drafts,
                key=lambda x: str(x.updated_at) if x.updated_at else "",
                reverse=True,
            )

            # Convert to DraftResponse
            draft_responses = []
            for draft in drafts_sorted[:limit]:
                metadata = {}
                if draft.metadata:
                    try:
                        metadata = (
                            json.loads(draft.metadata)
                            if isinstance(draft.metadata, str)
                            else draft.metadata
                        )
                    except Exception:
                        metadata = {}

                draft_responses.append(
                    DraftResponse(
                        id=draft.id,
                        title=draft.title,
                        content=draft.content,
                        metadata=metadata,
                        created_at=str(draft.created_at) if draft.created_at else None,
                        updated_at=str(draft.updated_at) if draft.updated_at else None,
                    )
                )

            return DashboardDraftSection(
                total=len(drafts),
                items=draft_responses,
                latest=draft_responses[0] if draft_responses else None,
            )
        except Exception as e:
            print(f"[DashboardService] Error fetching drafts: {e}")
            return DashboardDraftSection(total=0, items=[], latest=None)

    def _get_presentation_summaries(
        self, user_id: str
    ) -> List[DashboardPresentationSummary]:
        """Get recent presentation summaries"""
        try:
            # Query presentations for user's lessons
            conn = self.db_manager.get_connection()
            try:
                cursor = conn.execute(
                    """
                    SELECT p.id, p.lesson_id, p.status, p.created_at, p.updated_at
                    FROM presentations p
                    INNER JOIN lessons l ON p.lesson_id = l.id
                    WHERE l.user_id = ?
                    ORDER BY p.created_at DESC
                    LIMIT 10
                    """,
                    (user_id,),
                )

                presentations = []
                for row in cursor.fetchall():
                    presentations.append(
                        DashboardPresentationSummary(
                            id=row[0],
                            lesson_id=row[1],
                            status=row[2] or "unknown",
                            created_at=row[3] or datetime.utcnow().isoformat(),
                            updated_at=row[4],
                        )
                    )

                return presentations
            finally:
                conn.close()
        except Exception as e:
            print(f"[DashboardService] Error fetching presentations: {e}")
            return []

    def _calculate_stats(self, user_id: str) -> DashboardStats:
        """Calculate quick workspace statistics"""
        try:
            conn = self.db_manager.get_connection()
            try:
                # Count lessons (non-drafts)
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM lessons WHERE user_id = ? AND is_draft = 0",
                    (user_id,),
                )
                lessons_count = cursor.fetchone()[0]

                # Count active drafts
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM lessons WHERE user_id = ? AND is_draft = 1",
                    (user_id,),
                )
                drafts_count = cursor.fetchone()[0]

                # Count presentations
                cursor = conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM presentations p
                    INNER JOIN lessons l ON p.lesson_id = l.id
                    WHERE l.user_id = ?
                    """,
                    (user_id,),
                )
                presentations_count = cursor.fetchone()[0]

                # Count sessions
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM sessions WHERE user_id = ?", (user_id,)
                )
                sessions_count = cursor.fetchone()[0]

                return DashboardStats(
                    lessons_created=lessons_count,
                    active_drafts=drafts_count,
                    total_presentations=presentations_count,
                    total_sessions=sessions_count,
                )
            finally:
                conn.close()
        except Exception as e:
            print(f"[DashboardService] Error calculating stats: {e}")
            return DashboardStats()
