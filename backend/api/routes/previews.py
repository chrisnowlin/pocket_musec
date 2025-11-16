"""Presentation preview API endpoints.

Provides basic CRUD-like operations for presentation previews:
- Retrieve a preview by presentation ID.
- Generate a preview for a presentation (optional style ID).
- List previews for the current user with pagination.
- Delete a preview.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel

from ..dependencies import get_current_user
from backend.auth import User
from backend.services.preview_service import PreviewService
from backend.services.presentation_errors import PresentationError, PresentationErrorCode, create_error_from_exception
from backend.models.preview_schema import PresentationPreview

router = APIRouter(prefix="/api/previews", tags=["previews"])
logger = logging.getLogger(__name__)


def _handle_preview_error(error: PresentationError) -> HTTPException:
    """Map PresentationError to an appropriate HTTPException."""
    status_code_map = {
        PresentationErrorCode.LESSON_NOT_FOUND: status.HTTP_404_NOT_FOUND,
        PresentationErrorCode.LESSON_ACCESS_DENIED: status.HTTP_403_FORBIDDEN,
        PresentationErrorCode.VALIDATION_FAILED: status.HTTP_400_BAD_REQUEST,
        PresentationErrorCode.INVALID_STYLE: status.HTTP_400_BAD_REQUEST,
        PresentationErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    http_status = status_code_map.get(error.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(
        status_code=http_status,
        detail={"error": error.to_dict(), "timestamp": datetime.utcnow().isoformat()},
    )


def _log_api_error(error: PresentationError, endpoint: str, user_id: str, **context):
    """Log errors with useful context for debugging/monitoring."""
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


@router.get("/{presentation_id}", response_model=PresentationPreview)
async def get_preview(
    presentation_id: str,
    current_user: User = Depends(get_current_user),
) -> PresentationPreview:
    """Retrieve preview for a given presentation ID.

    Returns a :class:`PresentationPreview` model. Raises 404 if not found.
    """
    try:
        if not presentation_id:
            raise PresentationError.validation_failed("presentation_id", presentation_id)
        preview_service = PreviewService()
        preview = preview_service.get_preview(presentation_id, current_user.id)
        if not preview:
            raise PresentationError.validation_failed("presentation_id", presentation_id)
        return preview
    except PresentationError as e:
        _log_api_error(e, "get_preview", current_user.id, presentation_id=presentation_id)
        raise _handle_preview_error(e)
    except Exception as e:
        err = create_error_from_exception(
            e, {"operation": "get_preview", "presentation_id": presentation_id, "user_id": current_user.id}
        )
        _log_api_error(err, "get_preview", current_user.id)
        raise _handle_preview_error(err)


class GeneratePreviewBody(BaseModel):
    """Optional request body for preview generation.

    ``style_id`` is optional and, if provided, will be used when generating the preview.
    """

    style_id: Optional[str] = None


@router.post("/{presentation_id}", response_model=PresentationPreview)
async def generate_preview(
    presentation_id: str,
    body: GeneratePreviewBody = Body(...),
    current_user: User = Depends(get_current_user),
) -> PresentationPreview:
    """Generate a preview for a presentation.

    Accepts an optional JSON body with ``style_id``.
    """
    try:
        if not presentation_id:
            raise PresentationError.validation_failed("presentation_id", presentation_id)
        preview_service = PreviewService()
        preview = preview_service.generate_preview(presentation_id, style_id=body.style_id)
        return preview
    except PresentationError as e:
        _log_api_error(e, "generate_preview", current_user.id, presentation_id=presentation_id)
        raise _handle_preview_error(e)
    except Exception as e:
        err = create_error_from_exception(
            e, {"operation": "generate_preview", "presentation_id": presentation_id, "user_id": current_user.id}
        )
        _log_api_error(err, "generate_preview", current_user.id)
        raise _handle_preview_error(err)


@router.get("/", response_model=List[PresentationPreview])
async def list_user_previews(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
) -> List[PresentationPreview]:
    """List previews for the current user with pagination.

    ``limit`` and ``offset`` control the page size and start index.
    """
    try:
        preview_service = PreviewService()
        repo = preview_service.preview_repo
        previews = repo.list_previews(user_id=current_user.id, limit=limit, offset=offset)
        return previews
    except Exception as e:
        err = create_error_from_exception(
            e, {"operation": "list_user_previews", "user_id": current_user.id}
        )
        _log_api_error(err, "list_user_previews", current_user.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))


@router.delete("/{presentation_id}")
async def delete_preview(
    presentation_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Delete a preview.

    Returns a simple success message. 400 if the preview has been converted to a
    presentation; 404 if the preview does not exist.
    """
    try:
        if not presentation_id:
            raise PresentationError.validation_failed("presentation_id", presentation_id)
        preview_service = PreviewService()
        preview = preview_service.get_preview(presentation_id, current_user.id)
        if not preview:
            raise PresentationError.validation_failed("presentation_id", presentation_id)
        # Prevent deletion if linked to a full presentation
        if getattr(preview, "converted_to_presentation_id", None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete preview that has been converted to a presentation",
            )
        success = preview_service.preview_repo.delete_preview(presentation_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete preview",
            )
        return {"message": "Preview deleted successfully", "preview_id": presentation_id}
    except PresentationError as e:
        _log_api_error(e, "delete_preview", current_user.id, presentation_id=presentation_id)
        raise _handle_preview_error(e)
    except HTTPException:
        raise
    except Exception as e:
        err = create_error_from_exception(
            e, {"operation": "delete_preview", "presentation_id": presentation_id, "user_id": current_user.id}
        )
        _log_api_error(err, "delete_preview", current_user.id)
        raise _handle_preview_error(err)
