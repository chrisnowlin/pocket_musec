"""Presentation generation service orchestration.

This service coordinates the end-to-end presentation generation process,
including scaffold building, optional LLM polishing, and persistence.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from backend.repositories.presentation_repository import PresentationRepository
from backend.repositories.lesson_repository import LessonRepository
from backend.llm.chutes_client import ChutesClient
from backend.lessons.presentation_schema import (
    PresentationDocument,
    PresentationStatus,
    PresentationSlide,
    SourceSection,
    PresentationExport,
)
from backend.lessons.presentation_builder import build_presentation_scaffold
from backend.lessons.presentation_polish import polish_presentation_slides
from backend.lessons.schema_m2 import LessonDocumentM2

logger = logging.getLogger(__name__)


class PresentationService:
    """Orchestrates presentation generation from lesson documents."""

    def __init__(
        self,
        presentation_repo: Optional[PresentationRepository] = None,
        lesson_repo: Optional[LessonRepository] = None,
        chutes_client: Optional[ChutesClient] = None,
    ):
        self.presentation_repo = presentation_repo or PresentationRepository()
        self.lesson_repo = lesson_repo or LessonRepository()
        self.chutes_client = chutes_client or ChutesClient(require_api_key=False)

    def generate_presentation(
        self,
        lesson_id: str,
        user_id: str,
        style: str = "default",
        use_llm_polish: bool = True,
        timeout_seconds: int = 30,
    ) -> PresentationDocument:
        """Generate a presentation for a lesson.

        Args:
            lesson_id: ID of the lesson to generate presentation for
            user_id: ID of the user requesting the presentation
            style: Presentation style (currently only 'default' supported)
            use_llm_polish: Whether to attempt LLM polishing
            timeout_seconds: Maximum time to wait for LLM polishing

        Returns:
            PresentationDocument with generated slides
        """
        logger.info(f"Starting presentation generation for lesson {lesson_id}")

        # 1. Fetch the lesson document
        lesson = self._fetch_lesson_document(lesson_id, user_id)
        if not lesson:
            raise ValueError(f"Lesson {lesson_id} not found or access denied")

        # 2. Mark any existing presentations as stale
        self._mark_existing_stale(lesson_id, lesson.revision)

        # 3. Create initial presentation record with pending status
        scaffold_slides = build_presentation_scaffold(lesson)
        presentation = self.presentation_repo.create_presentation(
            lesson_id=lesson_id,
            lesson_revision=lesson.revision,
            slides=scaffold_slides,
            style=style,
        )

        try:
            # 4. Generate slides (scaffold + optional polish)
            final_slides = self._generate_slides(
                lesson, scaffold_slides, use_llm_polish, timeout_seconds
            )

            # 5. Update presentation with final slides
            updated_presentation = self.presentation_repo.update_presentation_slides(
                presentation_id=presentation.id,
                slides=final_slides,
            )

            # 6. Generate initial export assets
            self._generate_export_assets(updated_presentation)

            logger.info(f"Successfully generated presentation {presentation.id}")
            return updated_presentation

        except Exception as e:
            logger.error(f"Failed to generate presentation {presentation.id}: {e}")

            # Mark presentation as error
            self.presentation_repo.update_presentation_status(
                presentation_id=presentation.id,
                status=PresentationStatus.ERROR,
                error_code="GENERATION_FAILED",
                error_message=str(e),
            )
            raise

    def regenerate_presentation(
        self,
        lesson_id: str,
        user_id: str,
        style: str = "default",
        use_llm_polish: bool = True,
        timeout_seconds: int = 30,
    ) -> PresentationDocument:
        """Regenerate a presentation for a lesson.

        Similar to generate_presentation but explicitly marks all existing
        presentations as stale before creating a new one.
        """
        logger.info(f"Regenerating presentation for lesson {lesson_id}")

        # Mark all existing presentations as stale
        self._mark_all_stale(lesson_id)

        # Generate new presentation
        return self.generate_presentation(
            lesson_id, user_id, style, use_llm_polish, timeout_seconds
        )

    def get_presentation_status(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        """Get the current presentation status for a lesson.

        Returns:
            Dict with status information or None if no presentation exists
        """
        presentation = self.presentation_repo.latest_by_lesson(lesson_id)
        if not presentation:
            return None

        return {
            "presentation_id": presentation.id,
            "status": presentation.status.value,
            "lesson_revision": presentation.lesson_revision,
            "slide_count": len(presentation.slides),
            "created_at": presentation.created_at.isoformat(),
            "updated_at": presentation.updated_at.isoformat(),
            "has_exports": len(presentation.export_assets) > 0,
            "error_code": presentation.error_code,
            "error_message": presentation.error_message,
        }

    def get_presentation(
        self, presentation_id: str, user_id: str
    ) -> Optional[PresentationDocument]:
        """Get a presentation by ID with user access check."""
        presentation = self.presentation_repo.get_presentation(presentation_id)
        if not presentation:
            return None

        # Verify user has access to the lesson
        lesson = self._fetch_lesson_document(presentation.lesson_id, user_id)
        if not lesson:
            return None

        return presentation

    def mark_stale_on_lesson_update(self, lesson_id: str, new_revision: int) -> int:
        """Mark presentations as stale when a lesson is updated.

        Args:
            lesson_id: ID of the updated lesson
            new_revision: New revision number of the lesson

        Returns:
            Number of presentations marked as stale
        """
        return self.presentation_repo.mark_stale_for_lesson(lesson_id, new_revision)

    def _fetch_lesson_document(
        self, lesson_id: str, user_id: str
    ) -> Optional[LessonDocumentM2]:
        """Fetch and validate lesson document for the user."""
        # First check if user has access to the lesson
        lesson = self.lesson_repo.get_lesson(lesson_id)
        if not lesson or lesson.user_id != user_id:
            return None

        # Try to parse lesson content as m2.0 document
        try:
            import json

            lesson_data = json.loads(lesson.content)
            return LessonDocumentM2(**lesson_data)
        except Exception as e:
            logger.warning(f"Failed to parse lesson {lesson_id} as m2.0: {e}")
            return None

    def _mark_existing_stale(self, lesson_id: str, current_revision: int) -> None:
        """Mark existing presentations as stale for older revisions."""
        stale_count = self.presentation_repo.mark_stale_for_lesson(
            lesson_id, current_revision
        )
        if stale_count > 0:
            logger.info(f"Marked {stale_count} existing presentations as stale")

    def _mark_all_stale(self, lesson_id: str) -> None:
        """Mark all presentations for a lesson as stale."""
        # This is a more aggressive stale marking for regeneration
        presentations = self.presentation_repo.list_presentations_for_lesson(
            lesson_id, include_stale=False
        )

        for presentation in presentations:
            self.presentation_repo.update_presentation_status(
                presentation_id=presentation.id,
                status=PresentationStatus.STALE,
            )

        logger.info(
            f"Marked {len(presentations)} presentations as stale for regeneration"
        )

    def _generate_slides(
        self,
        lesson: LessonDocumentM2,
        scaffold_slides: List,
        use_llm_polish: bool,
        timeout_seconds: int,
    ) -> List:
        """Generate final slides from lesson content."""
        if use_llm_polish and self.chutes_client.is_available():
            try:
                return polish_presentation_slides(
                    lesson=lesson,
                    scaffold_slides=scaffold_slides,
                    chutes_client=self.chutes_client,
                    timeout_seconds=timeout_seconds,
                )
            except Exception as e:
                logger.warning(f"LLM polishing failed, using scaffold: {e}")

        return scaffold_slides

    def _generate_export_assets(self, presentation: PresentationDocument) -> None:
        """Generate initial export assets for the presentation."""
        try:
            # Generate JSON export
            json_export = self._create_json_export(presentation)
            self.presentation_repo.add_export_asset(
                presentation_id=presentation.id,
                export_asset=json_export,
            )

            # Generate Markdown export
            markdown_export = self._create_markdown_export(presentation)
            self.presentation_repo.add_export_asset(
                presentation_id=presentation.id,
                export_asset=markdown_export,
            )

            logger.info(f"Generated export assets for presentation {presentation.id}")

        except Exception as e:
            logger.warning(f"Failed to generate export assets: {e}")
            # Don't fail the whole presentation generation for export issues

    def _create_json_export(
        self, presentation: PresentationDocument
    ) -> PresentationExport:
        """Create JSON export asset."""
        import json

        json_content = json.dumps(
            {
                "presentation": presentation.model_dump(),
                "generated_at": datetime.utcnow().isoformat(),
                "format": "p1.0",
            },
            indent=2,
        )

        return PresentationExport(
            format="json",
            url_or_path=f"presentation_{presentation.id}.json",
            generated_at=datetime.utcnow(),
            file_size_bytes=len(json_content.encode("utf-8")),
        )

    def _create_markdown_export(
        self, presentation: PresentationDocument
    ) -> PresentationExport:
        """Create Markdown export asset."""
        markdown_lines = [
            f"# {presentation.slides[0].title if presentation.slides else 'Presentation'}",
            "",
            f"**Generated:** {presentation.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"**Lesson ID:** {presentation.lesson_id}",
            f"**Revision:** {presentation.lesson_revision}",
            "",
            "---",
            "",
        ]

        for slide in presentation.slides:
            markdown_lines.extend(
                [
                    f"## {slide.title}",
                    "",
                ]
            )

            if slide.subtitle:
                markdown_lines.extend(
                    [
                        f"**{slide.subtitle}**",
                        "",
                    ]
                )

            if slide.key_points:
                markdown_lines.extend(
                    [
                        "**Key Points:**",
                        "",
                    ]
                )
                for point in slide.key_points:
                    markdown_lines.append(f"- {point}")
                markdown_lines.append("")

            if slide.teacher_script:
                markdown_lines.extend(
                    [
                        "**Teacher Script:**",
                        "",
                        slide.teacher_script,
                        "",
                    ]
                )

            if slide.duration_minutes:
                markdown_lines.extend(
                    [
                        f"**Duration:** {slide.duration_minutes} minutes",
                        "",
                    ]
                )

            if slide.standard_codes:
                markdown_lines.extend(
                    [
                        "**Standards:** " + ", ".join(slide.standard_codes),
                        "",
                    ]
                )

            markdown_lines.append("---")
            markdown_lines.append("")

        markdown_content = "\n".join(markdown_lines)

        return PresentationExport(
            format="markdown",
            url_or_path=f"presentation_{presentation.id}.md",
            generated_at=datetime.utcnow(),
            file_size_bytes=len(markdown_content.encode("utf-8")),
        )
