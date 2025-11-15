"""Lesson generation endpoints"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel

from ..dependencies import get_current_user
from ...auth import User
from ..models import LessonSummary

router = APIRouter(prefix="/api/lessons", tags=["lessons"])


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
