"""Presentation generation and management endpoints"""

import io
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

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
from ..models import CamelModel
from backend.auth import User
from backend.repositories.lesson_repository import LessonRepository
from backend.services.presentation_service import PresentationService
from backend.services.presentation_jobs import (
    get_job_manager,
    create_presentation_job,
    get_presentation_job_status,
    initialize_job_system,
)
from backend.models.presentation_jobs import JobStatus, JobPriority
from backend.services.presentation_errors import (
    PresentationError,
    PresentationErrorCode,
    create_error_from_exception,
    ErrorRecoveryStrategy,
)
from backend.services.export_status_service import (
    export_status_service,
    ExportStatus,
    ExportFormat,
)
from backend.lessons.presentation_schema import (
    PresentationDocument,
    PresentationExport,
    PresentationStatus,
)
from backend.services.progress_websocket import get_websocket_manager
from fastapi import WebSocket, WebSocketDisconnect
from backend.models.streaming_schema import (
    create_job_status_envelope,
    JobStatusEnvelope,
)

router = APIRouter(prefix="/api/presentations", tags=["presentations"])
logger = logging.getLogger(__name__)


def _handle_presentation_error(error: PresentationError) -> HTTPException:
    """Convert PresentationError to appropriate HTTPException with status codes."""
    # Map error codes to HTTP status
    status_code_map = {
        PresentationErrorCode.LESSON_NOT_FOUND: status.HTTP_404_NOT_FOUND,
        PresentationErrorCode.LESSON_ACCESS_DENIED: status.HTTP_403_FORBIDDEN,
        PresentationErrorCode.JOB_NOT_FOUND: status.HTTP_404_NOT_FOUND,
        PresentationErrorCode.JOB_ACCESS_DENIED: status.HTTP_403_FORBIDDEN,
        PresentationErrorCode.PERMISSION_DENIED: status.HTTP_403_FORBIDDEN,
        PresentationErrorCode.VALIDATION_FAILED: status.HTTP_400_BAD_REQUEST,
        PresentationErrorCode.INVALID_STYLE: status.HTTP_400_BAD_REQUEST,
        PresentationErrorCode.INVALID_TIMEOUT: status.HTTP_400_BAD_REQUEST,
        PresentationErrorCode.INVALID_EXPORT_FORMAT: status.HTTP_400_BAD_REQUEST,
        PresentationErrorCode.JOB_TIMEOUT: status.HTTP_408_REQUEST_TIMEOUT,
        PresentationErrorCode.LLM_TIMEOUT: status.HTTP_408_REQUEST_TIMEOUT,
        PresentationErrorCode.LLM_RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
        PresentationErrorCode.SERVICE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
        PresentationErrorCode.EXPORT_PERMISSION_DENIED: status.HTTP_403_FORBIDDEN,
        PresentationErrorCode.EXPORT_STORAGE_FAILED: status.HTTP_507_INSUFFICIENT_STORAGE,
        PresentationErrorCode.DATABASE_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
        PresentationErrorCode.LLM_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
        PresentationErrorCode.LLM_QUOTA_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
        PresentationErrorCode.LESSON_PARSE_FAILED: status.HTTP_422_UNPROCESSABLE_ENTITY,
        PresentationErrorCode.EXPORT_PPTX_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
        PresentationErrorCode.EXPORT_PDF_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
        PresentationErrorCode.EXPORT_JSON_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
        PresentationErrorCode.EXPORT_MARKDOWN_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
        PresentationErrorCode.JOB_CANCELLED: status.HTTP_400_BAD_REQUEST,
        PresentationErrorCode.JOB_ALREADY_RUNNING: status.HTTP_409_CONFLICT,
        PresentationErrorCode.NETWORK_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
        PresentationErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    # Get appropriate status code
    http_status = status_code_map.get(error.code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Create response with error details and recovery information
    error_response = {
        "error": error.to_dict(),
        "timestamp": datetime.utcnow().isoformat(),
        "recovery": {
            "retry_recommended": error.retry_recommended,
            "retry_after_seconds": error.retry_after_seconds,
            "actions": ErrorRecoveryStrategy.get_recovery_actions(error),
        }
        if hasattr(error, "code")
        else None,
        "request_id": None,  # Could add request tracking here
    }

    return HTTPException(status_code=http_status, detail=error_response)


def _log_api_error(error: PresentationError, endpoint: str, user_id: str, **context):
    """Log API errors with context for monitoring."""
    logger.error(
        f"API error in {endpoint}: {error.code.value}",
        extra={
            "endpoint": endpoint,
            "user_id": user_id,
            "error_code": error.code.value,
            "error_details": error.technical_message,
            "context": context,
        },
    )


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

    try:
        service.presentation_repo.add_export_asset(
            presentation_id=presentation.id,
            export_asset=export_asset,
        )
    except TypeError as exc:
        if "datetime" in str(exc).lower() and "json serializable" in str(exc).lower():
            # This is the datetime serialization error - try to fix it by re-serializing the export asset
            logger.error(
                "DateTime serialization error for export asset, attempting to fix: %s",
                exc,
            )
            # Create a new export asset with proper datetime serialization
            try:
                from backend.repositories.presentation_repository import DateTimeEncoder

                # Re-serialize the export asset to ensure proper datetime handling
                export_asset_dict = service.presentation_repo._serialize_export_asset(
                    export_asset
                )
                # Create a new PresentationExport with serialized datetime
                from backend.lessons.presentation_schema import PresentationExport

                fixed_asset = PresentationExport(
                    format=export_asset_dict["format"],
                    url_or_path=export_asset_dict["url_or_path"],
                    generated_at=export_asset_dict[
                        "generated_at"
                    ],  # This is now a string
                    file_size_bytes=export_asset_dict["file_size_bytes"],
                )
                # Try again with the fixed asset
                service.presentation_repo.add_export_asset(
                    presentation_id=presentation.id,
                    export_asset=fixed_asset,
                )
                logger.info(
                    "Successfully fixed datetime serialization issue for export asset"
                )
                export_asset = fixed_asset
            except Exception as fix_exc:
                logger.error(
                    "Failed to fix datetime serialization: %s",
                    fix_exc,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to serialize export asset datetime fields: {str(fix_exc)}",
                ) from fix_exc
        else:
            raise

    return export_asset


# Request/Response models
class PresentationGenerateRequest(CamelModel):
    """Request to generate a presentation."""

    lesson_id: str = Field(
        ..., description="ID of the lesson to generate presentation for"
    )
    style: str = Field(default="default", description="Presentation style")
    use_llm_polish: bool = Field(
        default=True, description="Whether to use LLM polishing"
    )
    timeout_seconds: int = Field(default=30, description="Timeout for LLM operations")
    priority: str = Field(
        default="normal", description="Job priority (low, normal, high, urgent)"
    )
    max_retries: int = Field(default=2, description="Maximum number of retry attempts")


class PresentationGenerateResponse(CamelModel):
    """Response for presentation generation request."""

    job_id: str = Field(..., description="Job ID for tracking generation progress")
    status: str = Field(..., description="Initial job status")
    message: str = Field(..., description="Status message")


class PresentationStatusResponse(CamelModel):
    """Response for presentation status query."""

    job_id: str
    status: str
    priority: str
    lesson_id: str
    progress: int
    message: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    presentation_id: Optional[str] = None
    slide_count: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    max_retries: int
    processing_time_seconds: Optional[float] = None
    style: str
    use_llm_polish: bool


class JobListRequest(CamelModel):
    """Request for listing jobs with filtering."""

    status: Optional[str] = None
    priority: Optional[str] = None
    include_finished: bool = True
    limit: int = 20


class JobBulkRequest(CamelModel):
    """Request for bulk job operations."""

    job_ids: List[str] = Field(..., description="List of job IDs to operate on")


class JobRetryRequest(CamelModel):
    """Request to retry a failed job."""

    force_retry: bool = Field(
        default=False, description="Force retry even if max retries exceeded"
    )


class PresentationResponse(CamelModel):
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
    title: Optional[str] = None
    description: Optional[str] = None
    total_slides: Optional[int] = None
    total_duration_minutes: Optional[int] = None
    is_stale: Optional[bool] = None


class PresentationDetailResponse(PresentationResponse):
    """Detailed presentation response with slides."""

    slides: List[Dict[str, Any]]
    export_assets: List[Dict[str, Any]]


class ExportJobResponse(CamelModel):
    """Response containing export job status."""

    job_id: str
    presentation_id: str
    format: str
    status: str
    progress: int
    message: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    file_url: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[float] = None


class ExportStatsResponse(CamelModel):
    """Response containing export service statistics."""

    total_jobs: int
    pending_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    cancelled_jobs: int
    success_rate: float
    avg_processing_time: Optional[float] = None
    oldest_job_age_minutes: Optional[float] = None


@router.post("/generate", response_model=PresentationGenerateResponse)
async def generate_presentation(
    request: PresentationGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> PresentationGenerateResponse:
    """Generate a presentation for a lesson asynchronously."""
    try:
        # Validate request parameters
        if not request.lesson_id or not isinstance(request.lesson_id, str):
            raise PresentationError.validation_failed("lesson_id", request.lesson_id)

        # Validate style using style service
        try:
            from backend.services.style_service import StyleService

            style_service = StyleService()
            style_service.validate_and_apply_style(request.style, current_user.id)
        except Exception as style_error:
            raise PresentationError.invalid_style(str(style_error))

        if (
            not isinstance(request.timeout_seconds, int)
            or request.timeout_seconds < 1
            or request.timeout_seconds > 300
        ):
            raise PresentationError.validation_failed(
                "timeout_seconds", request.timeout_seconds
            )

        # Validate priority
        if request.priority not in [p.value for p in JobPriority]:
            raise PresentationError.validation_failed("priority", request.priority)

        # Validate max_retries
        if (
            not isinstance(request.max_retries, int)
            or request.max_retries < 0
            or request.max_retries > 10
        ):
            raise PresentationError.validation_failed(
                "max_retries", request.max_retries
            )

        # Verify user has access to the lesson
        lesson_repo = LessonRepository()
        try:
            lesson = lesson_repo.get_lesson(request.lesson_id)
            if not lesson:
                raise PresentationError.lesson_not_found(request.lesson_id)

            if lesson.user_id != current_user.id:
                logger.warning(
                    "Lesson access denied during presentation generation: lesson_user_id=%s request_user_id=%s",
                    getattr(lesson, "user_id", None),
                    current_user.id,
                )
                raise PresentationError.lesson_access_denied(request.lesson_id)

        except PresentationError:
            raise
        except Exception as e:
            error = create_error_from_exception(e, {"operation": "lesson_access_check"})
            raise error

        # Create background job
        try:
            job_id = create_presentation_job(
                lesson_id=request.lesson_id,
                user_id=current_user.id,
                style=request.style,
                use_llm_polish=request.use_llm_polish,
                timeout_seconds=request.timeout_seconds,
                priority=JobPriority(request.priority),
                max_retries=request.max_retries,
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

            logger.info(
                f"Started presentation generation job {job_id} for lesson {request.lesson_id} by user {current_user.id}"
            )

            return PresentationGenerateResponse(
                job_id=job_id,
                status="pending",
                message="Presentation generation started",
            )

        except PresentationError:
            raise
        except Exception as e:
            error = create_error_from_exception(
                e,
                {
                    "operation": "create_background_job",
                    "lesson_id": request.lesson_id,
                    "user_id": current_user.id,
                },
            )
            raise error

    except PresentationError as e:
        _log_api_error(
            e, "generate_presentation", current_user.id, request=request.dict()
        )
        raise _handle_presentation_error(e)
    except Exception as e:
        error = create_error_from_exception(
            e,
            {
                "operation": "generate_presentation",
                "user_id": current_user.id,
            },
        )
        _log_api_error(error, "generate_presentation", current_user.id)
        raise _handle_presentation_error(error)


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusEnvelope,
    responses={
        200: {
            "description": "Successfully retrieved job status with standardized envelope",
            "content": {
                "application/json": {
                    "example": {
                        "status": "running",
                        "progress": {
                            "completion_percentage": 75,
                            "step": "Generating slides",
                            "slide_count": 12,
                            "processing_time_seconds": 45,
                            "retry_count": 0,
                            "max_retries": 2,
                        },
                        "retry_after": None,
                        "error": None,
                        "meta": {
                            "job_id": "abc-123",
                            "lesson_id": "lesson-456",
                            "priority": "normal",
                            "style": "modern",
                            "use_llm_polish": True,
                            "created_at": "2025-11-16T10:25:00Z",
                            "started_at": "2025-11-16T10:26:00Z",
                        },
                        "timestamp": "2025-11-16T10:30:00Z",
                    }
                }
            },
        },
        404: {"description": "Job not found", "model": dict},
        403: {"description": "Access denied to job", "model": dict},
    },
    summary="Get presentation job status with standardized envelope",
    description="Retrieves the current status of a presentation generation job using the harmonized job status envelope format. Includes progress information, retry recommendations, and standardized error handling.",
)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
) -> JobStatusEnvelope:
    """Get the status of a presentation generation job with standardized envelope."""
    try:
        # Validate job_id
        if not job_id or not isinstance(job_id, str):
            raise PresentationError.validation_failed("job_id", job_id)

        # Get job status
        try:
            job_status = get_presentation_job_status(job_id)
            if not job_status:
                raise PresentationError.job_not_found(job_id)
        except PresentationError:
            raise
        except Exception as e:
            error = create_error_from_exception(
                e, {"operation": "get_job_status", "job_id": job_id}
            )
            raise error

        # Verify job belongs to current user
        try:
            job_manager = get_job_manager()
            job = job_manager.get_job(job_id)

            if not job or job.user_id != current_user.id:
                raise PresentationError.job_access_denied(job_id)

        except PresentationError:
            raise
        except Exception as e:
            error = create_error_from_exception(
                e, {"operation": "job_access_check", "job_id": job_id}
            )
            raise error

        # Create standardized job status envelope
        job_status_response = PresentationStatusResponse(**job_status)

        # Map status and progress information to standardized format
        status = job_status_response.status
        progress = {
            "completion_percentage": job_status_response.progress,
            "step": job_status_response.message,
            "slide_count": job_status_response.slide_count,
            "presentation_id": job_status_response.presentation_id,
            "processing_time_seconds": job_status_response.processing_time_seconds,
            "retry_count": job_status_response.retry_count,
            "max_retries": job_status_response.max_retries,
        }

        error = None
        if job_status_response.error_code or job_status_response.error_message:
            error = {
                "code": job_status_response.error_code,
                "message": job_status_response.error_message,
                "retry_recommended": job_status_response.status == "failed"
                and job_status_response.retry_count < job_status_response.max_retries,
            }

        retry_after = None
        if status == "failed" and error and error["retry_recommended"]:
            retry_after = 30  # Default 30 seconds for failed jobs

        return create_job_status_envelope(
            status=status,
            progress=progress,
            retry_after=retry_after,
            error=error,
            meta={
                "job_id": job_status_response.job_id,
                "lesson_id": job_status_response.lesson_id,
                "priority": job_status_response.priority,
                "style": job_status_response.style,
                "use_llm_polish": job_status_response.use_llm_polish,
                "created_at": job_status_response.created_at,
                "started_at": job_status_response.started_at,
                "completed_at": job_status_response.completed_at,
            },
        )

    except PresentationError as e:
        _log_api_error(e, "get_job_status", current_user.id, job_id=job_id)
        raise _handle_presentation_error(e)
    except Exception as e:
        error = create_error_from_exception(
            e,
            {
                "operation": "get_job_status",
                "job_id": job_id,
                "user_id": current_user.id,
            },
        )
        _log_api_error(error, "get_job_status", current_user.id)
        raise _handle_presentation_error(error)


@router.get("/jobs", response_model=List[PresentationStatusResponse])
async def list_user_jobs(
    status: Optional[str] = Query(default=None, description="Filter by job status"),
    priority: Optional[str] = Query(default=None, description="Filter by job priority"),
    include_finished: bool = Query(default=True, description="Include finished jobs"),
    limit: int = Query(
        default=20, le=100, description="Maximum number of jobs to return"
    ),
    current_user: User = Depends(get_current_user),
) -> List[PresentationStatusResponse]:
    """List presentation jobs for the current user with filtering options."""

    job_manager = get_job_manager()

    # Parse status filter
    status_filter = None
    if status:
        try:
            status_filter = JobStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}. Valid values: {[s.value for s in JobStatus]}",
            )

    # Parse priority filter
    jobs = job_manager.get_user_jobs(
        user_id=current_user.id,
        limit=limit,
        status=status_filter,
        include_finished=include_finished,
    )

    # Filter by priority if specified
    if priority:
        jobs = [job for job in jobs if job.priority.value == priority]

    return [
        PresentationStatusResponse(**job_manager.get_job_status(job.id)) for job in jobs
    ]


