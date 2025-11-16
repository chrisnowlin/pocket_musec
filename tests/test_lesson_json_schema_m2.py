"""Tests for Milestone 2 lesson JSON schema (m2.0).

These tests drive the initial Pydantic models and helper used to
construct and validate m2.0 lesson documents.
"""

from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from backend.lessons.schema_m2 import (
    LessonDocumentM2,
    build_m2_lesson_document,
)


def _sample_content() -> Dict[str, Any]:
    """Return a minimal but complete content structure for m2.0."""

    return {
        "materials": ["rhythm cards", "drums"],
        "warmup": "Students echo simple rhythms.",
        "activities": [
            {
                "id": "act-1",
                "title": "Echo clapping",
                "duration_minutes": 10,
                "steps": [
                    "Teacher claps a pattern",
                    "Students echo the pattern",
                ],
                "aligned_standards": ["K.CN.1"],
                "citations": ["source-1", "shared-source"],
            },
            {
                "id": "act-2",
                "title": "Create a rhythm",
                "duration_minutes": 20,
                "steps": [
                    "Students create 4-beat patterns",
                    "Students perform for peers",
                ],
                "aligned_standards": ["K.CN.1"],
                "citations": ["shared-source", "source-2"],
            },
        ],
        "assessment": "Teacher observes performance.",
        "differentiation": "Provide visual rhythm cards.",
        "exit_ticket": "Students clap one pattern independently.",
        "notes": "Keep tempo slow for beginners.",
        "prerequisites": "Students know quarter and eighth notes.",
        "accommodations": "Allow seated movement.",
        "homework": "Clap patterns at home.",
        "reflection": "How did students respond to call-and-response?",
        "timing": {"total_minutes": 30},
    }


def _base_payload() -> Dict[str, Any]:
    """Base payload that can be turned into a full m2.0 document."""

    return {
        "title": "Rhythm and Movement",
        "grade": "Kindergarten",
        "strands": ["CN"],
        "standards": [
            {
                "code": "K.CN.1",
                "title": "Execute rhythmic patterns",
                "summary": "Students perform simple rhythmic patterns.",
            }
        ],
        "objectives": [
            "Students will clap quarter note patterns.",
            "Students will echo rhythmic patterns.",
        ],
        "content": _sample_content(),
    }


def test_lesson_document_m2_enforces_version_literal() -> None:
    """LessonDocumentM2 should only accept version "m2.0"."""

    now = datetime.now(timezone.utc)
    data = {
        "id": "lesson-1",
        "created_at": now,
        "updated_at": now,
        "version": "m3.0",  # invalid
        "title": "Invalid Version",
        "grade": "Kindergarten",
        "strands": ["CN"],
        "standards": [
            {
                "code": "K.CN.1",
                "title": "Execute rhythmic patterns",
                "summary": "Students perform simple rhythmic patterns.",
            }
        ],
        "objectives": ["Objective"],
        "content": _sample_content(),
        "citations": ["source-1"],
        "revision": 1,
    }

    with pytest.raises(ValidationError):
        LessonDocumentM2.model_validate(data)


def test_build_m2_lesson_document_new_populates_metadata_and_citations() -> None:
    """Building a new document should set metadata and compute citations union."""

    payload = _base_payload()

    doc = build_m2_lesson_document(payload)

    # Metadata
    assert doc.id, "id should be generated for new documents"
    assert doc.version == "m2.0"
    assert doc.revision == 1
    assert doc.title == payload["title"]
    assert doc.grade == payload["grade"]

    # Content is preserved
    assert len(doc.content.activities) == 2
    assert doc.content.activities[0].title == "Echo clapping"

    # Citations are the de-duplicated union of per-activity citations
    assert set(doc.citations) == {"source-1", "shared-source", "source-2"}


def test_build_m2_lesson_document_update_increments_revision_and_preserves_created_at() -> None:
    """Updating a document should bump revision, keep created_at, and merge citations."""

    base_payload = _base_payload()
    original = build_m2_lesson_document(base_payload)

    update_payload: Dict[str, Any] = {
        "title": "Rhythm and Movement (Revised)",
        "content": {
            **base_payload["content"],
            "activities": base_payload["content"]["activities"]
            + [
                {
                    "id": "act-3",
                    "title": "Instrument exploration",
                    "duration_minutes": 5,
                    "steps": ["Students explore percussion instruments."],
                    "aligned_standards": ["K.CN.1"],
                    "citations": ["source-3"],
                }
            ],
        },
    }

    updated = build_m2_lesson_document(update_payload, existing=original)

    assert updated.id == original.id
    assert updated.created_at == original.created_at
    assert updated.revision == original.revision + 1
    assert updated.title == "Rhythm and Movement (Revised)"

    # Citations should include previous and new sources
    assert set(updated.citations) == {
        "source-1",
        "shared-source",
        "source-2",
        "source-3",
    }

