"""Image ingestion API routes"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import List, Optional
import tempfile
from pathlib import Path
import logging

from ...auth import User
from ...image_processing import ImageProcessor, ImageRepository
from ..dependencies import get_current_user
from ..models import MessageResponse
from ...config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/images", tags=["images"])


# Helper to get image processor
def get_image_processor() -> ImageProcessor:
    """Get ImageProcessor instance"""
    return ImageProcessor(
        storage_path=config.image_processing.storage_path, api_key=config.chutes.api_key
    )


# Helper to get image repository
def get_image_repository() -> ImageRepository:
    """Get ImageRepository instance"""
    return ImageRepository(db_path=config.database.path)


# Pydantic models for responses
from pydantic import BaseModel
from datetime import datetime


class ImageResponse(BaseModel):
    """Image metadata response"""

    id: str
    filename: str
    file_size: int
    mime_type: str
    extracted_text: Optional[str]
    vision_summary: Optional[str]
    ocr_confidence: Optional[float]
    metadata: Optional[str]
    created_at: datetime
    url: str  # URL to retrieve image

    class Config:
        from_attributes = True


class ImageUploadResponse(BaseModel):
    """Image upload response"""

    id: str
    filename: str
    file_size: int
    mime_type: str
    extracted_text: str
    vision_summary: Optional[str]
    ocr_confidence: float
    image_type: str
    message: str


class StorageInfoResponse(BaseModel):
    """Storage quota information"""

    usage_mb: float
    limit_mb: float
    available_mb: float
    percentage: float
    image_count: int


@router.post(
    "/upload", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED
)
async def upload_image(
    file: UploadFile = File(...),
    analyze_vision: bool = Form(True),
    current_user: User = Depends(get_current_user),
    processor: ImageProcessor = Depends(get_image_processor),
    repo: ImageRepository = Depends(get_image_repository),
):
    """
    Upload and process an image

    Args:
        file: Image file to upload
        analyze_vision: Whether to run vision analysis (default: true)
        current_user: Current authenticated user
        processor: ImageProcessor instance
        repo: ImageRepository instance

    Returns:
        Processing results

    Raises:
        400: If file invalid or quota exceeded
        413: If file too large
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/tiff", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}",
        )

    # Check file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {max_size / (1024 * 1024):.1f}MB",
        )

    # Check storage quota
    if not processor.storage.check_quota(len(file_content)):
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="Storage quota exceeded. Please delete old images.",
        )

    # Save to temporary file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=Path(file.filename).suffix
    ) as tmp_file:
        tmp_file.write(file_content)
        tmp_path = tmp_file.name

    try:
        # Process image
        result = processor.process_image(
            image_path=tmp_path,
            user_id=current_user.id,
            original_filename=file.filename,
            analyze_vision=analyze_vision,
        )

        # Save to database
        image_model = repo.save_image(
            user_id=current_user.id,
            filename=file.filename,
            file_path=result["stored_path"],
            file_size=result["file_size"],
            mime_type=result["mime_type"],
            extracted_text=result["extracted_text"],
            vision_summary=result["vision_summary"],
            ocr_confidence=result["ocr_confidence"],
            metadata=result.get("metadata"),
        )

        logger.info(f"User {current_user.id} uploaded image: {image_model.id}")

        return ImageUploadResponse(
            id=image_model.id,
            filename=file.filename,
            file_size=result["file_size"],
            mime_type=result["mime_type"],
            extracted_text=result["extracted_text"],
            vision_summary=result["vision_summary"],
            ocr_confidence=result["ocr_confidence"],
            image_type=result["image_type"],
            message="Image uploaded and processed successfully",
        )

    finally:
        # Clean up temporary file
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/upload/batch", response_model=List[ImageUploadResponse])
async def upload_images_batch(
    files: List[UploadFile] = File(...),
    analyze_vision: bool = Form(True),
    current_user: User = Depends(get_current_user),
    processor: ImageProcessor = Depends(get_image_processor),
    repo: ImageRepository = Depends(get_image_repository),
):
    """
    Upload and process multiple images

    Args:
        files: List of image files
        analyze_vision: Whether to run vision analysis
        current_user: Current authenticated user
        processor: ImageProcessor instance
        repo: ImageRepository instance

    Returns:
        List of processing results
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files per batch upload",
        )

    results = []

    for file in files:
        try:
            # Process each file
            result = await upload_image(
                file=file,
                analyze_vision=analyze_vision,
                current_user=current_user,
                processor=processor,
                repo=repo,
            )
            results.append(result)

        except HTTPException as e:
            # Continue processing other files on error
            logger.warning(f"Failed to process {file.filename}: {e.detail}")
            results.append(
                ImageUploadResponse(
                    id="error",
                    filename=file.filename,
                    file_size=0,
                    mime_type="",
                    extracted_text="",
                    vision_summary=None,
                    ocr_confidence=0.0,
                    image_type="error",
                    message=f"Error: {e.detail}",
                )
            )

    return results


@router.get("/", response_model=List[ImageResponse])
async def list_images(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    repo: ImageRepository = Depends(get_image_repository),
):
    """
    List user's images

    Args:
        limit: Maximum number of images (default: 50)
        offset: Offset for pagination (default: 0)
        current_user: Current authenticated user
        repo: ImageRepository instance

    Returns:
        List of images
    """
    images = repo.get_user_images(
        user_id=current_user.id,
        limit=min(limit, 100),  # Cap at 100
        offset=offset,
    )

    return [
        ImageResponse(**{**image.__dict__, "url": f"/api/images/{image.id}/data"})
        for image in images
    ]


@router.get("/search", response_model=List[ImageResponse])
async def search_images(
    q: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    repo: ImageRepository = Depends(get_image_repository),
):
    """
    Search images by text content

    Args:
        q: Search query
        limit: Maximum results (default: 20)
        current_user: Current authenticated user
        repo: ImageRepository instance

    Returns:
        Matching images
    """
    images = repo.search_images(user_id=current_user.id, query=q, limit=min(limit, 50))

    return [
        ImageResponse(**{**image.__dict__, "url": f"/api/images/{image.id}/data"})
        for image in images
    ]


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: str,
    current_user: User = Depends(get_current_user),
    repo: ImageRepository = Depends(get_image_repository),
):
    """
    Get image metadata

    Args:
        image_id: Image ID
        current_user: Current authenticated user
        repo: ImageRepository instance

    Returns:
        Image metadata

    Raises:
        404: If image not found or not owned by user
    """
    image = repo.get_image_by_id(image_id)

    if not image or image.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    # Update last accessed
    repo.update_last_accessed(image_id)

    return ImageResponse(**{**image.__dict__, "url": f"/api/images/{image_id}/data"})


@router.get("/{image_id}/data")
async def get_image_data(
    image_id: str,
    compressed: bool = True,
    current_user: User = Depends(get_current_user),
    repo: ImageRepository = Depends(get_image_repository),
):
    """
    Get image file data

    Args:
        image_id: Image ID
        compressed: Return compressed version (default: true)
        current_user: Current authenticated user
        repo: ImageRepository instance

    Returns:
        Image file

    Raises:
        404: If image not found or file missing
    """
    image = repo.get_image_by_id(image_id)

    if not image or image.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    # Determine which file to serve
    file_path = Path(image.file_path)

    if compressed:
        # Look for compressed version
        compressed_path = file_path.parent / file_path.name.replace(
            "_original", "_compressed"
        ).replace(file_path.suffix, ".jpg")
        if compressed_path.exists():
            file_path = compressed_path

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found"
        )

    # Update last accessed
    repo.update_last_accessed(image_id)

    return FileResponse(
        path=str(file_path),
        media_type=image.mime_type if not compressed else "image/jpeg",
        filename=image.filename,
    )


@router.delete("/{image_id}", response_model=MessageResponse)
async def delete_image(
    image_id: str,
    current_user: User = Depends(get_current_user),
    repo: ImageRepository = Depends(get_image_repository),
    processor: ImageProcessor = Depends(get_image_processor),
):
    """
    Delete an image

    Args:
        image_id: Image ID
        current_user: Current authenticated user
        repo: ImageRepository instance
        processor: ImageProcessor instance

    Returns:
        Success message

    Raises:
        404: If image not found
    """
    image = repo.get_image_by_id(image_id)

    if not image or image.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    # Delete from storage
    processor.storage.delete_image(image.file_path)

    # Delete from database
    repo.delete_image(image_id)

    logger.info(f"User {current_user.id} deleted image: {image_id}")

    return MessageResponse(message="Image deleted successfully")


@router.get("/storage/info", response_model=StorageInfoResponse)
async def get_storage_info(
    current_user: User = Depends(get_current_user),
    processor: ImageProcessor = Depends(get_image_processor),
    repo: ImageRepository = Depends(get_image_repository),
):
    """
    Get storage quota information

    Args:
        current_user: Current authenticated user
        processor: ImageProcessor instance
        repo: ImageRepository instance

    Returns:
        Storage quota info
    """
    quota_info = processor.get_storage_info()
    image_count = repo.get_image_count(current_user.id)

    return StorageInfoResponse(**quota_info, image_count=image_count)
