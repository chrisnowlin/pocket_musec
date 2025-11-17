"""Pydantic models and helpers for Milestone 2 lesson JSON schema (m2.0).

This module defines the structured lesson document used as the canonical
contract for milestone 2 (version ``m2.0``) and a small helper for building
and validating documents on create/update.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Literal
from uuid import uuid4

from pydantic import BaseModel, Field
from backend.api.models import CamelModel


class LessonStandard(CamelModel):
    """Standard metadata included in m2.0 lesson documents."""

    code: str
    title: str
    summary: str


class LessonActivity(CamelModel):
    """An instructional activity within the lesson content."""

    id: str
    title: str
    duration_minutes: int
    steps: List[str]
    aligned_standards: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)


class LessonTiming(CamelModel):
    """Overall timing information for the lesson."""

    total_minutes: int


class LessonContent(CamelModel):
    """Nested instructional content for an m2.0 lesson."""

    materials: List[str] = Field(default_factory=list)
    warmup: str = ""
    activities: List[LessonActivity] = Field(default_factory=list)
    assessment: str = ""
    differentiation: str = ""
    exit_ticket: str = ""
    notes: str = ""
    prerequisites: str = ""
    accommodations: str = ""
    homework: str = ""
    reflection: str = ""
    timing: LessonTiming


class LessonDocumentM2(CamelModel):
    """Structured JSON representation of a lesson for milestone 2 (m2.0).

    This mirrors the requirements in
    ``openspec/changes/add-lesson-json-schema-m2/specs/lesson-json-schema/spec.md``.
    """

    id: str
    created_at: datetime
    updated_at: datetime
    # Version is a closed set; for this change we only support m2.0
    version: Literal["m2.0"]
    title: str
    grade: str
    strands: List[str]
    standards: List[LessonStandard]
    objectives: List[str]
    content: LessonContent
    citations: List[str] = Field(default_factory=list)
    revision: int


def _now_utc() -> datetime:
    """Return a timezone-aware UTC timestamp.

    Wrapped for easier patching in tests if needed.
    """

    return datetime.now(timezone.utc)


def _ensure_global_citations(document: Dict[str, Any]) -> Dict[str, Any]:
    """Populate the top-level ``citations`` with the union of activity citations.

    The OpenSpec requirement states that the top-level ``citations`` array
    SHALL include a de-duplicated list of all citations used anywhere in
    ``content``. This helper enforces that invariant on a plain dict, leaving
    other fields untouched.
    """

    seen: set[str] = set()
    merged: List[str] = []

    # Start with any explicit top-level citations
    for c in document.get("citations") or []:
        if isinstance(c, str) and c not in seen:
            seen.add(c)
            merged.append(c)

    content = document.get("content") or {}
    activities = content.get("activities") or []

    for activity in activities:
        if not isinstance(activity, dict):
            continue
        for c in activity.get("citations") or []:
            if isinstance(c, str) and c not in seen:
                seen.add(c)
                merged.append(c)

    document["citations"] = merged
    return document


def build_m2_lesson_document(
    payload: Dict[str, Any],
    existing: Optional[Union[LessonDocumentM2, Dict[str, Any]]] = None,
) -> LessonDocumentM2:
    """Build and validate an m2.0 lesson document.

    This helper is intended for use at API boundaries where callers may
    provide a partial payload and (optionally) an existing document. It:

    - Ensures required metadata fields are present (``id``, timestamps,
      ``version``, ``revision``).
    - Increments ``revision`` and updates ``updated_at`` on updates while
      preserving ``created_at``.
    - Computes the top-level ``citations`` array as the de-duplicated union
      of all activity-level citations.
    - Returns a fully validated :class:`LessonDocumentM2` instance.
    """

    if existing is None:
        base: Dict[str, Any] = {}
    elif isinstance(existing, LessonDocumentM2):
        # Use model_dump for Pydantic v2, falling back to dict() if needed.
        dump_method = getattr(existing, "model_dump", None)
        base = dump_method() if callable(dump_method) else existing.dict()
    else:
        base = dict(existing)

    now = _now_utc()

    if not base:
        # Creating a new document: generate id/timestamps if absent and
        # start revision at 1.
        base["id"] = payload.get("id") or str(uuid4())
        base["created_at"] = payload.get("created_at") or now
        base["revision"] = payload.get("revision") or 1
        base["version"] = "m2.0"
    else:
        # Updating an existing document: preserve id/created_at and bump
        # revision. If version is missing, default to m2.0.
        base["id"] = base.get("id")
        base["created_at"] = base.get("created_at")
        base["revision"] = int(base.get("revision", 1)) + 1
        base["version"] = base.get("version") or "m2.0"

    base["updated_at"] = now

    # Merge payload fields, letting the new payload win for non-metadata keys.
    for key, value in payload.items():
        if key in {"id", "created_at", "updated_at", "version", "revision"}:
            continue
        base[key] = value

    base = _ensure_global_citations(base)

    # Let Pydantic handle structural validation and coercion.
    return LessonDocumentM2(**base)
