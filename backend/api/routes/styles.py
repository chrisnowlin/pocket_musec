"""Style management API endpoints for presentation generation."""

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
)
from pydantic import BaseModel, Field

from ..dependencies import get_current_user
from ..models import CamelModel
from backend.auth import User
from backend.services.style_service import (
    StyleService,
    StyleValidationError,
    StyleNotFoundError,
    StyleAccessDeniedError,
)
from backend.models.style_schema import (
    StyleConfig,
    StyleTemplate,
    ColorPalette,
    FontConfig,
    LayoutConfig,
    TransitionConfig,
    ColorScheme,
    FontFamily,
    LayoutType,
    SlideTransition,
)

router = APIRouter(prefix="/api/styles", tags=["styles"])
logger = logging.getLogger(__name__)


def _handle_style_error(error: Exception) -> HTTPException:
    """Convert style service errors to HTTP exceptions."""
    if isinstance(error, StyleValidationError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_failed", "message": str(error)},
        )
    elif isinstance(error, StyleNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "style_not_found", "message": str(error)},
        )
    elif isinstance(error, StyleAccessDeniedError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "access_denied", "message": str(error)},
        )
    else:
        logger.error(f"Unexpected style service error: {error}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Internal server error"},
        )


# Request/Response models
class StyleCreateRequest(CamelModel):
    """Request to create a new style."""

    name: str = Field(..., min_length=1, max_length=100, description="Style name")
    description: Optional[str] = Field(
        None, max_length=500, description="Style description"
    )
    template: Optional[StyleTemplate] = Field(
        None, description="Style template to base on"
    )
    config: Optional[Dict[str, Any]] = Field(
        None, description="Direct style configuration"
    )


class StyleUpdateRequest(CamelModel):
    """Request to update an existing style."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    colors: Optional[ColorPalette] = None
    fonts: Optional[FontConfig] = None
    layout: Optional[LayoutConfig] = None
    transitions: Optional[TransitionConfig] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    show_progress_indicator: Optional[bool] = None
    show_slide_numbers: Optional[bool] = None
    show_section_headers: Optional[bool] = None
    use_animations: Optional[bool] = None


class StyleResponse(CamelModel):
    """Response containing style information."""

    id: str
    name: str
    description: Optional[str]
    type: str
    user_id: Optional[str]
    is_public: bool
    is_active: bool
    color_scheme: str
    colors: Dict[str, str]
    fonts: Dict[str, Any]
    layout: Dict[str, Any]
    transitions: Dict[str, Any]
    show_progress_indicator: bool
    show_slide_numbers: bool
    show_section_headers: bool
    use_animations: bool
    created_at: str
    updated_at: str


class StyleListResponse(CamelModel):
    """Response for style list queries."""

    styles: List[StyleResponse]
    total: int
    page: int
    page_size: int


class StyleSearchRequest(CamelModel):
    """Request to search for styles."""

    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    search_type: str = Field(
        default="all", description="Search type: all, user, preset, public"
    )
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=50, description="Page size")


class StyleImportRequest(CamelModel):
    """Request to import a style configuration."""

    style_data: Dict[str, Any] = Field(..., description="Style configuration data")
    name: Optional[str] = Field(None, description="Override name")
    merge_with: Optional[str] = Field(None, description="Style ID to merge with")


class StyleCopyRequest(CamelModel):
    """Request to copy an existing style."""

    new_name: str = Field(
        ..., min_length=1, max_length=100, description="Name for the copied style"
    )


def _style_to_response(style: StyleConfig) -> StyleResponse:
    """Convert StyleConfig to response model."""
    return StyleResponse(
        id=style.id,
        name=style.name,
        description=style.description,
        type=style.type.value,
        user_id=style.user_id,
        is_public=style.is_public,
        is_active=style.is_active,
        color_scheme=style.color_scheme.value,
        colors=style.colors.to_dict(),
        fonts=style.fonts.to_dict(),
        layout=style.layout.to_dict(),
        transitions=style.transitions.to_dict(),
        show_progress_indicator=style.show_progress_indicator,
        show_slide_numbers=style.show_slide_numbers,
        show_section_headers=style.show_section_headers,
        use_animations=style.use_animations,
        created_at=style.created_at.isoformat(),
        updated_at=style.updated_at.isoformat(),
    )


# API endpoints
@router.get("/presets", response_model=List[Dict[str, Any]])
async def get_style_presets(
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get all available preset styles."""
    try:
        style_service = StyleService()
        presets = style_service.get_available_presets()
        return presets
    except Exception as e:
        logger.error(f"Failed to get style presets: {e}")
        raise _handle_style_error(e)


