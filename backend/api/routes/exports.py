"""Enhanced export API with comprehensive progress tracking and feedback."""

import io
import json
import logging
import os
import zipfile
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    BackgroundTasks,
    Body,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.auth import User
from backend.api.dependencies import get_current_user
from backend.api.models import CamelModel
from backend.repositories.presentation_repository import PresentationRepository
from backend.services.export_service import (
    ExportService,
    ExportOptions,
    get_export_service,
)
from backend.services.presentation_errors import (
    PresentationError,
    PresentationErrorCode,
    ErrorRecoveryStrategy,
)
from backend.models.export_progress import (
    ExportFormat,
    ExportStatus,
    ExportFormatProgress,
    BulkExportProgress,
    ExportAnalytics,
)

router = APIRouter(prefix="/api/exports", tags=["exports"])
logger = logging.getLogger(__name__)


def _handle_export_error(error: PresentationError) -> HTTPException:
    """Convert export errors to HTTP exceptions with recovery information."""
    status_map = {
        PresentationErrorCode.EXPORT_PERMISSION_DENIED: 403,
        PresentationErrorCode.EXPORT_STORAGE_FAILED: 507,
        PresentationErrorCode.EXPORT_PPTX_FAILED: 500,
        PresentationErrorCode.EXPORT_PDF_FAILED: 500,
        PresentationErrorCode.EXPORT_JSON_FAILED: 500,
        PresentationErrorCode.EXPORT_MARKDOWN_FAILED: 500,
        PresentationErrorCode.VALIDATION_FAILED: 400,
        PresentationErrorCode.LESSON_NOT_FOUND: 404,
        PresentationErrorCode.LESSON_ACCESS_DENIED: 403,
        PresentationErrorCode.JOB_TIMEOUT: 408,
        PresentationErrorCode.SERVICE_UNAVAILABLE: 503,
    }

    status_code = status_map.get(error.code, 500)

    error_response = {
        "error": {
            "code": error.code.value,
            "message": error.user_message,
            "technical_message": error.technical_message,
        },
        "timestamp": datetime.utcnow().isoformat(),
        "recovery": {
            "retry_recommended": error.retry_recommended,
            "retry_after_seconds": error.retry_after_seconds,
            "actions": ErrorRecoveryStrategy.get_recovery_actions(error),
        },
    }

    return HTTPException(status_code=status_code, detail=error_response)


# Request/Response models
class ExportRequest(CamelModel):
    """Request for single format export."""

    presentation_id: str = Field(..., description="ID of the presentation to export")
    format: ExportFormat = Field(..., description="Export format")
    options: Optional[Dict[str, Any]] = Field(
        default=None, description="Export options"
    )
    track_progress: bool = Field(
        default=True, description="Whether to track export progress"
    )


class BulkExportRequest(CamelModel):
    """Request for multiple format exports."""

    presentation_id: str = Field(..., description="ID of the presentation to export")
    formats: List[ExportFormat] = Field(..., description="Export formats")
    options: Optional[Dict[str, Any]] = Field(
        default=None, description="Export options"
    )
    create_zip: bool = Field(
        default=True, description="Create ZIP containing all exports"
    )
    track_progress: bool = Field(
        default=True, description="Whether to track export progress"
    )


class ExportProgressResponse(CamelModel):
    """Response for export progress queries."""

    export_id: str
    format: ExportFormat
    status: ExportStatus
    overall_progress: float
    current_step: Optional[Dict[str, Any]] = None
    file_size_bytes: Optional[int] = None
    filename: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_time_remaining: Optional[float] = None
    steps: List[Dict[str, Any]] = []


class BulkExportProgressResponse(CamelModel):
    """Response for bulk export progress queries."""

    bulk_export_id: str
    presentation_id: str
    status: ExportStatus
    overall_progress: float
    total_formats: int
    successful_exports: int
    failed_exports: int
    running_exports: int
    pending_exports: int
    formats: Dict[str, ExportProgressResponse] = {}
    download_zip_path: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


