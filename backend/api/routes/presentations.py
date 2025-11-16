"""Presentation generation and management endpoints"""

import io
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Body,
    Query,
    BackgroundTasks,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..dependencies import get_current_user
from backend.auth import User
from backend.repositories.lesson_repository import LessonRepository
from backend.services.presentation_service import PresentationService
from backend.services.presentation_jobs import (
    get_job_manager,
    create_presentation_job,
    get_presentation_job_status,
)
from backend.lessons.presentation_schema import (
    PresentationDocument,
    PresentationExport,
    PresentationStatus,
)

router = APIRouter(prefix="/api/presentations", tags=["presentations"])
logger = logging.getLogger(__name__)


def _generate_export_asset_on_demand(
    service: PresentationService,
    presentation: PresentationDocument,
    export_format: str,
) -> PresentationExport:
    """Ensure a requested export asset exists, generating it if necessary."""
    format_map = {
        "json": service._create_json_export,
        "markdown": service._create_markdown_export,
        "pptx": service._create_pptx_export,
        "pdf": service._create_pdf_export,
    }

    if export_format not in format_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {export_format}",
        )

    try:
        export_asset = format_map[export_format](presentation)
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export format '{export_format}' requires optional dependency: {exc.name}",
        ) from exc
    except Exception as exc:
        logger.error(
            "Failed to generate %s export for presentation %s: %s",
            export_format,
            presentation.id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate {export_format} export",
        ) from exc

    service.presentation_repo.add_export_asset(
        presentation_id=presentation.id,
        export_asset=export_asset,
    )
    return export_asset


# Request/Response models
class PresentationGenerateRequest(BaseModel):
    """Request to generate a presentation."""

    lesson_id: str = Field(
        ..., description="ID of the lesson to generate presentation for"
    )
    style: str = Field(default="default", description="Presentation style")
    use_llm_polish: bool = Field(
        default=True, description="Whether to use LLM polishing"
    )
    timeout_seconds: int = Field(default=30, description="Timeout for LLM operations")


class PresentationGenerateResponse(BaseModel):
    """Response for presentation generation request."""

    job_id: str = Field(..., description="Job ID for tracking generation progress")
    status: str = Field(..., description="Initial job status")
    message: str = Field(..., description="Status message")


class PresentationStatusResponse(BaseModel):
    """Response for presentation status query."""

    job_id: str
    status: str
    lesson_id: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    presentation_id: Optional[str] = None
    error: Optional[str] = None


class PresentationResponse(BaseModel):
    """Response containing presentation details."""

    id: str
    presentation_id: str
    lesson_id: str
    lesson_revision: int
    version: str
    status: str
    style: str
    slide_count: int
    created_at: str
    updated_at: str
    has_exports: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class PresentationDetailResponse(PresentationResponse):
    """Detailed presentation response with slides."""

    slides: List[Dict[str, Any]]
    export_assets: List[Dict[str, Any]]


@router.post("/generate", response_model=PresentationGenerateResponse)
async def generate_presentation(
    request: PresentationGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> PresentationGenerateResponse:
    """Generate a presentation for a lesson asynchronously."""

    # Verify user has access to the lesson
    lesson_repo = LessonRepository()
    lesson = lesson_repo.get_lesson(request.lesson_id)

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )

    if lesson.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Create background job
    job_id = create_presentation_job(
        lesson_id=request.lesson_id,
        user_id=current_user.id,
        style=request.style,
        use_llm_polish=request.use_llm_polish,
        timeout_seconds=request.timeout_seconds,
    )

    # Add job to background tasks
    job_manager = get_job_manager()
    background_tasks.add_task(
        job_manager.execute_job,
        job_id=job_id,
        style=request.style,
        use_llm_polish=request.use_llm_polish,
        timeout_seconds=request.timeout_seconds,
    )

    return PresentationGenerateResponse(
        job_id=job_id, status="pending", message="Presentation generation started"
    )


