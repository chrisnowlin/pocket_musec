"""Lesson generation endpoints"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from pydantic import BaseModel
import json

from ..dependencies import get_current_user
from ...auth import User
from ..models import LessonSummary
from ...repositories.lesson_repository import LessonRepository

router = APIRouter(prefix="/api/lessons", tags=["lessons"])


@router.get("", response_model=List[LessonSummary])
async def list_lessons(
    is_draft: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
) -> List[LessonSummary]:
    """List lessons for the current user, optionally filtered by is_draft status"""
    lesson_repo = LessonRepository()

    # Get lessons with optional is_draft filter
    lessons = lesson_repo.list_lessons_for_user(
        current_user.id,
        is_draft=is_draft,
    )

    # Convert to LessonSummary responses
    results = []
    for lesson in lessons:
        # Parse metadata
        metadata = {}
        if lesson.metadata:
            try:
                metadata = json.loads(lesson.metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        results.append(LessonSummary(
            id=lesson.id,
            title=lesson.title,
            summary=lesson.content[:200] + "..." if len(lesson.content) > 200 else lesson.content,
            content=lesson.content,
            metadata=metadata,
            citations=[],
        ))

    return results


@router.get("/{lesson_id}", response_model=LessonSummary)
async def get_lesson(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
) -> LessonSummary:
    """Get a specific lesson by ID"""
    lesson_repo = LessonRepository()

    lesson = lesson_repo.get_lesson(lesson_id)
    if not lesson or lesson.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    # Parse metadata
    metadata = {}
    if lesson.metadata:
        try:
            metadata = json.loads(lesson.metadata)
        except (json.JSONDecodeError, TypeError):
            metadata = {}

    return LessonSummary(
        id=lesson.id,
        title=lesson.title,
        summary=lesson.content[:200] + "..." if len(lesson.content) > 200 else lesson.content,
        content=lesson.content,
        metadata=metadata,
        citations=[],
    )


@router.delete("/{lesson_id}")
async def delete_lesson(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete a lesson"""
    lesson_repo = LessonRepository()

    # Verify ownership
    lesson = lesson_repo.get_lesson(lesson_id)
    if not lesson or lesson.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    # Delete the lesson
    success = lesson_repo.delete_lesson(lesson_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete lesson"
        )

    return {"message": "Lesson deleted successfully"}


class LessonGenerationRequest(BaseModel):
    """Request for direct lesson generation"""

    grade_level: str
    strand_code: str
    standard_id: Optional[str] = None
    objectives: Optional[List[str]] = None
    duration: str = "30 minutes"
    class_size: str = "25"
    additional_context: Optional[str] = None


@router.post("/generate", response_model=LessonSummary)
async def generate_lesson(
    request: LessonGenerationRequest,
    current_user: User = Depends(get_current_user),
) -> LessonSummary:
    """Generate a lesson directly without session management"""
    try:
        # Generate lesson content based on request
        lesson_content = _create_lesson_content(
            grade_level=request.grade_level,
            strand_code=request.strand_code,
            standard_id=request.standard_id,
            objectives=request.objectives or [],
            duration=request.duration,
            class_size=request.class_size,
            additional_context=request.additional_context or "",
        )

        # Create lesson summary
        metadata = {
            "grade_level": request.grade_level,
            "strand_code": request.strand_code,
            "standard_id": request.standard_id,
            "duration": request.duration,
            "class_size": request.class_size,
            "user_id": current_user.id,
        }

        title = f"{request.grade_level} {request.strand_code} Music Lesson"
        summary = (
            lesson_content[:200] + "..."
            if len(lesson_content) > 200
            else lesson_content
        )

        return LessonSummary(
            id=f"generated-{hash(lesson_content) % 1000000}",
            title=title,
            summary=summary,
            content=lesson_content,
            metadata=metadata,
            citations=[],
        )

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate lesson: {str(e)}",
        )


