"""Tests for workspace dashboard endpoint."""

from backend.repositories.lesson_repository import LessonRepository
from backend.api.dependencies import DEFAULT_USER


def _create_session(client):
    payload = {
        "grade_level": "Grade 4",
        "strand_code": "CN",
        "selected_objectives": ["4.CN.1.1"],
        "additional_context": "Dashboard test",
    }
    response = client.post("/api/sessions", json=payload)
    assert response.status_code == 200
    return response.json()["id"]


def test_dashboard_returns_default_sections(client):
    session_id = _create_session(client)

    lesson_repo = LessonRepository()
    lesson_repo.create_lesson(
        session_id=session_id,
        user_id=DEFAULT_USER.id,
        title="Draft One",
        content="Lesson content",
        metadata="{}",
        is_draft=True,
    )

    resp = client.get("/api/workspace/dashboard")
    assert resp.status_code == 200
    data = resp.json()

    assert "generatedAt" in data
    assert set(data["includes"]) == {"drafts", "presentations", "sessions", "stats"}
    assert isinstance(data.get("sessions"), list)
    assert data["sessions"], "Expected at least one session"
    assert data["drafts"]["total"] >= 1
    assert "stats" in data
    assert data["stats"]["activeDrafts"] >= 1


def test_dashboard_include_filter(client):
    _create_session(client)

    resp = client.get("/api/workspace/dashboard", params={"include": "sessions,stats"})
    assert resp.status_code == 200
    data = resp.json()

    assert "sessions" in data
    assert "stats" in data
    assert "drafts" not in data
    assert "presentations" not in data
