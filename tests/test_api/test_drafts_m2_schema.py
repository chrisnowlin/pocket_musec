from typing import Any, Dict
from datetime import datetime
import json

import pytest
from fastapi import HTTPException

from backend.api.routes.drafts import _validate_and_attach_m2_document, _lesson_to_draft_response
from backend.auth import Lesson, Session, ProcessingMode


def _simple_payload() -> Dict[str, Any]:
    """Return a minimal but valid m2.0 payload for lesson_document.

    We intentionally keep this small; the full structure is exercised in
    tests/test_lesson_json_schema_m2.py.
    """

    return {
        "title": "Sample Lesson",
        "grade": "Grade 3",
        "strands": ["CN"],
        "standards": [
            {
                "code": "3.CN.1",
                "title": "Sample standard",
                "summary": "Sample summary",
            }
        ],
        "objectives": ["Students will do something."],
        "content": {
            "materials": [],
            "warmup": "",
            "activities": [],
            "assessment": "",
            "differentiation": "",
            "exit_ticket": "",
            "notes": "",
            "prerequisites": "",
            "accommodations": "",
            "homework": "",
            "reflection": "",
            "timing": {"total_minutes": 30},
        },
    }


def test_validate_and_attach_m2_document_no_document_returns_metadata_unchanged() -> None:
    metadata: Dict[str, Any] = {"foo": "bar"}

    result = _validate_and_attach_m2_document(metadata)

    # No lesson_document key means no validation or mutation
    assert result == metadata


def test_validate_and_attach_m2_document_valid_document_sets_version_and_revision() -> None:
    metadata: Dict[str, Any] = {"lesson_document": _simple_payload()}

    result = _validate_and_attach_m2_document(metadata)

    doc = result["lesson_document"]
    # Helper should have round-tripped through Pydantic and attached
    # metadata fields like id, timestamps, version, revision.
    assert doc["version"] == "m2.0"
    assert doc["revision"] == 1
    assert "id" in doc
    assert "created_at" in doc
    assert "updated_at" in doc


def test_validate_and_attach_m2_document_update_uses_existing_document_for_revision() -> None:
    # First call creates the initial document
    initial_metadata = _validate_and_attach_m2_document({"lesson_document": _simple_payload()})
    existing_doc = initial_metadata["lesson_document"]

    # Second call simulates an update with a changed title
    updated_metadata = _validate_and_attach_m2_document(
        {"lesson_document": {"title": "Updated Title"}},
        existing_document=existing_doc,
    )

    updated_doc = updated_metadata["lesson_document"]
    assert updated_doc["title"] == "Updated Title"
    assert updated_doc["revision"] == existing_doc["revision"] + 1
    assert updated_doc["created_at"] == existing_doc["created_at"]


def test_validate_and_attach_m2_document_invalid_document_raises_http_400() -> None:
    # Missing required fields like grade, strands, standards, content
    metadata: Dict[str, Any] = {"lesson_document": {"title": "Incomplete"}}

    with pytest.raises(HTTPException) as excinfo:
        _validate_and_attach_m2_document(metadata)

    assert excinfo.value.status_code == 400




def test_lesson_to_draft_response_does_not_auto_attach_m2_lesson_document() -> None:
    """Draft responses should not synthesize m2.0 documents for legacy data.

    We no longer maintain on-read migration logic. If a stored lesson
    does not have a ``lesson_document`` in its metadata, the drafts API
    simply returns the parsed metadata and relies on the frontend to fall
    back to the narrative ``content`` string.
    """

    # Simulate stored metadata from the existing pipeline
    metadata_dict: Dict[str, Any] = {
        "grade_level": "Grade 3",
        "strand_code": "CN",
        "standard_id": "3.CN.1",
        "duration": "30 minutes",
        "class_size": 25,
        "generated_by": "llm",
    }

    lesson = Lesson(
        id="lesson-1",
        session_id="session-1",
        user_id="user-1",
        title="3.CN.1 Focus",
        content="Narrative lesson content",
        metadata=json.dumps(metadata_dict),
    )

    # Provide a minimal session stub so _lesson_to_draft_response can fall
    # back to session grade/strand if needed.
    session = Session(
        id="session-1",
        user_id="user-1",
        grade_level="Grade 3",
        strand_code="CN",
    )

    class _StubSessionRepo:
        def __init__(self, session: Session) -> None:
            self._session = session

        def get_session(self, session_id: str) -> Session:
            return self._session

    draft = _lesson_to_draft_response(lesson, _StubSessionRepo(session))

    # The response metadata should not be mutated with an auto-generated
    # m2.0 document, but basic fields should still be exposed.
    assert draft.metadata == metadata_dict
    assert "lesson_document" not in draft.metadata
    assert draft.grade == "Grade 3"
    assert draft.strand == "CN"
    assert draft.standard == "3.CN.1"
    assert draft.content == lesson.content
