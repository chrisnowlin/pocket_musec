"""Pydantic models and helpers for presentation documents (p1.0).

This module defines the structured presentation document used for storing
generated slide decks that accompany lessons, following the design in
``openspec/changes/add-lesson-presentations/design.md``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Literal
from uuid import uuid4
from enum import Enum

from pydantic import BaseModel, Field


class PresentationStatus(str, Enum):
    """Status of presentation generation."""

    PENDING = "pending"
    COMPLETE = "complete"
    ERROR = "error"
    STALE = "stale"


class SourceSection(str, Enum):
    """Source sections in a lesson that slides can reference."""

    OVERVIEW = "overview"
    OBJECTIVES = "objectives"
    MATERIALS = "materials"
    WARMUP = "warmup"
    ACTIVITY = "activity"
    ASSESSMENT = "assessment"
    DIFFERENTIATION = "differentiation"
    CLOSURE = "closure"


class PresentationSlide(BaseModel):
    """Individual slide within a presentation document."""

    id: str
    order: int
    title: str
    subtitle: Optional[str] = None
    key_points: List[str] = Field(default_factory=list)
    teacher_script: str = ""
    visual_prompt: Optional[str] = None
    duration_minutes: Optional[int] = None
    source_section: SourceSection
    activity_id: Optional[str] = None
    standard_codes: List[str] = Field(default_factory=list)


class PresentationExport(BaseModel):
    """Export asset metadata for a presentation."""

    format: str  # "json", "markdown", "pptx", "pdf"
    url_or_path: str
    generated_at: datetime
    file_size_bytes: Optional[int] = None


class PresentationDocument(BaseModel):
    """Structured JSON representation of a presentation (p1.0).

    This mirrors the requirements in
    ``openspec/changes/add-lesson-presentations/specs/lesson-presentations/spec.md``.
    """

    id: str
    lesson_id: str
    lesson_revision: int
    version: Literal["p1.0"]
    status: PresentationStatus = PresentationStatus.PENDING
    style: str = "default"
    slides: List[PresentationSlide] = Field(default_factory=list)
    export_assets: List[PresentationExport] = Field(default_factory=list)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


def _now_utc() -> datetime:
    """Return a timezone-aware UTC timestamp.

    Wrapped for easier patching in tests if needed.
    """
    return datetime.now(timezone.utc)


def build_presentation_document(
    lesson_id: str,
    lesson_revision: int,
    slides: List[PresentationSlide],
    existing: Optional[PresentationDocument] = None,
    style: str = "default",
) -> PresentationDocument:
    """Build and validate a presentation document.

    This helper is intended for use at API boundaries where callers may
    provide slide data and (optionally) an existing document. It:

    - Ensures required metadata fields are present (id, timestamps, version)
    - Preserves lesson linkage and revision information
    - Returns a fully validated :class:`PresentationDocument` instance
    """

    now = _now_utc()

    if existing is None:
        # Creating a new document: generate id/timestamps
        doc_id = str(uuid4())
        created_at = now
        version = "p1.0"
    else:
        # Updating existing document: preserve id/created_at
        doc_id = existing.id
        created_at = existing.created_at
        version = existing.version

    return PresentationDocument(
        id=doc_id,
        lesson_id=lesson_id,
        lesson_revision=lesson_revision,
        version=version,
        status=PresentationStatus.PENDING,
        style=style,
        slides=slides,
        export_assets=[],
        error_code=None,
        error_message=None,
        created_at=created_at,
        updated_at=now,
    )


def create_slide_from_lesson_section(
    order: int,
    title: str,
    source_section: SourceSection,
    key_points: List[str],
    activity_id: Optional[str] = None,
    standard_codes: Optional[List[str]] = None,
    subtitle: Optional[str] = None,
    teacher_script: str = "",
    visual_prompt: Optional[str] = None,
    duration_minutes: Optional[int] = None,
) -> PresentationSlide:
    """Create a presentation slide from lesson section data.

    Helper function to standardize slide creation from lesson content.
    """
    return PresentationSlide(
        id=str(uuid4()),
        order=order,
        title=title,
        subtitle=subtitle,
        key_points=key_points,
        teacher_script=teacher_script,
        visual_prompt=visual_prompt,
        duration_minutes=duration_minutes,
        source_section=source_section,
        activity_id=activity_id,
        standard_codes=standard_codes or [],
    )
