"""Endpoints for exploring standards metadata"""

from typing import Optional, List
from fastapi import APIRouter, Query, Depends, HTTPException, status

from ...repositories.standards_repository import StandardsRepository
from ..models import StandardResponse
from ..dependencies import get_current_user
from ...auth import User

router = APIRouter(prefix="/api/standards", tags=["standards"])


def _standard_to_response(standard, repo: StandardsRepository) -> StandardResponse:
    objectives = repo.get_objectives_for_standard(standard.standard_id)
    learning_objectives = [obj.objective_text for obj in objectives]
    # Convert database grade format to frontend display format
    # Database stores: "0", "1", "2", "3", etc.
    # Frontend expects: "Kindergarten", "Grade 1", "Grade 2", "Grade 3", etc.
    grade_display = standard.grade_level
    if grade_display == "0" or grade_display == "K":
        grade_display = "Kindergarten"
    elif grade_display and grade_display.isdigit():
        # Convert numeric grades to "Grade X" format
        grade_display = f"Grade {grade_display}"
    return StandardResponse(
        id=standard.standard_id,
        code=standard.standard_id,
        grade=grade_display,
        strand_code=standard.strand_code,
        strand_name=standard.strand_name,
        title=standard.standard_text,
        description=standard.strand_description,
        objectives=len(objectives),
        learning_objectives=learning_objectives,
    )


@router.get("", response_model=List[StandardResponse])
async def list_standards(
    grade_level: Optional[str] = Query(None),
    strand_code: Optional[str] = Query(None),
    limit: int = Query(50, gt=0, le=200),
    current_user: User = Depends(get_current_user),
) -> List[StandardResponse]:
    """List standards filtered by grade or strand"""
    repo = StandardsRepository()
    standards = repo.list_standards(
        grade_level=grade_level, strand_code=strand_code, limit=limit
    )
    return [_standard_to_response(std, repo) for std in standards]


@router.get("/{standard_id}", response_model=StandardResponse)
async def get_standard(
    standard_id: str, current_user: User = Depends(get_current_user)
) -> StandardResponse:
    """Return detail for a single standard"""
    repo = StandardsRepository()
    standard = repo.get_standard_by_id(standard_id)
    if not standard:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Standard not found")
    return _standard_to_response(standard, repo)
