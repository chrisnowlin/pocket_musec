"""Service for generating lightweight presentation previews.

This module provides a thin wrapper around the existing lesson data to produce a
`PresentationPreview` consisting of a list of `SlidePreview` objects. The preview
contains only the most salient information needed for a quick overview before a
full presentation is generated.
"""

import logging
from datetime import datetime
from typing import List, Optional

from backend.repositories.preview_repository import PreviewRepository
from backend.repositories.lesson_repository import LessonRepository
from backend.services.presentation_service import PresentationService
from backend.services.presentation_errors import PresentationError, PresentationErrorCode, create_error_from_exception
from backend.models.preview_schema import PresentationPreview, SlidePreview

logger = logging.getLogger(__name__)


class PreviewService:
    """Orchestrates generation and retrieval of presentation previews.

    The service pulls lesson content, creates a concise slide outline, stores the
    preview in the SQLite `presentation_previews` table and returns a
    :class:`PresentationPreview` instance.
    """

    def __init__(
        self,
        preview_repo: Optional[PreviewRepository] = None,
        lesson_repo: Optional[LessonRepository] = None,
        presentation_service: Optional[PresentationService] = None,
    ) -> None:
        """Initialize the service with optional repository and service instances.

        Parameters
        ----------
        preview_repo: PreviewRepository, optional
            Repository used for persisting previews. If omitted a default instance
            is created.
        lesson_repo: LessonRepository, optional
            Repository used for fetching lesson documents.
        presentation_service: PresentationService, optional
            Service used for any additional lesson‑level processing. It is not
            required for the minimal preview generation but is injected for
            consistency with the rest of the code‑base.
        """
        self.preview_repo = preview_repo or PreviewRepository()
        self.lesson_repo = lesson_repo or LessonRepository()
        self.presentation_service = presentation_service or PresentationService()

    def _fetch_lesson(self, lesson_id: str):
        """Retrieve a lesson document or raise a ``PresentationError``.

        Parameters
        ----------
        lesson_id: str
            The identifier of the lesson to preview.
        """
        lesson = self.lesson_repo.get_lesson(lesson_id)
        if not lesson:
            logger.error("Lesson %s not found when generating preview", lesson_id)
            raise PresentationError.not_found(
                f"Lesson {lesson_id} does not exist",
                code=PresentationErrorCode.LESSON_NOT_FOUND,
            )
        return lesson

    def _create_slide_previews(self, lesson) -> List[SlidePreview]:
        """Create a lightweight slide preview list from lesson activities.

        The implementation is deliberately simple: each activity becomes a slide.
        The slide title is the activity title and the key points are the first three
        steps of the activity. Estimated duration is ``30 seconds`` per bullet
        point.
        """
        slide_previews: List[SlidePreview] = []
        # The lesson object is a Pydantic model (LessonDocumentM2). Access the
        # nested content safely.
        activities = getattr(lesson.content, "activities", [])
        for activity in activities:
            title = getattr(activity, "title", "Untitled")
            steps = getattr(activity, "steps", [])[:3]  # first three bullets
            estimated_seconds = max(30, len(steps) * 30)
            slide = SlidePreview(
                title=title,
                key_points=steps,
                estimated_duration_seconds=estimated_seconds,
            )
            slide_previews.append(slide)
        # Fallback: if no activities were defined, create a single generic slide.
        if not slide_previews:
            slide_previews.append(
                SlidePreview(
                    title=lesson.title,
                    key_points=[lesson.objectives[0]] if lesson.objectives else [],
                    estimated_duration_seconds=30,
                )
            )
        return slide_previews

    def generate_preview(
        self,
        presentation_id: str,
        style_id: Optional[str] = None,
    ) -> PresentationPreview:
        """Generate and persist a preview for the given presentation.

        Parameters
        ----------
        presentation_id: str
            Identifier of the lesson/presentation to preview.
        style_id: str, optional
            Identifier of the style to associate with the preview.

        Returns
        -------
        PresentationPreview
            The created preview object.
        """
        logger.info("Generating preview for presentation %s", presentation_id)
        try:
            # 1. Fetch lesson data.
            lesson = self._fetch_lesson(presentation_id)

            # 2. Build slide previews.
            slides = self._create_slide_previews(lesson)
            total_duration = sum(s.estimated_duration_seconds for s in slides)

            # 3. Assemble the preview model.
            preview = PresentationPreview(
                presentation_id=presentation_id,
                generated_at=datetime.utcnow(),
                slides=slides,
                total_estimated_duration_seconds=total_duration,
                style_id=style_id,
            )

            # 4. Persist using the repository.
            self.preview_repo.add_preview(preview)
            logger.info(
                "Preview generated (slides=%d, total_seconds=%d)",
                len(slides),
                total_duration,
            )
            return preview
        except PresentationError:
            # Propagate structured errors unchanged.
            raise
        except Exception as exc:
            # Wrap any unexpected exception.
            logger.exception("Unexpected error generating preview for %s", presentation_id)
            raise create_error_from_exception(
                exc,
                context={"presentation_id": presentation_id},
                code=PresentationErrorCode.INTERNAL_ERROR,
            )

    def get_preview(self, presentation_id: str) -> Optional[PresentationPreview]:
        """Retrieve a stored preview by its presentation identifier.

        Parameters
        ----------
        presentation_id: str
            The identifier of the preview to fetch.

        Returns
        -------
        Optional[PresentationPreview]
            The preview if found, otherwise ``None``.
        """
        logger.debug("Fetching preview for presentation %s", presentation_id)
        return self.preview_repo.get_preview(presentation_id)
