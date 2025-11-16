"""Drafts management endpoints"""

import json
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError

from repositories.lesson_repository import LessonRepository
from repositories.session_repository import SessionRepository
from ..models import (
    DraftResponse,
    DraftCreateRequest,
    DraftUpdateRequest,
)
from ..dependencies import get_current_user
from auth import User
from lessons.schema_m2 import build_m2_lesson_document
from services.presentation_service import PresentationService

router = APIRouter(prefix="/api/drafts", tags=["drafts"])


def _parse_metadata(raw_metadata: Optional[str]) -> Dict[str, Any]:
    """Safely parse JSON metadata stored on a lesson"""
    if not raw_metadata:
        return {}
    try:
        return json.loads(raw_metadata)
    except (json.JSONDecodeError, TypeError):
        return {}


def _validate_and_attach_m2_document(
    metadata: Dict[str, Any],
    existing_document: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Validate an optional m2.0 lesson_document inside metadata.

    If ``metadata`` contains a ``lesson_document`` key, this helper will:

    - Run the payload through :func:`build_m2_lesson_document`, optionally using
      an existing document to handle revision bumps.
    - On success, replace ``lesson_document`` with the fully validated
      Pydantic dump so it can be JSON-serialized.
    - On validation error, raise ``HTTPException`` with ``400 Bad Request`` so
      callers see structured error information.

    If ``lesson_document`` is absent, ``metadata`` is returned unchanged.
    """

    if "lesson_document" not in metadata:
        return metadata

    raw_document = metadata["lesson_document"]
    if raw_document is None:
        # Explicit null clears the document
        metadata.pop("lesson_document", None)
        return metadata

    try:
        doc = build_m2_lesson_document(raw_document, existing=existing_document)
    except ValidationError as exc:
        # Map Pydantic validation errors to a 400 at the HTTP boundary
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid m2.0 lesson_document",
                "errors": exc.errors() if hasattr(exc, "errors") else str(exc),
            },
        )

    dump_method = getattr(doc, "model_dump", None)
    metadata["lesson_document"] = (
        dump_method(mode="python") if callable(dump_method) else doc.dict()
    )
    return metadata


def _trigger_presentation_generation(lesson_id: str, user_id: str) -> None:
    """Trigger presentation generation for a lesson in the background.

    This is a fire-and-forget operation that doesn't block the response.
    """
    try:
        from services.presentation_jobs import create_presentation_job
        import asyncio

        # Create the job asynchronously
        async def trigger_job():
            try:
                job_id = create_presentation_job(
                    lesson_id=lesson_id,
                    user_id=user_id,
                    style="default",
                    use_llm_polish=True,
                    timeout_seconds=30,
                )
                # Execute the job in background
                from services.presentation_jobs import get_job_manager

                job_manager = get_job_manager()
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    job_manager.execute_job,
                    job_id,
                    "default",
                    True,
                    30,
                )
            except Exception as e:
                # Log error but don't fail the draft creation
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Failed to trigger presentation generation for lesson {lesson_id}: {e}"
                )

        # Schedule the background task
        asyncio.create_task(trigger_job())

    except Exception as e:
        # Log error but don't fail the draft creation
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(
            f"Failed to schedule presentation generation for lesson {lesson_id}: {e}"
        )


def _lesson_to_draft_response(lesson, session_repo: SessionRepository) -> DraftResponse:
    """Convert a lesson to a draft response format.

    This helper now assumes that any structured ``lesson_document`` has
    already been validated and attached at write time (via
    ``_validate_and_attach_m2_document``). It no longer performs any
    on-read migration for legacy data; if a lesson lacks a
    ``lesson_document`` in its metadata, the frontend will fall back to
    the narrative ``content`` string instead.
    """

    # Get session information for metadata fallbacks
    session = session_repo.get_session(lesson.session_id)

    # Parse metadata if available, but do not mutate it with synthesized
    # m2.0 documents.
    metadata = _parse_metadata(lesson.metadata)

    return DraftResponse(
        id=lesson.id,
        title=lesson.title,
        content=lesson.content,
        metadata=metadata,
        grade=metadata.get("grade_level") or (session.grade_level if session else None),
        strand=metadata.get("strand_code")
        or (session.strand_code if session else None),
        standard=metadata.get("standard_id"),
        created_at=lesson.created_at.isoformat() if lesson.created_at else None,
        updated_at=lesson.updated_at.isoformat() if lesson.updated_at else None,
    )


@router.get("", response_model=List[DraftResponse])
async def list_drafts(
    session_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
) -> List[DraftResponse]:
    """List all drafts for the current user"""
    lesson_repo = LessonRepository()
    session_repo = SessionRepository()

    # Get only draft lessons for the user
    lessons = lesson_repo.list_lessons_for_user(
        current_user.id,
        is_draft=True,
        session_id=session_id,
    )

    return [_lesson_to_draft_response(lesson, session_repo) for lesson in lessons]


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
) -> DraftResponse:
    """Get a specific draft by ID"""
    lesson_repo = LessonRepository()
    session_repo = SessionRepository()

    lesson = lesson_repo.get_lesson(draft_id)
    if not lesson or lesson.user_id != current_user.id or not lesson.is_draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found"
        )

    return _lesson_to_draft_response(lesson, session_repo)


@router.post("", response_model=DraftResponse)
async def create_draft(
    request: DraftCreateRequest,
    current_user: User = Depends(get_current_user),
) -> DraftResponse:
    """Create a new draft"""
    lesson_repo = LessonRepository()
    session_repo = SessionRepository()

    # Verify the session belongs to the user
    session = session_repo.get_session(request.session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    # Create the lesson as a draft
    metadata_dict: Optional[Dict[str, Any]] = (
        dict(request.metadata) if request.metadata else None
    )
    if metadata_dict is not None:
        metadata_dict = _validate_and_attach_m2_document(metadata_dict)

    lesson = lesson_repo.create_lesson(
        session_id=request.session_id,
        user_id=current_user.id,
        title=request.title,
        content=request.content,
        metadata=json.dumps(metadata_dict) if metadata_dict else None,
        processing_mode=current_user.processing_mode.value,
        is_draft=True,
    )

    # Trigger presentation generation if this is an m2.0 lesson document
    if metadata_dict and "lesson_document" in metadata_dict:
        _trigger_presentation_generation(lesson.id, current_user.id)

    return _lesson_to_draft_response(lesson, session_repo)


@router.put("/{draft_id}", response_model=DraftResponse)
async def update_draft(
    draft_id: str,
    request: DraftUpdateRequest,
    current_user: User = Depends(get_current_user),
) -> DraftResponse:
    """Update an existing draft"""
    lesson_repo = LessonRepository()
    session_repo = SessionRepository()

    # Get the existing draft
    lesson = lesson_repo.get_lesson(draft_id)
    if not lesson or lesson.user_id != current_user.id or not lesson.is_draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found"
        )

    # Update the draft
    metadata_payload = None
    if request.metadata is not None:
        existing_metadata = _parse_metadata(lesson.metadata)
        merged_metadata = {**existing_metadata, **request.metadata}
        merged_metadata = _validate_and_attach_m2_document(
            merged_metadata,
            existing_document=existing_metadata.get("lesson_document"),
        )
        metadata_payload = json.dumps(merged_metadata)

    updated_lesson = lesson_repo.update_lesson(
        lesson_id=draft_id,
        title=request.title,
        content=request.content,
        metadata=metadata_payload,
        is_draft=True,  # Ensure it remains a draft
    )

    if not updated_lesson:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update draft",
        )

    return _lesson_to_draft_response(updated_lesson, session_repo)


@router.delete("/{draft_id}")
async def delete_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Delete a draft"""
    lesson_repo = LessonRepository()

    # Get the existing draft to verify ownership
    lesson = lesson_repo.get_lesson(draft_id)
    if not lesson or lesson.user_id != current_user.id or not lesson.is_draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found"
        )

    # Delete the draft
    success = lesson_repo.delete_lesson(draft_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete draft",
        )

    return {"message": "Draft deleted successfully"}