def _create_lesson_content(
    grade_level: str,
    strand_code: str,
    standard_id: Optional[str],
    objectives: List[str],
    duration: str,
    class_size: str,
    additional_context: str,
) -> str:
    """Helper function to create lesson content from requirements"""

    objectives_text = (
        "\n".join(f"- {obj}" for obj in objectives)
        if objectives
        else "- Students will engage with music concepts"
    )

    lesson_content = f"""# {grade_level} {strand_code} Music Lesson

## Lesson Overview
**Grade Level:** {grade_level}  
**Strand:** {strand_code}  
**Standard:** {standard_id or "To be determined"}  
**Duration:** {duration}  
**Class Size:** {class_size} students

## Learning Objectives
{objectives_text}

## Lesson Context
{additional_context if additional_context else "This lesson introduces students to core musical concepts aligned with national standards."}

## Lesson Activities

### Warm-up (5 minutes)
- Welcome students and establish focus
- Brief rhythmic or melodic exercises to prepare for learning
- Review prior concepts if applicable

### Main Activity (15-20 minutes)
- **Introduction:** Present the core musical concept for the day
- **Exploration:** Students engage with the concept through listening and analysis
- **Practice:** Hands-on application with instruments or voice
- **Creation:** Students create their own musical examples
- **Collaboration:** Small group work to reinforce concepts

### Cool-down (5 minutes)
- Review and reflect on key learning points
- Students share one thing they learned
- Preview next lesson concepts

## Assessment Strategies
- **Formative:** Observe student participation and engagement throughout lesson
- **Check for Understanding:** Use targeted questions and student demonstrations
- **Performance Assessment:** Review completed work or performances
- **Self-Assessment:** Students reflect on their own learning

## Materials Needed
- Basic classroom instruments (rhythm sticks, hand drums, xylophones)
- Whiteboard or chart paper for notation
- Audio playback system
- Student handouts or worksheets (as appropriate)
- Visual aids relevant to the concept

## Differentiation & Extensions
- **For Advanced Learners:** Provide additional complexity in rhythmic or melodic patterns
- **For Struggling Learners:** Simplify patterns and provide additional modeling
- **For English Language Learners:** Use visual aids and demonstrations
- **Technology Integration:** Consider using music apps or notation software
- **Cross-Curricular Connections:** Link to math (patterns, fractions), language arts (storytelling)

## Standards Alignment
This lesson aligns with National Core Arts Standards for Music Education, specifically the {strand_code} strand for {grade_level}.

## Additional Notes
- Ensure all students have equitable access to instruments
- Consider classroom management strategies for instrument distribution
- Have a backup plan for activities that may need adjustment
- Be prepared to extend or condense based on student engagement

---
*Generated by PocketMusec AI Assistant*
*Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""
    return lesson_content


# Import at module level for the f-string
from datetime import datetime


@router.post("/{lesson_id}/promote", response_model=LessonSummary)
async def promote_lesson(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
) -> LessonSummary:
    """Promote a draft lesson to a permanent lesson"""
    lesson_repo = LessonRepository()

    # Get the existing lesson
    lesson = lesson_repo.get_lesson(lesson_id)
    if not lesson or lesson.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    # Promote the lesson
    promoted_lesson = lesson_repo.promote_lesson(lesson_id)
    if not promoted_lesson:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to promote lesson"
        )

    # Parse metadata
    metadata = {}
    if promoted_lesson.metadata:
        try:
            import json
            metadata = json.loads(promoted_lesson.metadata)
        except (json.JSONDecodeError, TypeError):
            metadata = {}

    return LessonSummary(
        id=promoted_lesson.id,
        title=promoted_lesson.title,
        summary=promoted_lesson.content[:200] + "..." if len(promoted_lesson.content) > 200 else promoted_lesson.content,
        content=promoted_lesson.content,
        metadata=metadata,
        citations=[],
    )


@router.post("/{lesson_id}/demote", response_model=LessonSummary)
async def demote_lesson(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
) -> LessonSummary:
    """Demote a permanent lesson back to a draft"""
    lesson_repo = LessonRepository()

    # Get the existing lesson
    lesson = lesson_repo.get_lesson(lesson_id)
    if not lesson or lesson.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    # Demote the lesson
    demoted_lesson = lesson_repo.demote_lesson(lesson_id)
    if not demoted_lesson:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to demote lesson"
        )

    # Parse metadata
    metadata = {}
    if demoted_lesson.metadata:
        try:
            import json
            metadata = json.loads(demoted_lesson.metadata)
        except (json.JSONDecodeError, TypeError):
            metadata = {}

    return LessonSummary(
        id=demoted_lesson.id,
        title=demoted_lesson.title,
        summary=demoted_lesson.content[:200] + "..." if len(demoted_lesson.content) > 200 else demoted_lesson.content,
        content=demoted_lesson.content,
        metadata=metadata,
        citations=[],
    )
