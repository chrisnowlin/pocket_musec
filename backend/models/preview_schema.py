"""Pydantic models for presentation preview functionality.

This module defines the structured preview document used for storing
presentation outline and key information before full generation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Literal
from uuid import uuid4
from enum import Enum

from pydantic import BaseModel, Field, validator
from backend.api.models import CamelModel


class PreviewStatus(str, Enum):
    """Status of preview generation."""

    PENDING = "pending"
    COMPLETE = "complete"
    ERROR = "error"
    ACCEPTED = "accepted"  # User accepted preview for full generation
    REJECTED = "rejected"  # User rejected preview
    EXPIRED = "expired"  # Preview is older than current lesson revision


class PreviewSlideOutline(CamelModel):
    """Outline of a single slide in the preview."""

    id: str
    order: int
    title: str
    subtitle: Optional[str] = None
    key_points: List[str] = Field(default_factory=list)
    estimated_duration_minutes: int
    slide_type: str = "content"  # title, content, activity, assessment, closure
    source_section: str
    content_summary: str = ""  # Brief summary of slide content
    visual_elements: List[str] = Field(
        default_factory=list
    )  # Suggested visual elements


class PreviewQualityCheck(CamelModel):
    """Result of content quality validation."""

    check_type: str  # content_length, structure, objectives, materials, timing
    passed: bool
    message: str
    severity: str = "info"  # info, warning, error
    suggestion: Optional[str] = None


class PreviewMetadata(CamelModel):
    """Metadata about the preview generation."""

    estimated_duration_minutes: int
    total_slides: int
    slide_types_distribution: Dict[str, int] = Field(default_factory=dict)
    complexity_score: float = Field(ge=0.0, le=1.0)  # 0=simple, 1=complex
    word_count_estimate: int
    teaching_style: str = "interactive"
    target_grade_level: str
    aligned_standards_count: int = 0
    has_assessment: bool = False
    has_differentiation: bool = False
    generation_time_ms: Optional[int] = None


class PreviewUserFeedback(CamelModel):
    """User feedback on the preview."""

    rating: Optional[int] = Field(ge=1, le=5, default=None)
    comments: Optional[str] = None
    suggested_changes: List[str] = Field(default_factory=list)
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None


class PreviewDocument(CamelModel):
    """Structured representation of a presentation preview.

    Contains the outline and key information before full presentation generation.
    """

    id: str
    lesson_id: str
    lesson_revision: int
    version: Literal["prev1.0"]
    status: PreviewStatus = PreviewStatus.PENDING
    style: str = "default"

    # Core preview content
    slide_outlines: List[PreviewSlideOutline] = Field(default_factory=list)
    content_summary: str = ""
    key_teaching_points: List[str] = Field(default_factory=list)

    # Metadata and quality
    metadata: PreviewMetadata
    quality_checks: List[PreviewQualityCheck] = Field(default_factory=list)

    # User interaction
    user_feedback: Optional[PreviewUserFeedback] = None

    # Style and formatting preview
    style_preview: Dict[str, Any] = Field(default_factory=dict)

    # Generation tracking
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Conversion tracking
    converted_to_presentation_id: Optional[str] = (
        None  # Links to full presentation if accepted
    )


def _now_utc() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def build_preview_document(
    lesson_id: str,
    lesson_revision: int,
    slide_outlines: List[PreviewSlideOutline],
    content_summary: str,
    metadata: PreviewMetadata,
    style: str = "default",
    existing: Optional[PreviewDocument] = None,
) -> PreviewDocument:
    """Build and validate a preview document.

    This helper creates or updates a preview document with proper validation.
    """
    now = _now_utc()

    if existing is None:
        # Creating a new document: generate id/timestamps
        doc_id = str(uuid4())
        created_at = now
        version = "prev1.0"
    else:
        # Updating existing document: preserve id/created_at
        doc_id = existing.id
        created_at = existing.created_at
        version = existing.version

    return PreviewDocument(
        id=doc_id,
        lesson_id=lesson_id,
        lesson_revision=lesson_revision,
        version=version,
        status=PreviewStatus.PENDING,
        style=style,
        slide_outlines=slide_outlines,
        content_summary=content_summary,
        key_teaching_points=[],  # Will be populated during generation
        metadata=metadata,
        quality_checks=[],
        user_feedback=None,
        style_preview={},
        error_code=None,
        error_message=None,
        created_at=created_at,
        updated_at=now,
        converted_to_presentation_id=None,
    )


def create_slide_outline(
    order: int,
    title: str,
    slide_type: str,
    key_points: List[str],
    estimated_duration: int,
    source_section: str,
    subtitle: Optional[str] = None,
    content_summary: str = "",
    visual_elements: Optional[List[str]] = None,
) -> PreviewSlideOutline:
    """Create a slide outline with standard structure.

    Helper function for consistent slide outline creation.
    """
    return PreviewSlideOutline(
        id=str(uuid4()),
        order=order,
        title=title,
        subtitle=subtitle,
        key_points=key_points,
        estimated_duration_minutes=estimated_duration,
        slide_type=slide_type,
        source_section=source_section,
        content_summary=content_summary,
        visual_elements=visual_elements or [],
    )


class PreviewGenerationRequest(CamelModel):
    """Request model for preview generation."""

    lesson_id: str
    user_id: str
    style: str = "default"
    max_slides: Optional[int] = Field(default=20, ge=5, le=50)
    include_quality_checks: bool = True
    target_duration_minutes: Optional[int] = Field(default=45, ge=15, le=120)
    complexity_preference: str = Field(
        default="balanced", pattern="^(simple|balanced|advanced)$"
    )


class PreviewUpdateRequest(CamelModel):
    """Request model for updating preview content."""

    slide_outlines: Optional[List[PreviewSlideOutline]] = None
    content_summary: Optional[str] = None
    key_teaching_points: Optional[List[str]] = None
    style: Optional[str] = None


class PreviewAcceptRequest(CamelModel):
    """Request model for accepting a preview for full generation."""

    use_llm_polish: bool = True
    timeout_seconds: int = 30
    apply_suggested_changes: bool = True
    additional_instructions: Optional[str] = None


class PreviewFeedbackRequest(CamelModel):
    """Request model for submitting user feedback."""

    rating: Optional[int] = Field(ge=1, le=5)
    comments: Optional[str] = None
    suggested_changes: List[str] = Field(default_factory=list)


# Response models
class PreviewResponse(CamelModel):
    """Response model for preview data."""

    id: str
    lesson_id: str
    lesson_revision: int
    status: str
    style: str
    slide_count: int
    estimated_duration_minutes: int
    content_summary: str
    key_teaching_points: List[str]
    created_at: str
    updated_at: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    user_feedback: Optional[Dict[str, Any]] = None
    quality_checks: List[Dict[str, Any]] = []
    metadata: Dict[str, Any]
    converted_to_presentation_id: Optional[str] = None


class PreviewDetailResponse(PreviewResponse):
    """Detailed preview response with slide outlines."""

    slide_outlines: List[Dict[str, Any]]
    style_preview: Dict[str, Any]


class PreviewGenerationResponse(CamelModel):
    """Response model for preview generation requests."""

    preview_id: str
    status: str
    message: str
    generation_time_ms: Optional[int] = None


class PreviewQualityReport(CamelModel):
    """Quality assessment report for a preview."""

    preview_id: str
    overall_score: float = Field(ge=0.0, le=1.0)
    checks: List[PreviewQualityCheck]
    recommendations: List[str] = Field(default_factory=list)
    estimated_quality_tier: str = Field(pattern="^(basic|standard|premium)$")


# ---------------------------------------------------------------------------
# Simple content preview models
# ---------------------------------------------------------------------------


class SlidePreview(CamelModel):
    """A lightweight representation of a single slide.

    Attributes
    ----------
    title: str
        The slide title.
    key_points: List[str]
        Bullet points or key ideas that will appear on the slide.
    estimated_duration_seconds: int
        Approximate time, in seconds, that a presenter should spend on this slide.
        Must be greater than zero.
    """

    title: str
    key_points: List[str]
    estimated_duration_seconds: int

    @validator("estimated_duration_seconds")
    def duration_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("estimated_duration_seconds must be greater than 0")
        return v


class PresentationPreview(CamelModel):
    """A preview of an entire presentation.

    Attributes
    ----------
    presentation_id: str
        Identifier for the presentation.
    generated_at: datetime
        Timestamp when the preview was generated.
    slides: List[SlidePreview]
        List of slide previews.
    total_estimated_duration_seconds: int
        Sum of the estimated durations of all slides.
    style_id: Optional[str]
        Optional reference to a style definition used for the presentation.
    """

    presentation_id: str
    generated_at: datetime
    slides: List[SlidePreview]
    total_estimated_duration_seconds: int
    style_id: Optional[str] = None

    def summary(self) -> dict:
        """Return a concise summary of the preview.

        The summary includes the total number of slides and the total
        estimated duration (in seconds).
        """
        return {
            "slide_count": len(self.slides),
            "total_estimated_duration_seconds": self.total_estimated_duration_seconds,
        }
