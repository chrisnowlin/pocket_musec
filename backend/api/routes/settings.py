"""Settings API routes for user preferences and processing mode"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
import logging

from backend.auth import User, ProcessingMode
from backend.llm.model_router import ModelRouter
from ..dependencies import get_current_user
from ..models import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])
CURRENT_PROCESSING_MODE = ProcessingMode.CLOUD


# Pydantic models
class ProcessingModeInfo(BaseModel):
    """Processing mode information"""

    id: str
    name: str
    description: str
    available: bool
    estimated_speed: str = ""
    provider: str = ""
    model: str = ""
    error: str = ""


class ProcessingModeResponse(BaseModel):
    """Processing mode response"""

    modes: List[ProcessingModeInfo]
    current: str


class UpdateProcessingModeRequest(BaseModel):
    """Request to update processing mode"""

    mode: str  # "cloud" or "local"


class ModelInfoResponse(BaseModel):
    """Local model information"""

    available: bool
    installed: bool
    model: str
    size: str = ""
    health: str = ""
    models_list: List[str] = []


# Helper to get model router
def get_model_router() -> ModelRouter:
    """Get ModelRouter instance"""
    return ModelRouter()


@router.get("/processing-modes", response_model=ProcessingModeResponse)
async def get_processing_modes(
    current_user: User = Depends(get_current_user),
    router: ModelRouter = Depends(get_model_router),
):
    """
    Get available processing modes

    Args:
        current_user: Current authenticated user
        router: ModelRouter instance

    Returns:
        Available modes and current user preference
    """
    modes = router.get_available_modes()

    # Convert to ProcessingModeInfo
    mode_infos = []
    for mode in modes:
        mode_infos.append(
            ProcessingModeInfo(
                id=mode["id"],
                name=mode["name"],
                description=mode["description"],
                available=mode["available"],
                estimated_speed=mode.get("estimated_speed", ""),
                provider=mode.get("provider", ""),
                model=mode.get("model", ""),
                error=mode.get("error", ""),
            )
        )

    return ProcessingModeResponse(
        modes=mode_infos, current=current_user.processing_mode.value
    )


@router.put("/processing-mode", response_model=MessageResponse)
async def update_processing_mode(
    request: UpdateProcessingModeRequest,
    current_user: User = Depends(get_current_user),
    router: ModelRouter = Depends(get_model_router),
):
    """
    Update user's processing mode preference

    Args:
        request: Processing mode update request
        current_user: Current authenticated user
        auth_service: AuthService instance
        router: ModelRouter instance

    Returns:
        Success message

    Raises:
        400: If mode invalid or unavailable
    """
    # Validate mode
    try:
        mode = ProcessingMode(request.mode)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode: {request.mode}. Must be 'cloud' or 'local'.",
        )

    # Check if mode is available
    if mode == ProcessingMode.CLOUD:
        if not router.is_cloud_available():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cloud mode not available. Check CHUTES_API_KEY configuration.",
            )
    elif mode == ProcessingMode.LOCAL:
        if not router.is_local_available():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Local mode not available. Ensure Ollama is running and model is installed.",
            )

    # Update user preference
    global CURRENT_PROCESSING_MODE
    CURRENT_PROCESSING_MODE = mode
    current_user.processing_mode = mode

    logger.info(f"Processing mode changed to {mode.value}")
    return MessageResponse(message=f"Processing mode updated to {mode.value}")


@router.get("/models/local/status", response_model=ModelInfoResponse)
async def get_local_model_status(
    current_user: User = Depends(get_current_user),
    router: ModelRouter = Depends(get_model_router),
):
    """
    Get local model status

    Args:
        current_user: Current authenticated user
        router: ModelRouter instance

    Returns:
        Local model status information
    """
    if not router.local_provider:
        return ModelInfoResponse(
            available=False,
            installed=False,
            model="",
            health="not_configured",
            models_list=[],
        )

    available = router.local_provider.is_available()
    installed = router.local_provider.is_model_available() if available else False
    models_list = router.list_local_models()

    # Get model info if available
    model_info = None
    size = ""
    if installed:
        model_info = router.local_provider.get_model_info()
        if model_info:
            # Extract size from model info
            size_bytes = model_info.get("size", 0)
            size = f"{size_bytes / (1024**3):.1f} GB"

    health = "healthy" if (available and installed) else "unavailable"

    return ModelInfoResponse(
        available=available,
        installed=installed,
        model=router.local_provider.model,
        size=size,
        health=health,
        models_list=models_list,
    )


@router.post("/models/local/download", response_model=MessageResponse)
async def download_local_model(
    current_user: User = Depends(get_current_user),
    router: ModelRouter = Depends(get_model_router),
):
    """
    Download/pull local model (blocking operation)

    Args:
        current_user: Current authenticated user
        router: ModelRouter instance

    Returns:
        Success message

    Raises:
        400: If Ollama not available
        500: If download fails

    Note: This is a long-running operation (GB download)
    """
    if not router.local_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Local provider not configured",
        )

    if not router.local_provider.is_available():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ollama not running. Start Ollama first.",
        )

    logger.info(
        f"User {current_user.id} initiating model download: {router.local_provider.model}"
    )

    # Pull model (this is blocking)
    success = router.pull_local_model()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download model. Check logs for details.",
        )

    return MessageResponse(
        message=f"Model {router.local_provider.model} downloaded successfully"
    )
