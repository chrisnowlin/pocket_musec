"""Tests for session repository serialization helpers."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.auth.models import Session


def test_session_selected_fields_to_lists():
    """Session dataclass exposes comma-delimited fields as lists."""

    session = Session(
        id="session-1",
        user_id="user-1",
        grade_level="Grade 4",
        strand_code="CN",
        selected_standards="4.CN.1, 4.CN.2",
        selected_objectives="4.CN.1.1,4.CN.2.2",
    )

    assert session.selected_standards_list == ["4.CN.1", "4.CN.2"]
    assert session.selected_objectives_list == ["4.CN.1.1", "4.CN.2.2"]


def test_session_selected_lists_empty_by_default():
    """Empty CSV fields yield empty lists."""

    session = Session(id="session-2", user_id="user-2")

    assert session.selected_standards_list == []
    assert session.selected_objectives_list == []