@router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    reason: str = Query(
        default="User cancelled", description="Reason for cancellation"
    ),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Cancel a pending or running presentation generation job."""

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

    success = job_manager.cancel_job(job_id, reason)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job cannot be cancelled (may have already completed)",
        )

    return {"message": "Job cancelled successfully", "job_id": job_id, "reason": reason}


@router.post("/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    request: JobRetryRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Retry a failed presentation generation job."""

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

    # Force retry by temporarily increasing max_retries if needed
    if request.force_retry and job.retry_count >= job.max_retries:
        # Update the job to allow one more retry
        job.max_retries = job.retry_count + 1
        job_manager.job_repository.update_job(job)

    success = job_manager.retry_job(job_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job cannot be retried (no retries available or not in failed state)",
        )

    return {"message": "Job queued for retry", "job_id": job_id}


@router.delete("/jobs/cleanup")
async def cleanup_old_jobs(
    max_age_hours: int = Query(
        default=24, ge=1, le=168, description="Maximum age in hours"
    ),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Clean up old completed/failed jobs (admin only or user's own jobs)."""

    job_manager = get_job_manager()

    # For now, allow users to cleanup their own jobs
    # In a production system, this might be admin-only
    try:
        # Note: This cleans up all old jobs, not just the user's jobs
        # For user-specific cleanup, we'd need to modify the repository
        deleted_count = job_manager.cleanup_old_jobs(max_age_hours=max_age_hours)

        return {
            "message": "Job cleanup completed",
            "deleted_jobs": deleted_count,
            "max_age_hours": max_age_hours,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup old jobs: {str(e)}",
        )


@router.post("/jobs/bulk-cancel")
async def bulk_cancel_jobs(
    request: JobBulkRequest,
    reason: str = Query(
        default="Bulk cancellation", description="Reason for cancellation"
    ),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Cancel multiple jobs at once."""

    job_manager = get_job_manager()
    cancelled_jobs = []
    failed_jobs = []

    for job_id in request.job_ids:
        try:
            # Verify job ownership
            job = job_manager.get_job(job_id)
            if not job:
                failed_jobs.append({"job_id": job_id, "error": "Job not found"})
                continue

            if job.user_id != current_user.id:
                failed_jobs.append({"job_id": job_id, "error": "Access denied"})
                continue

            success = job_manager.cancel_job(job_id, reason)
            if success:
                cancelled_jobs.append(job_id)
            else:
                failed_jobs.append(
                    {"job_id": job_id, "error": "Job cannot be cancelled"}
                )
        except Exception as e:
            failed_jobs.append({"job_id": job_id, "error": str(e)})

    return {
        "message": f"Bulk cancellation completed",
        "cancelled_jobs": cancelled_jobs,
        "failed_jobs": failed_jobs,
        "total_requested": len(request.job_ids),
        "total_cancelled": len(cancelled_jobs),
    }


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
            **presentation_service._build_presentation_metadata(p),
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
        **presentation_service._build_presentation_metadata(presentation),
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
        # Generate content directly without saving to database to avoid serialization issues
        pass  # We'll generate content inline below

    # Generate content
    if format == "json":
        content = json.dumps(
            {
                "presentation": presentation.model_dump(mode="json"),
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
        # Generate PPTX on demand if no export asset exists
        if not export_asset:
            export_asset = presentation_service._create_pptx_export(presentation)

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
        # Generate PDF on demand if no export asset exists
        if not export_asset:
            export_asset = presentation_service._create_pdf_export(presentation)

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


# Export status endpoints
@router.get("/{presentation_id}/export-status", response_model=List[ExportJobResponse])
async def get_presentation_export_jobs(
    presentation_id: str,
    current_user: User = Depends(get_current_user),
) -> List[ExportJobResponse]:
    """Get all export jobs for a specific presentation."""
    try:
        # Validate presentation_id
        if not presentation_id or not isinstance(presentation_id, str):
            raise PresentationError.validation_failed(
                "presentation_id", presentation_id
            )

        # Verify user has access to the presentation
        presentation_service = PresentationService()
        presentation = presentation_service.get_presentation(
            presentation_id, current_user.id
        )

        if not presentation:
            raise PresentationError.lesson_not_found(presentation_id)

        # Get export jobs for the presentation
        try:
            export_jobs = export_status_service.get_jobs_for_presentation(
                presentation_id
            )
        except Exception as e:
            logger.error(
                f"Failed to get export jobs for presentation {presentation_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve export jobs",
            )

        # Convert to response models
        return [
            ExportJobResponse(
                job_id=job.job_id,
                presentation_id=job.presentation_id,
                format=job.format.value
                if hasattr(job.format, "value")
                else str(job.format),
                status=job.status.value
                if hasattr(job.status, "value")
                else str(job.status),
                progress=job.progress,
                message=job.message,
                created_at=job.created_at.isoformat() if job.created_at else "",
                started_at=job.started_at.isoformat() if job.started_at else None,
                completed_at=job.completed_at.isoformat() if job.completed_at else None,
                file_url=job.file_url,
                error_code=job.error_code,
                error_message=job.error_message,
                processing_time_seconds=job.processing_time_seconds,
            )
            for job in export_jobs
        ]

    except PresentationError as e:
        _log_api_error(
            e,
            "get_presentation_export_jobs",
            current_user.id,
            presentation_id=presentation_id,
        )
        raise _handle_presentation_error(e)
    except Exception as e:
        logger.error(f"Unexpected error in get_presentation_export_jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/export-status/{job_id}", response_model=ExportJobResponse)
async def get_export_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
) -> ExportJobResponse:
    """Get the status of a specific export job."""
    try:
        # Validate job_id
        if not job_id or not isinstance(job_id, str):
            raise PresentationError.validation_failed("job_id", job_id)

        # Get export job status
        try:
            export_job = export_status_service.get_job_status(job_id)
            if not export_job:
                raise PresentationError.job_not_found(job_id)
        except PresentationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get export job status for {job_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve export job status",
            )

        # Verify user has access to the presentation
        presentation_service = PresentationService()
        presentation = presentation_service.get_presentation(
            export_job.presentation_id, current_user.id
        )

        if not presentation:
            raise PresentationError.lesson_access_denied(export_job.presentation_id)

        return ExportJobResponse(
            job_id=export_job.job_id,
            presentation_id=export_job.presentation_id,
            format=export_job.format.value
            if hasattr(export_job.format, "value")
            else str(export_job.format),
            status=export_job.status.value
            if hasattr(export_job.status, "value")
            else str(export_job.status),
            progress=export_job.progress,
            message=export_job.message,
            created_at=export_job.created_at.isoformat()
            if export_job.created_at
            else "",
            started_at=export_job.started_at.isoformat()
            if export_job.started_at
            else None,
            completed_at=export_job.completed_at.isoformat()
            if export_job.completed_at
            else None,
            file_url=export_job.file_url,
            error_code=export_job.error_code,
            error_message=export_job.error_message,
            processing_time_seconds=export_job.processing_time_seconds,
        )

    except PresentationError as e:
        _log_api_error(e, "get_export_job_status", current_user.id, job_id=job_id)
        raise _handle_presentation_error(e)
    except Exception as e:
        logger.error(f"Unexpected error in get_export_job_status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete("/export-status/{job_id}")
async def cancel_export_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Cancel an export job."""
    try:
        # Validate job_id
        if not job_id or not isinstance(job_id, str):
            raise PresentationError.validation_failed("job_id", job_id)

        # First get the job to verify access
        try:
            export_job = export_status_service.get_job_status(job_id)
            if not export_job:
                raise PresentationError.job_not_found(job_id)
        except PresentationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get export job for cancellation {job_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve export job",
            )

        # Verify user has access to the presentation
        presentation_service = PresentationService()
        presentation = presentation_service.get_presentation(
            export_job.presentation_id, current_user.id
        )

        if not presentation:
            raise PresentationError.lesson_access_denied(export_job.presentation_id)

        # Cancel the job
        try:
            success = export_status_service.cancel_job(job_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Export job cannot be cancelled (may have already completed)",
                )
        except Exception as e:
            logger.error(f"Failed to cancel export job {job_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel export job",
            )

        logger.info(f"Export job {job_id} cancelled by user {current_user.id}")
        return {"message": "Export job cancelled successfully", "job_id": job_id}

    except PresentationError as e:
        _log_api_error(e, "cancel_export_job", current_user.id, job_id=job_id)
        raise _handle_presentation_error(e)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in cancel_export_job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/export-status/stats", response_model=ExportStatsResponse)
async def get_export_statistics(
    current_user: User = Depends(get_current_user),
) -> ExportStatsResponse:
    """Get export service statistics."""
    try:
        # Get global export statistics
        try:
            stats = export_status_service.get_statistics()
        except Exception as e:
            logger.error(f"Failed to get export statistics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve export statistics",
            )

        # Convert to response model
        return ExportStatsResponse(
            total_jobs=stats.get("total_jobs", 0),
            pending_jobs=stats.get("pending_jobs", 0),
            running_jobs=stats.get("running_jobs", 0),
            completed_jobs=stats.get("completed_jobs", 0),
            failed_jobs=stats.get("failed_jobs", 0),
            cancelled_jobs=stats.get("cancelled_jobs", 0),
            success_rate=stats.get("success_rate", 0.0),
            avg_processing_time=stats.get("avg_processing_time"),
            oldest_job_age_minutes=stats.get("oldest_job_age_minutes"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_export_statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Job monitoring and health endpoints
@router.get("/jobs/health")
async def get_job_health_metrics(
    hours: int = Query(
        default=24, ge=1, le=168, description="Time window in hours for statistics"
    ),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get health metrics and statistics for the presentation job system."""

    try:
        job_manager = get_job_manager()
        metrics = job_manager.get_job_health_metrics()

        # Get user-specific metrics
        user_jobs = job_manager.get_user_jobs(current_user.id, limit=1000)
        user_stats = {
            "total_user_jobs": len(user_jobs),
            "user_pending_jobs": len(
                [j for j in user_jobs if j.status == JobStatus.PENDING]
            ),
            "user_running_jobs": len(
                [j for j in user_jobs if j.status == JobStatus.RUNNING]
            ),
            "user_completed_jobs": len(
                [j for j in user_jobs if j.status == JobStatus.COMPLETED]
            ),
            "user_failed_jobs": len(
                [j for j in user_jobs if j.status == JobStatus.FAILED]
            ),
        }

        # Calculate user-specific rates
        if user_stats["total_user_jobs"] > 0:
            user_stats["user_success_rate"] = (
                user_stats["user_completed_jobs"] / user_stats["total_user_jobs"]
            ) * 100
            user_stats["user_failure_rate"] = (
                user_stats["user_failed_jobs"] / user_stats["total_user_jobs"]
            ) * 100
        else:
            user_stats["user_success_rate"] = 0
            user_stats["user_failure_rate"] = 0

        metrics.update(user_stats)

        return metrics

    except Exception as e:
        logger.error(f"Failed to get job health metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job health metrics: {str(e)}",
        )


@router.get("/jobs/statistics")
async def get_job_statistics(
    hours: int = Query(
        default=24, ge=1, le=168, description="Time window in hours for statistics"
    ),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get detailed job statistics for monitoring and analytics."""

    try:
        job_manager = get_job_manager()
        repository = job_manager.job_repository

        # Get comprehensive statistics
        stats = repository.get_job_statistics(hours=hours)

        # Add performance insights
        if stats.get("avg_processing_time"):
            if stats["avg_processing_time"] > 300:  # > 5 minutes
                stats["performance_warning"] = "Average processing time is high"
            elif stats["avg_processing_time"] > 120:  # > 2 minutes
                stats["performance_warning"] = "Average processing time is elevated"

        # Add queue health indicators
        if stats.get("oldest_pending_job_age_minutes"):
            if stats["oldest_pending_job_age_minutes"] > 30:
                stats["queue_warning"] = "Oldest pending job is very old"
            elif stats["oldest_pending_job_age_minutes"] > 10:
                stats["queue_warning"] = "Oldest pending job is getting old"

        # Add failure rate alerts
        if stats.get("failure_rate", 0) > 20:
            stats["failure_alert"] = "High failure rate detected"
        elif stats.get("failure_rate", 0) > 10:
            stats["failure_alert"] = "Elevated failure rate detected"

        return stats

    except Exception as e:
        logger.error(f"Failed to get job statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job statistics: {str(e)}",
        )


@router.post("/jobs/system/recovery")
async def trigger_job_recovery(
    timeout_minutes: int = Query(
        default=30,
        ge=5,
        le=120,
        description="Timeout in minutes for orphaned job detection",
    ),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Trigger recovery of orphaned jobs (admin or system operation)."""

    # For now, allow any authenticated user to trigger recovery
    # in production, this might be admin-only
    try:
        job_manager = get_job_manager()
        repository = job_manager.job_repository

        recovered_count = repository.recover_orphaned_jobs(
            timeout_minutes=timeout_minutes
        )

        return {
            "message": "Job recovery completed",
            "recovered_jobs": recovered_count,
            "timeout_minutes": timeout_minutes,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to trigger job recovery: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job recovery failed: {str(e)}",
        )


# WebSocket endpoints for real-time progress
@router.websocket("/progress/ws")
async def websocket_progress_updates(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates."""
    websocket_manager = get_websocket_manager()
    user_id = None

    try:
        # Accept connection and get authentication
        await websocket.accept()

        # Get user ID from query parameter (in production, use proper auth)
        query_params = websocket.query_params
        user_id = query_params.get("user_id")

        if not user_id:
            await websocket.send_json(
                {"type": "error", "message": "user_id parameter is required"}
            )
            await websocket.close(code=4001)
            return

        # Connect to WebSocket manager
        connected = await websocket_manager.connect(websocket, user_id)
        if not connected:
            await websocket.close(code=4002)
            return

        logger.info(f"WebSocket connection established for user {user_id}")

        # Send initial connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "stats": websocket_manager.get_connection_stats(),
            }
        )

        # Handle incoming messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_json()
                message_type = data.get("type")

                # Handle different message types
                if message_type == "subscribe_job":
                    job_id = data.get("job_id")
                    if job_id:
                        success = websocket_manager.subscribe_to_job(user_id, job_id)
                        await websocket.send_json(
                            {
                                "type": "subscription_result",
                                "job_id": job_id,
                                "success": success,
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )

                elif message_type == "unsubscribe_job":
                    job_id = data.get("job_id")
                    if job_id:
                        websocket_manager.unsubscribe_from_job(user_id, job_id)
                        await websocket.send_json(
                            {
                                "type": "unsubscription_result",
                                "job_id": job_id,
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )

                elif message_type == "ping":
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                    )

                elif message_type == "get_stats":
                    stats = websocket_manager.get_connection_stats()
                    await websocket.send_json(
                        {
                            "type": "stats",
                            "stats": stats,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                else:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": f"Unknown message type: {message_type}",
                        }
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(
                    f"Error handling WebSocket message for user {user_id}: {e}"
                )
                await websocket.send_json(
                    {"type": "error", "message": "Error processing message"}
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket connection error for user {user_id}: {e}")
    finally:
        # Clean up connection
        if user_id:
            websocket_manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket connection cleaned up for user {user_id}")


@router.post("/progress/subscribe")
async def subscribe_to_job_progress(
    job_id: str = Body(..., description="Job ID to subscribe to"),
    user_id: Optional[str] = Body(None, description="User ID (if not using WebSocket)"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Subscribe to job progress updates (falls back to polling if WebSocket not available)."""

    # Use authenticated user if user_id not provided
    user_id = user_id or current_user.id

    try:
        # Verify job belongs to user
        job_manager = get_job_manager()
        job = job_manager.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        websocket_manager = get_websocket_manager()

        # In a real implementation, you'd store this subscription for future use
        # For now, just confirm the subscription would work
        return {
            "message": "Subscription setup complete",
            "job_id": job_id,
            "user_id": user_id,
            "websocket_url": f"/api/presentations/progress/ws?user_id={user_id}",
            "polling_endpoint": f"/api/presentations/jobs/{job_id}",
            "current_status": job.to_status_dict(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set up progress subscription for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set up progress subscription",
        )


@router.get("/progress/connections/stats")
async def get_connection_stats(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get WebSocket connection statistics (for monitoring)."""

    try:
        websocket_manager = get_websocket_manager()
        stats = websocket_manager.get_connection_stats()

        return {"stats": stats, "timestamp": datetime.utcnow().isoformat()}

    except Exception as e:
        logger.error(f"Failed to get connection stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get connection statistics",
        )


@router.post("/progress/connections/cleanup")
async def cleanup_connections(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Clean up inactive WebSocket connections."""

    try:
        websocket_manager = get_websocket_manager()
        cleaned_count = await websocket_manager.cleanup_inactive_connections()

        return {
            "message": "Connection cleanup completed",
            "cleaned_connections": cleaned_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to cleanup connections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup connections",
        )
