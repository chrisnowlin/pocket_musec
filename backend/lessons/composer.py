"""Simple lesson drafting helper"""

from typing import Optional, Dict, Any

from backend.repositories.standards_repository import StandardsRepository
from backend.auth.models import Session


class LessonComposer:
    """Generates narrative lesson drafts from session context"""

    def __init__(self, standards_repo: Optional[StandardsRepository] = None):
        self.standards_repo = standards_repo or StandardsRepository()

    def compose(
        self,
        session: Session,
        message: str,
        lesson_duration: Optional[str] = None,
        class_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        standard = None
        if session.selected_standards:
            standard = self.standards_repo.get_standard_by_id(
                session.selected_standards
            )

        standard_label = standard.standard_id if standard else "Selected standard"
        grade_label = session.grade_level or "the chosen grade level"

        duration_text = lesson_duration or "one class period"
        size_text = f"{class_size} students" if class_size else "your class"

        overview = (
            f"{message.strip() or 'We are co-planning a lesson.'} This draft connects {grade_label} learners "
            f"to {standard_label} and considers {size_text} over {duration_text}."
        )

        activities = [
            "Warm-up: Short rhythm clapping inspired by the strand's motif.",
            "Main activity: Guided practice connecting movement, text, and sound.",
            "Closure: Reflective journaling or share-out with peer feedback.",
        ]

        assessment = "Use quick performance checks, exit tickets, or recordings to capture mastery of the targeted objective."

        content_lines = [
            f"Title: {standard_label} Focus",
            f"Overview: {overview}",
            "Activities:",
        ]
        content_lines.extend([f"- {activity}" for activity in activities])
        content_lines.append(f"Assessment: {assessment}")
        content_lines.append(
            "Extensions: Invite students to share cultural connections or create visuals."
        )

        return {
            "title": standard_label,
            "summary": overview,
            "content": "\n".join(content_lines),
            "metadata": {
                "grade_level": session.grade_level,
                "strand_code": session.strand_code,
                "standard_id": standard.standard_id if standard else None,
                "duration": lesson_duration,
                "class_size": class_size,
            },
            "citations": [standard.standard_id] if standard else [],
        }