@router.get("/jobs/{job_id}", response_model=PresentationStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
) -> PresentationStatusResponse:
    """Get the status of a presentation generation job."""

    job_status = get_presentation_job_status(job_id)

    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    # Verify job belongs to current user
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job or job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return PresentationStatusResponse(**job_status)


@router.get("/jobs", response_model=List[PresentationStatusResponse])
async def list_user_jobs(
    limit: int = Query(default=20, le=100),
    current_user: User = Depends(get_current_user),
) -> List[PresentationStatusResponse]:
    """List presentation jobs for the current user."""

    job_manager = get_job_manager()
    jobs = job_manager.get_user_jobs(current_user.id, limit)

    return [
        PresentationStatusResponse(**job_manager.get_job_status(job.id)) for job in jobs
    ]


@router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Cancel a pending presentation generation job."""

    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    success = job_manager.cancel_job(job_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job cannot be cancelled (may have already started)",
        )

    return {"message": "Job cancelled successfully"}


# Lesson-specific presentation endpoints
@router.get(
    "/lessons/{lesson_id}/latest", response_model=Optional[PresentationResponse]
)
async def get_latest_presentation(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
) -> Optional[PresentationResponse]:
    """Get the latest non-stale presentation for a lesson."""

    # Verify user has access to the lesson
    lesson_repo = LessonRepository()
    lesson = lesson_repo.get_lesson(lesson_id)

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )

    if lesson.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    presentation_service = PresentationService()
    status_info = presentation_service.get_presentation_status(lesson_id)

    if not status_info:
        return None

    return PresentationResponse(**status_info)


@router.get(
    "/lessons/{lesson_id}/presentations", response_model=List[PresentationResponse]
)
async def list_lesson_presentations(
    lesson_id: str,
    include_stale: bool = Query(default=False),
    limit: int = Query(default=10, le=50),
    current_user: User = Depends(get_current_user),
) -> List[PresentationResponse]:
    """List presentations for a lesson."""

    # Verify user has access to the lesson
    lesson_repo = LessonRepository()
    lesson = lesson_repo.get_lesson(lesson_id)

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )

    if lesson.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    presentation_service = PresentationService()
    presentation_repo = presentation_service.presentation_repo

    presentations = presentation_repo.list_presentations_for_lesson(
        lesson_id=lesson_id,
        include_stale=include_stale,
        limit=limit,
    )

    return [
        PresentationResponse(
            id=p.id,
            presentation_id=p.id,
            lesson_id=p.lesson_id,
            lesson_revision=p.lesson_revision,
            version=p.version,
            status=p.status.value,
            style=p.style,
            slide_count=len(p.slides),
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
            has_exports=len(p.export_assets) > 0,
            error_code=p.error_code,
            error_message=p.error_message,
        )
        for p in presentations
    ]


@router.get("/{presentation_id}", response_model=PresentationDetailResponse)
async def get_presentation(
    presentation_id: str,
    current_user: User = Depends(get_current_user),
) -> PresentationDetailResponse:
    """Get detailed presentation information including slides."""

    presentation_service = PresentationService()
    presentation = presentation_service.get_presentation(
        presentation_id, current_user.id
    )

    if not presentation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found"
        )

    return PresentationDetailResponse(
        id=presentation.id,
        presentation_id=presentation.id,
        lesson_id=presentation.lesson_id,
        lesson_revision=presentation.lesson_revision,
        version=presentation.version,
        status=presentation.status.value,
        style=presentation.style,
        slide_count=len(presentation.slides),
        created_at=presentation.created_at.isoformat(),
        updated_at=presentation.updated_at.isoformat(),
        has_exports=len(presentation.export_assets) > 0,
        error_code=presentation.error_code,
        error_message=presentation.error_message,
        slides=[slide.model_dump() for slide in presentation.slides],
        export_assets=[asset.model_dump() for asset in presentation.export_assets],
    )


@router.post(
    "/{presentation_id}/regenerate", response_model=PresentationGenerateResponse
)
async def regenerate_presentation(
    presentation_id: str,
    background_tasks: BackgroundTasks,
    style: str = Body(default="default"),
    use_llm_polish: bool = Body(default=True),
    timeout_seconds: int = Body(default=30),
    current_user: User = Depends(get_current_user),
) -> PresentationGenerateResponse:
    """Regenerate a presentation for a lesson."""

    presentation_service = PresentationService()
    presentation = presentation_service.get_presentation(
        presentation_id, current_user.id
    )

    if not presentation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found"
        )

    # Create new job for regeneration
    job_id = create_presentation_job(
        lesson_id=presentation.lesson_id,
        user_id=current_user.id,
        style=style,
        use_llm_polish=use_llm_polish,
        timeout_seconds=timeout_seconds,
    )

    # Add regeneration job to background tasks
    job_manager = get_job_manager()
    background_tasks.add_task(
        job_manager.execute_job,
        job_id=job_id,
        style=style,
        use_llm_polish=use_llm_polish,
        timeout_seconds=timeout_seconds,
    )

    return PresentationGenerateResponse(
        job_id=job_id, status="pending", message="Presentation regeneration started"
    )


@router.get("/{presentation_id}/export")
async def export_presentation(
    presentation_id: str,
    format: str = Query(..., regex="^(json|markdown|pptx|pdf)$"),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Export a presentation in the specified format."""

    presentation_service = PresentationService()
    presentation = presentation_service.get_presentation(
        presentation_id, current_user.id
    )

    if not presentation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found"
        )

    if presentation.status != PresentationStatus.COMPLETE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Presentation is not ready for export",
        )

    # Find the requested export asset
    export_asset = None
    for asset in presentation.export_assets:
        if asset.format == format:
            export_asset = asset
            break

    if not export_asset:
        export_asset = _generate_export_asset_on_demand(
            presentation_service, presentation, format
        )

    # Generate content
    if format == "json":
        content = json.dumps(
            {
                "presentation": presentation.model_dump(),
                "generated_at": presentation.created_at.isoformat(),
                "format": "p1.0",
            },
            indent=2,
        )
        media_type = "application/json"
        filename = f"presentation_{presentation_id}.json"
    elif format == "markdown":
        # Generate markdown content
        lines = [
            f"# {presentation.slides[0].title if presentation.slides else 'Presentation'}",
            "",
            f"**Generated:** {presentation.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"**Lesson ID:** {presentation.lesson_id}",
            f"**Revision:** {presentation.lesson_revision}",
            "",
            "---",
            "",
        ]

        for slide in presentation.slides:
            lines.extend([f"## {slide.title}", ""])

            if slide.subtitle:
                lines.extend([f"**{slide.subtitle}**", ""])

            if slide.key_points:
                lines.extend(["**Key Points:**", ""])
                for point in slide.key_points:
                    lines.append(f"- {point}")
                lines.append("")

            if slide.teacher_script:
                lines.extend(["**Teacher Script:**", "", slide.teacher_script, ""])

            if slide.duration_minutes:
                lines.extend([f"**Duration:** {slide.duration_minutes} minutes", ""])

            if slide.standard_codes:
                lines.extend(["**Standards:** " + ", ".join(slide.standard_codes), ""])

            lines.extend(["---", ""])

        content = "\n".join(lines)
        media_type = "text/markdown"
        filename = f"presentation_{presentation_id}.md"
    elif format == "pptx":
        # Read the PPTX file
        import os

        if not os.path.exists(export_asset.url_or_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PPTX export file not found",
            )

        with open(export_asset.url_or_path, "rb") as f:
            content = f.read()

        media_type = (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
        filename = f"presentation_{presentation_id}.pptx"

        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    elif format == "pdf":
        # Read the PDF file
        import os

        if not os.path.exists(export_asset.url_or_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF export file not found",
            )

        with open(export_asset.url_or_path, "rb") as f:
            content = f.read()

        media_type = "application/pdf"
        filename = f"presentation_{presentation_id}.pdf"

        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {format}",
        )

    # Return as streaming response for text formats
    return StreamingResponse(
        io.StringIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