@router.get("/presets/{preset_id}", response_model=StyleResponse)
async def get_preset_style(
    preset_id: str, current_user: User = Depends(get_current_user)
) -> StyleResponse:
    """Get a specific preset style configuration."""
    try:
        style_service = StyleService()
        style = style_service.get_preset_style(preset_id)
        return _style_to_response(style)
    except Exception as e:
        logger.error(f"Failed to get preset style {preset_id}: {e}")
        raise _handle_style_error(e)


@router.get("/options", response_model=Dict[str, List[str]])
async def get_style_options(
    current_user: User = Depends(get_current_user),
) -> Dict[str, List[str]]:
    """Get available style options (color schemes, fonts, layouts, etc.)."""
    try:
        return {
            "color_schemes": ColorScheme.list_all(),
            "font_families": FontFamily.list_all(),
            "layout_types": LayoutType.list_all(),
            "slide_transitions": SlideTransition.list_all(),
        }
    except Exception as e:
        logger.error(f"Failed to get style options: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to get style options",
            },
        )


@router.post("/", response_model=StyleResponse)
async def create_style(
    request: StyleCreateRequest, current_user: User = Depends(get_current_user)
) -> StyleResponse:
    """Create a new style configuration."""
    try:
        # Validate request
        if request.template and request.config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "validation_failed",
                    "message": "Cannot provide both template and config",
                },
            )

        style_service = StyleService()
        style = style_service.create_style(
            name=request.name,
            description=request.description,
            config=request.config,
            user_id=current_user.id,
            template=request.template,
        )
        return _style_to_response(style)
    except Exception as e:
        logger.error(f"Failed to create style: {e}")
        raise _handle_style_error(e)


@router.get("/", response_model=StyleListResponse)
async def list_user_styles(
    include_public: bool = Query(default=True, description="Include public styles"),
    include_presets: bool = Query(default=True, description="Include preset styles"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
) -> StyleListResponse:
    """List styles available to the current user."""
    try:
        style_service = StyleService()
        styles, total = style_service.list_user_styles(
            user_id=current_user.id,
            include_public=include_public,
            include_presets=include_presets,
            page=page,
            page_size=page_size,
        )
        return StyleListResponse(
            styles=[_style_to_response(style) for style in styles],
            total=min(total, page_size * len(styles)),
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error(f"Failed to list user styles: {e}")
        raise _handle_style_error(e)


@router.post("/search", response_model=StyleListResponse)
async def search_styles(
    request: StyleSearchRequest, current_user: User = Depends(get_current_user)
) -> StyleListResponse:
    """Search for styles by name or description."""
    try:
        style_service = StyleService()
        styles, total = style_service.search_styles(
            query=request.query,
            user_id=current_user.id if request.search_type in ["user", "all"] else None,
            search_type=request.search_type,
            page=request.page,
            page_size=request.page_size,
        )
        return StyleListResponse(
            styles=[_style_to_response(style) for style in styles],
            total=min(total, request.page_size * len(styles)),
            page=request.page,
            page_size=request.page_size,
        )
    except Exception as e:
        logger.error(f"Failed to search styles: {e}")
        raise _handle_style_error(e)


@router.get("/{style_id}", response_model=StyleResponse)
async def get_style(
    style_id: str, current_user: User = Depends(get_current_user)
) -> StyleResponse:
    """Get a specific style configuration."""
    try:
        style_service = StyleService()
        style = style_service.get_style(style_id, current_user.id)
        return _style_to_response(style)
    except Exception as e:
        logger.error(f"Failed to get style {style_id}: {e}")
        raise _handle_style_error(e)


@router.put("/{style_id}", response_model=StyleResponse)
async def update_style(
    style_id: str,
    request: StyleUpdateRequest,
    current_user: User = Depends(get_current_user),
) -> StyleResponse:
    """Update an existing style configuration."""
    try:
        # Build updates dictionary
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.colors is not None:
            updates["colors"] = request.colors.to_dict()
        if request.fonts is not None:
            updates["fonts"] = request.fonts.to_dict()
        if request.layout is not None:
            updates["layout"] = request.layout.to_dict()
        if request.transitions is not None:
            updates["transitions"] = request.transitions.to_dict()
        if request.is_public is not None:
            updates["is_public"] = request.is_public
        if request.is_active is not None:
            updates["is_active"] = request.is_active
        if request.show_progress_indicator is not None:
            updates["show_progress_indicator"] = request.show_progress_indicator
        if request.show_slide_numbers is not None:
            updates["show_slide_numbers"] = request.show_slide_numbers
        if request.show_section_headers is not None:
            updates["show_section_headers"] = request.show_section_headers
        if request.use_animations is not None:
            updates["use_animations"] = request.use_animations

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "validation_failed", "message": "No updates provided"},
            )

        style_service = StyleService()
        style = style_service.update_style(style_id, updates, current_user.id)
        return _style_to_response(style)
    except Exception as e:
        logger.error(f"Failed to update style {style_id}: {e}")
        raise _handle_style_error(e)


