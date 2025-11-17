"""Workspace dashboard endpoints."""

from datetime import datetime
from typing import Dict, Any, Optional, Set

from fastapi import APIRouter, Depends, Query

from ..dependencies import get_current_user
from backend.auth import User
from backend.repositories.session_repository import SessionRepository
from backend.repositories.lesson_repository import LessonRepository
from backend.repositories.presentation_repository import PresentationRepository
from backend.repositories.standards_repository import StandardsRepository
from backend.services.presentation_service import PresentationService
from .sessions import _session_to_response
from .drafts import _lesson_to_draft_response

ALLOWED_SECTIONS = {"sessions", "drafts", "presentations", "stats"}
DEFAULT_SECTIONS = set(ALLOWED_SECTIONS)

router = APIRouter(prefix="/api/workspace", tags=["workspace"])

_session_repo = SessionRepository()
_lesson_repo = LessonRepository()
_standard_repo = StandardsRepository()
_presentation_repo = PresentationRepository()
_presentation_service = PresentationService()


def _parse_includes(raw: Optional[str]) -> Set[str]:
    if not raw:
        return set(DEFAULT_SECTIONS)

    includes = {
        item.strip() for item in raw.split(",") if item.strip() in ALLOWED_SECTIONS
    }
    return includes or set(DEFAULT_SECTIONS)


def _serialize_sessions(user_id: str, limit: int = 10) -> Any:
    sessions = _session_repo.list_sessions(user_id, limit=limit)
    return [
        _session_to_response(session, _standard_repo).model_dump(by_alias=True)
        for session in sessions
    ]


def _serialize_drafts(user_id: str, limit: int = 5) -> Dict[str, Any]:
    # Get all lessons including drafts, then filter to only drafts
    all_lessons = _lesson_repo.list_lessons_for_user(user_id, include_drafts=True)
    draft_lessons = [l for l in all_lessons if l.is_draft]
    total_drafts = len(draft_lessons)

    # Limit to requested number
    draft_lessons = draft_lessons[:limit]

    draft_items = [
        _lesson_to_draft_response(lesson, _session_repo).model_dump(by_alias=True)
        for lesson in draft_lessons
    ]

    return {
        "total": total_drafts,
        "items": draft_items,
        "latest": draft_items[0] if draft_items else None,
    }


def _serialize_presentations(user_id: str, limit: int = 5) -> Any:
    presentations = _presentation_repo.list_recent_for_user(user_id, limit=limit)
    return [
        _presentation_service.serialize_presentation_summary(presentation)
        for presentation in presentations
    ]


def _serialize_stats(user_id: str) -> Dict[str, int]:
    lessons_created = _lesson_repo.count_lessons_for_user(user_id, is_draft=False)
    active_drafts = _lesson_repo.count_lessons_for_user(user_id, is_draft=True)

    return {
        "lessonsCreated": lessons_created,
        "activeDrafts": active_drafts,
    }


@router.get("/dashboard")
async def get_workspace_dashboard(
    include: Optional[str] = Query(
        None,
        description="Comma-separated list of sections to include: sessions,drafts,presentations,stats",
    ),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return aggregated workspace data for the current user."""

    sections = _parse_includes(include)
    payload: Dict[str, Any] = {
        "generatedAt": datetime.utcnow().isoformat(),
        "includes": sorted(sections),
    }

    if "sessions" in sections:
        payload["sessions"] = _serialize_sessions(current_user.id)

    if "drafts" in sections:
        payload["drafts"] = _serialize_drafts(current_user.id)

    if "presentations" in sections:
        payload["presentations"] = _serialize_presentations(current_user.id)

    if "stats" in sections:
        payload["stats"] = _serialize_stats(current_user.id)

    return payload
