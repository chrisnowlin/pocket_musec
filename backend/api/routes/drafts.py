"""Drafts management endpoints"""

import json
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from ...repositories.lesson_repository import LessonRepository
from ...repositories.session_repository import SessionRepository
from ..models import (
    DraftResponse,
    DraftCreateRequest,
    DraftUpdateRequest,
)
from ..dependencies import get_current_user
from ...auth import User

router = APIRouter(prefix="/api/drafts", tags=["drafts"])


def _lesson_to_draft_response(lesson, session_repo: SessionRepository) -> DraftResponse:
    """Convert a lesson to a draft response format"""
    
    # Get session information for metadata
    session = session_repo.get_session(lesson.session_id)
    
    # Parse metadata if available
    metadata = {}
    if lesson.metadata:
        try:
            metadata = json.loads(lesson.metadata)
        except (json.JSONDecodeError, TypeError):
            metadata = {}
    
    return DraftResponse(
        id=lesson.id,
        title=lesson.title,
        content=lesson.content,
        metadata=metadata,
        grade=metadata.get('grade_level') or (session.grade_level if session else None),
        strand=metadata.get('strand_code') or (session.strand_code if session else None),
        standard=metadata.get('standard_id'),
        created_at=lesson.created_at.isoformat() if lesson.created_at else None,
        updated_at=lesson.updated_at.isoformat() if lesson.updated_at else None,
    )


@router.get("", response_model=List[DraftResponse])
async def list_drafts(
    current_user: User = Depends(get_current_user),
) -> List[DraftResponse]:
    """List all drafts for the current user"""
    lesson_repo = LessonRepository()
    session_repo = SessionRepository()
    
    # Get only draft lessons for the user
    lessons = lesson_repo.list_lessons_for_user(current_user.id, is_draft=True)
    
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
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Draft not found"
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
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Session not found"
        )
    
    # Create the lesson as a draft
    lesson = lesson_repo.create_lesson(
        session_id=request.session_id,
        user_id=current_user.id,
        title=request.title,
        content=request.content,
        metadata=json.dumps(request.metadata) if request.metadata else None,
        processing_mode=current_user.processing_mode.value,
        is_draft=True,
    )
    
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
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Draft not found"
        )
    
    # Update the draft
    updated_lesson = lesson_repo.update_lesson(
        lesson_id=draft_id,
        title=request.title,
        content=request.content,
        metadata=json.dumps(request.metadata) if request.metadata is not None else None,
        is_draft=True,  # Ensure it remains a draft
    )
    
    if not updated_lesson:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update draft"
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
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Draft not found"
        )
    
    # Delete the draft
    success = lesson_repo.delete_lesson(draft_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete draft"
        )
    
    return {"message": "Draft deleted successfully"}