@router.delete("/{style_id}")
async def delete_style(
    style_id: str, current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete a style configuration."""
    try:
        style_service = StyleService()
        success = style_service.delete_style(style_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "style_not_found", "message": "Style not found"},
            )
        return {"message": "Style deleted successfully", "style_id": style_id}
    except Exception as e:
        logger.error(f"Failed to delete style {style_id}: {e}")
        raise _handle_style_error(e)


@router.post("/{style_id}/export")
async def export_style(
    style_id: str, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Export a style configuration."""
    try:
        style_service = StyleService()
        exported_style = style_service.export_style(style_id, current_user.id)
        return {"style": exported_style, "exported_at": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Failed to export style {style_id}: {e}")
        raise _handle_style_error(e)


@router.post("/import", response_model=StyleResponse)
async def import_style(
    request: StyleImportRequest, current_user: User = Depends(get_current_user)
) -> StyleResponse:
    """Import a style configuration."""
    try:
        style_service = StyleService()
        style = style_service.import_style(
            style_data=request.style_data,
            name=request.name,
            user_id=current_user.id,
            merge_with=request.merge_with,
        )
        return _style_to_response(style)
    except Exception as e:
        logger.error(f"Failed to import style: {e}")
        raise _handle_style_error(e)


@router.post("/create-from-template", response_model=StyleResponse)
async def create_style_from_template(
    template: StyleTemplate, current_user: User = Depends(get_current_user)
) -> StyleResponse:
    """Create a style from a template."""
    try:
        style_service = StyleService()
        style = style_service.create_style_from_template(template, current_user.id)
        return _style_to_response(style)
    except Exception as e:
        logger.error(f"Failed to create style from template: {e}")
        raise _handle_style_error(e)


@router.post("/{style_id}/copy", response_model=StyleResponse)
async def copy_style(
    style_id: str,
    request: StyleCopyRequest,
    current_user: User = Depends(get_current_user),
) -> StyleResponse:
    """Create a copy of an existing style."""
    try:
        style_service = StyleService()
        style = style_service.copy_style(style_id, request.new_name, current_user.id)
        return _style_to_response(style)
    except Exception as e:
        logger.error(f"Failed to copy style {style_id}: {e}")
        raise _handle_style_error(e)


@router.get("/{style_id}/stats")
async def get_style_stats(
    style_id: str, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get usage statistics for a style."""
    try:
        style_service = StyleService()
        stats = style_service.get_style_usage_stats(style_id, current_user.id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get style stats for {style_id}: {e}")
        raise _handle_style_error(e)


@router.post("/{style_id}/validate")
async def validate_style(
    style_id: str, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Validate a style configuration for use."""
    try:
        style_service = StyleService()
        style = style_service.get_style(style_id, current_user.id)
        validated_style = style_service.validate_and_apply_style(style, current_user.id)
        return {
            "valid": True,
            "style_id": style_id,
            "validated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to validate style {style_id}: {e}")
        if isinstance(
            e, (StyleValidationError, StyleNotFoundError, StyleAccessDeniedError)
        ):
            return {
                "valid": False,
                "error": e.__class__.__name__.lower().replace("error", ""),
                "message": str(e),
                "validated_at": datetime.utcnow().isoformat(),
            }
        else:
            raise _handle_style_error(e)


@router.post("/validate-config")
async def validate_style_config(
    config: Dict[str, Any] = Body(..., description="Style configuration to validate"),
) -> Dict[str, Any]:
    """Validate a style configuration without saving it."""
    try:
        from backend.models.style_schema import (
            import_style_config,
            validate_style_config,
        )

        style = import_style_config(config, validate=False)
        if not style:
            return {
                "valid": False,
                "error": "invalid_config",
                "message": "Invalid style configuration format",
            }

        is_valid = validate_style_config(style)
        return {
            "valid": is_valid,
            "validation_errors": []
            if is_valid
            else ["Configuration validation failed"],
            "validated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to validate style config: {e}")
        return {
            "valid": False,
            "error": "validation_failed",
            "message": str(e),
            "validated_at": datetime.utcnow().isoformat(),
        }