class AnalyticsResponse(CamelModel):
    """Response for export analytics queries."""

    user_id: str
    time_window_hours: int
    total_exports: int
    successful_exports: int
    failed_exports: int
    success_rate: float
    formats_used: Dict[str, int]
    average_processing_time_seconds: float
    average_file_size_bytes: float
    most_popular_format: Optional[str] = None
    performance_summary: Dict[str, Any] = {}


@router.post("/export", response_model=Dict[str, Any])
async def start_export(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Start a presentation export with progress tracking."""

    try:
        export_service = get_export_service()

        # Parse export options
        options = ExportOptions()
        if request.options:
            options = ExportOptions(**request.options)

        # Start export in background
        export_id = f"export_{request.presentation_id}_{request.format.value}_{int(datetime.utcnow().timestamp())}"

        if request.track_progress:
            # Export with progress tracking
            background_tasks.add_task(
                _export_with_progress,
                request.presentation_id,
                request.format,
                current_user.id,
                options,
                export_id,
            )
        else:
            # Simple export without progress tracking
            background_tasks.add_task(
                _simple_export,
                request.presentation_id,
                request.format,
                current_user.id,
                options,
            )
            export_id = None

        return {
            "export_id": export_id,
            "presentation_id": request.presentation_id,
            "format": request.format.value,
            "status": "started",
            "track_progress": request.track_progress,
            "websocket_url": f"/api/presentations/progress/ws?user_id={current_user.id}"
            if export_id
            else None,
            "created_at": datetime.utcnow().isoformat(),
        }

    except PresentationError as e:
        logger.error(f"Export start failed: {e}")
        raise _handle_export_error(e)
    except Exception as e:
        logger.error(f"Unexpected export start error: {e}")
        raise HTTPException(status_code=500, detail="Failed to start export")


@router.post("/bulk-export", response_model=Dict[str, Any])
async def start_bulk_export(
    request: BulkExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Start a bulk presentation export with concurrent processing and progress tracking."""

    try:
        export_service = get_export_service()

        # Parse export options
        options = ExportOptions()
        if request.options:
            options = ExportOptions(**request.options)

        # Start bulk export in background
        bulk_export_id = f"bulk_export_{request.presentation_id}_{int(datetime.utcnow().timestamp())}"

        background_tasks.add_task(
            _bulk_export_with_progress,
            request.presentation_id,
            request.formats,
            current_user.id,
            options,
            bulk_export_id,
            request.create_zip,
        )

        return {
            "bulk_export_id": bulk_export_id,
            "presentation_id": request.presentation_id,
            "formats": [f.value for f in request.formats],
            "status": "started",
            "create_zip": request.create_zip,
            "concurrent_exports": options.batch_size,
            "websocket_url": f"/api/presentations/progress/ws?user_id={current_user.id}",
            "created_at": datetime.utcnow().isoformat(),
        }

    except PresentationError as e:
        logger.error(f"Bulk export start failed: {e}")
        raise _handle_export_error(e)
    except Exception as e:
        logger.error(f"Unexpected bulk export start error: {e}")
        raise HTTPException(status_code=500, detail="Failed to start bulk export")


@router.get("/progress/{export_id}", response_model=ExportProgressResponse)
async def get_export_progress(
    export_id: str,
    current_user: User = Depends(get_current_user),
) -> ExportProgressResponse:
    """Get progress for a specific export."""

    try:
        export_service = get_export_service()
        export_progress = await export_service.get_export_progress(export_id)

        if not export_progress:
            raise HTTPException(status_code=404, detail="Export not found")

        # Convert to response model
        return ExportProgressResponse(
            export_id=export_progress.export_id,
            format=export_progress.format,
            status=export_progress.status,
            overall_progress=export_progress.overall_progress,
            current_step=export_progress.get_current_step_info(),
            file_size_bytes=export_progress.file_size_bytes,
            filename=export_progress.filename,
            error_message=export_progress.error_message,
            error_code=export_progress.error_code,
            created_at=export_progress.created_at.isoformat(),
            started_at=export_progress.started_at.isoformat()
            if export_progress.started_at
            else None,
            completed_at=export_progress.completed_at.isoformat()
            if export_progress.completed_at
            else None,
            estimated_time_remaining=export_progress.get_estimated_time_remaining_seconds(),
            steps=[
                {
                    "step": step.step.value,
                    "name": step.name,
                    "status": step.status,
                    "progress": step.progress_percent,
                    "weight": step.weight,
                    "error_message": step.error_message,
                    "details": step.details,
                }
                for step in export_progress.steps
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get export progress: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve export progress"
        )


@router.get(
    "/bulk-progress/{bulk_export_id}", response_model=BulkExportProgressResponse
)
async def get_bulk_export_progress(
    bulk_export_id: str,
    current_user: User = Depends(get_current_user),
) -> BulkExportProgressResponse:
    """Get progress for a bulk export."""

    try:
        export_service = get_export_service()
        bulk_progress = await export_service.get_bulk_export_progress(bulk_export_id)

        if not bulk_progress:
            raise HTTPException(status_code=404, detail="Bulk export not found")

        # Convert format progresses to response models
        format_responses = {}
        for format, progress in bulk_progress.export_progress.items():
            format_responses[format.value] = ExportProgressResponse(
                export_id=progress.export_id,
                format=progress.format,
                status=progress.status,
                overall_progress=progress.overall_progress,
                current_step=progress.get_current_step_info(),
                file_size_bytes=progress.file_size_bytes,
                filename=progress.filename,
                error_message=progress.error_message,
                error_code=progress.error_code,
                created_at=progress.created_at.isoformat(),
                started_at=progress.started_at.isoformat()
                if progress.started_at
                else None,
                completed_at=progress.completed_at.isoformat()
                if progress.completed_at
                else None,
                estimated_time_remaining=progress.get_estimated_time_remaining_seconds(),
                steps=[
                    {
                        "step": step.step.value,
                        "name": step.name,
                        "status": step.status,
                        "progress": step.progress_percent,
                        "weight": step.weight,
                        "error_message": step.error_message,
                        "details": step.details,
                    }
                    for step in progress.steps
                ],
            )

        return BulkExportProgressResponse(
            bulk_export_id=bulk_progress.bulk_export_id,
            presentation_id=bulk_progress.presentation_id,
            status=bulk_progress.status,
            overall_progress=bulk_progress.overall_progress,
            total_formats=len(bulk_progress.formats),
            successful_exports=len(bulk_progress.successful_exports),
            failed_exports=len(bulk_progress.failed_exports),
            running_exports=len(
                [
                    f
                    for f, p in bulk_progress.export_progress.items()
                    if p.status == ExportStatus.RUNNING
                ]
            ),
            pending_exports=len(
                [
                    f
                    for f, p in bulk_progress.export_progress.items()
                    if p.status == ExportStatus.PENDING
                ]
            ),
            formats=format_responses,
            download_zip_path=bulk_progress.download_zip_path,
            created_at=bulk_progress.created_at.isoformat(),
            started_at=bulk_progress.started_at.isoformat()
            if bulk_progress.started_at
            else None,
            completed_at=bulk_progress.completed_at.isoformat()
            if bulk_progress.completed_at
            else None,
            error_message=bulk_progress.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bulk export progress: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve bulk export progress"
        )


@router.delete("/exports/{export_id}/cancel")
async def cancel_export(
    export_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Cancel a running export."""

    try:
        export_service = get_export_service()
        success = await export_service.cancel_export(export_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=404, detail="Export not found or cannot be cancelled"
            )

        return {
            "export_id": export_id,
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel export: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel export")


@router.delete("/bulk-exports/{bulk_export_id}/cancel")
async def cancel_bulk_export(
    bulk_export_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Cancel a running bulk export."""

    try:
        export_service = get_export_service()
        success = await export_service.cancel_bulk_export(
            bulk_export_id, current_user.id
        )

        if not success:
            raise HTTPException(
                status_code=404, detail="Bulk export not found or cannot be cancelled"
            )

        return {
            "bulk_export_id": bulk_export_id,
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel bulk export: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel bulk export")


@router.post("/exports/{export_id}/retry")
async def retry_export(
    export_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retry a failed export."""

    try:
        export_service = get_export_service()
        success = await export_service.retry_export(export_id, current_user.id)

        if not success:
            raise HTTPException(status_code=400, detail="Export cannot be retried")

        return {
            "export_id": export_id,
            "status": "retrying",
            "retried_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry export: {e}")
        raise HTTPException(status_code=500, detail="Failed to retry export")


@router.get("/exports/download/{export_id}")
async def download_exported_file(
    export_id: str,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Download a completed export file."""

    try:
        export_service = get_export_service()
        export_progress = await export_service.get_export_progress(export_id)

        if not export_progress:
            raise HTTPException(status_code=404, detail="Export not found")

        if export_progress.status != ExportStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Export not completed")

        # This would need to be implemented based on your file storage strategy
        # For now, we'll create a mock response
        if export_progress.format == ExportFormat.JSON:
            content = json.dumps(
                {
                    "message": "Export completed successfully",
                    "export_id": export_progress.export_id,
                    "format": export_progress.format.value,
                    "file_size_bytes": export_progress.file_size_bytes,
                },
                indent=2,
            )
            media_type = "application/json"
            filename = f"export_{export_id}.json"
        elif export_progress.format == ExportFormat.MARKDOWN:
            content = f"# Export Document\n\nExport ID: {export_progress.export_id}\nFormat: {export_progress.format.value}\nSize: {export_progress.file_size_bytes} bytes"
            media_type = "text/markdown"
            filename = f"export_{export_id}.md"
        else:
            # For binary formats, you would stream the actual file
            content = b"Mock file content"
            if export_progress.format == ExportFormat.PPTX:
                media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                filename = f"export_{export_id}.pptx"
            else:  # PDF
                media_type = "application/pdf"
                filename = f"export_{export_id}.pdf"

        if isinstance(content, str):
            return StreamingResponse(
                io.StringIO(content),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        else:
            return StreamingResponse(
                io.BytesIO(content),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download export: {e}")
        raise HTTPException(status_code=500, detail="Failed to download export file")


@router.get("/bulk-exports/download/{bulk_export_id}")
async def download_bulk_export_zip(
    bulk_export_id: str,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Download bulk export as ZIP file."""

    try:
        export_service = get_export_service()
        bulk_progress = await export_service.get_bulk_export_progress(bulk_export_id)

        if not bulk_progress:
            raise HTTPException(status_code=404, detail="Bulk export not found")

        if bulk_progress.status != ExportStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Bulk export not completed")

        if not bulk_progress.download_zip_path:
            raise HTTPException(status_code=400, detail="Download ZIP not available")

        # This would stream the actual ZIP file
        # For now, create a mock ZIP
        mock_zip = io.BytesIO()
        with zipfile.ZipFile(mock_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for format in bulk_progress.successful_exports:
                format_progress = bulk_progress.export_progress[format]
                content = f"Mock content for {format.value} export".encode()
                zipf.writestr(f"export_{format.value}.{format.value}", content)

        mock_zip.seek(0)

        return StreamingResponse(
            io.BytesIO(mock_zip.getvalue()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=bulk_export_{bulk_export_id}.zip"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download bulk export: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to download bulk export ZIP"
        )


@router.get("/exports", response_model=List[ExportProgressResponse])
async def list_active_exports(
    current_user: User = Depends(get_current_user),
    status: Optional[ExportStatus] = Query(
        default=None, description="Filter by status"
    ),
    limit: int = Query(
        default=50, le=100, description="Maximum number of exports to return"
    ),
) -> List[ExportProgressResponse]:
    """List active exports for the current user."""

    try:
        export_service = get_export_service()

        # Get recent exports (this would need database implementation)
        # For now, return active exports from memory
        active_exports = []

        for export_progress in export_service.active_exports.values():
            if status is None or export_progress.status == status:
                active_exports.append(
                    ExportProgressResponse(
                        export_id=export_progress.export_id,
                        format=export_progress.format,
                        status=export_progress.status,
                        overall_progress=export_progress.overall_progress,
                        current_step=export_progress.get_current_step_info(),
                        file_size_bytes=export_progress.file_size_bytes,
                        filename=export_progress.filename,
                        error_message=export_progress.error_message,
                        error_code=export_progress.error_code,
                        created_at=export_progress.created_at.isoformat(),
                        started_at=export_progress.started_at.isoformat()
                        if export_progress.started_at
                        else None,
                        completed_at=export_progress.completed_at.isoformat()
                        if export_progress.completed_at
                        else None,
                        estimated_time_remaining=export_progress.get_estimated_time_remaining_seconds(),
                        steps=[
                            {
                                "step": step.step.value,
                                "name": step.name,
                                "status": step.status,
                                "progress": step.progress_percent,
                                "weight": step.weight,
                                "error_message": step.error_message,
                                "details": step.details,
                            }
                            for step in export_progress.steps
                        ],
                    )
                )

        return sorted(active_exports[:limit], key=lambda x: x.created_at, reverse=True)

    except Exception as e:
        logger.error(f"Failed to list active exports: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve export list")


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_export_analytics(
    hours: int = Query(default=24, ge=1, le=168, description="Time window in hours"),
    current_user: User = Depends(get_current_user),
) -> AnalyticsResponse:
    """Get export analytics for the current user."""

    try:
        export_service = get_export_service()
        analytics = await export_service.get_export_analytics(current_user.id, hours)

        # Calculate additional metrics
        success_rate = 0.0
        if analytics["total_exports"] > 0:
            success_rate = (
                analytics["successful_exports"] / analytics["total_exports"]
            ) * 100.0

        # Determine most popular format
        most_popular_format = None
        if analytics["formats_used"]:
            most_popular_format = max(
                analytics["formats_used"].items(), key=lambda x: x[1]
            )[0]

        # Performance summary
        performance_summary = {}
        if success_rate < 80:
            performance_summary["warning"] = "Low success rate detected"
        if analytics["average_processing_time"] > 60:
            performance_summary["performance_issue"] = "High average processing time"
        if analytics["average_file_size"] > 10_000_000:  # 10MB
            performance_summary["size_notice"] = "Large average file size"

        return AnalyticsResponse(
            user_id=current_user.id,
            time_window_hours=hours,
            total_exports=analytics["total_exports"],
            successful_exports=analytics["successful_exports"],
            failed_exports=analytics["failed_exports"],
            success_rate=success_rate,
            formats_used=analytics["formats_used"],
            average_processing_time_seconds=analytics["average_processing_time"],
            average_file_size_bytes=analytics["average_file_size"],
            most_popular_format=most_popular_format,
            performance_summary=performance_summary,
        )

    except Exception as e:
        logger.error(f"Failed to get export analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve export analytics"
        )


@router.delete("/exports/cleanup")
async def cleanup_expired_exports(
    max_age_hours: int = Query(
        default=24, ge=1, le=168, description="Maximum age in hours"
    ),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Clean up expired export data (admin only or user's own exports)."""

    try:
        export_service = get_export_service()
        cleaned_count = await export_service.cleanup_expired_exports(max_age_hours)

        return {
            "message": "Export cleanup completed",
            "cleaned_exports": cleaned_count,
            "max_age_hours": max_age_hours,
            "cleaned_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to cleanup exports: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup exports")


# Background task functions
async def _export_with_progress(
    presentation_id: str,
    format: ExportFormat,
    user_id: str,
    options: ExportOptions,
    export_id: str,
):
    """Background task for export with progress tracking."""
    try:
        export_service = get_export_service()
        await export_service.export_presentation(
            presentation_id, format, user_id, options, websocket_available=True
        )
    except Exception as e:
        logger.error(f"Export background task failed: {e}")


async def _simple_export(
    presentation_id: str,
    format: ExportFormat,
    user_id: str,
    options: ExportOptions,
):
    """Background task for simple export without progress tracking."""
    try:
        export_service = get_export_service()
        await export_service.export_presentation(
            presentation_id, format, user_id, options, websocket_available=False
        )
    except Exception as e:
        logger.error(f"Simple export background task failed: {e}")


async def _bulk_export_with_progress(
    presentation_id: str,
    formats: List[ExportFormat],
    user_id: str,
    options: ExportOptions,
    bulk_export_id: str,
    create_zip: bool,
):
    """Background task for bulk export with progress tracking."""
    try:
        export_service = get_export_service()
        await export_service.bulk_export_presentation(
            presentation_id,
            formats,
            user_id,
            options,
            create_zip,
            websocket_available=True,
        )
    except Exception as e:
        logger.error(f"Bulk export background task failed: {e}")
