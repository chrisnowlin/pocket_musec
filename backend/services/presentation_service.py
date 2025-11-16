"""Presentation generation service orchestration.

This service coordinates the end-to-end presentation generation process,
including scaffold building, optional LLM polishing, and persistence.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

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
from pydantic import ValidationError

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
        """Return the latest presentation for a lesson as a status dict."""
        presentation = self.presentation_repo.latest_by_lesson(lesson_id)
        if not presentation:
            return None

        status_payload = {
            "id": presentation.id,
            "presentation_id": presentation.id,  # backwards compatibility for UI
            "lesson_id": presentation.lesson_id,
            "lesson_revision": presentation.lesson_revision,
            "version": presentation.version,
            "status": presentation.status.value,
            "style": presentation.style,
            "slide_count": len(presentation.slides),
            "created_at": presentation.created_at.isoformat(),
            "updated_at": presentation.updated_at.isoformat(),
            "has_exports": len(presentation.export_assets) > 0,
            "error_code": presentation.error_code,
            "error_message": presentation.error_message,
        }
        return status_payload

    def get_presentation(
        self, presentation_id: str, user_id: str
    ) -> Optional[PresentationDocument]:
        """Get a presentation by ID with user access check."""
        presentation = self.presentation_repo.get_presentation(presentation_id)
        if not presentation:
            return None

        lesson = self.lesson_repo.get_lesson(presentation.lesson_id)
        if not lesson or lesson.user_id != user_id:
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
        lesson = self.lesson_repo.get_lesson(lesson_id)
        if not lesson or lesson.user_id != user_id:
            return None

        metadata_doc: Optional[LessonDocumentM2] = None
        if lesson.metadata:
            try:
                metadata = json.loads(lesson.metadata)
                raw_doc = metadata.get("lesson_document")
                if raw_doc:
                    validate_fn = getattr(LessonDocumentM2, "model_validate", None)
                    metadata_doc = (
                        validate_fn(raw_doc)
                        if callable(validate_fn)
                        else LessonDocumentM2(**raw_doc)
                    )
            except (json.JSONDecodeError, ValidationError) as exc:
                logger.warning(
                    "Failed to parse lesson %s metadata as m2.0: %s", lesson_id, exc
                )

        if metadata_doc:
            return metadata_doc

        # Fallback: attempt to treat lesson.content as JSON for edge cases
        try:
            lesson_data = json.loads(lesson.content)
            return LessonDocumentM2(**lesson_data)
        except Exception as exc:
            logger.warning("Lesson %s lacks structured document: %s", lesson_id, exc)
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

            # Generate PPTX export
            try:
                pptx_export = self._create_pptx_export(presentation)
                self.presentation_repo.add_export_asset(
                    presentation_id=presentation.id,
                    export_asset=pptx_export,
                )
            except Exception as pptx_error:
                logger.warning(f"PPTX export failed: {pptx_error}")

            # Generate PDF export
            try:
                pdf_export = self._create_pdf_export(presentation)
                self.presentation_repo.add_export_asset(
                    presentation_id=presentation.id,
                    export_asset=pdf_export,
                )
            except Exception as pdf_error:
                logger.warning(f"PDF export failed: {pdf_error}")

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
                "presentation": presentation.model_dump(mode="json"),
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

    def _create_pptx_export(
        self, presentation: PresentationDocument
    ) -> PresentationExport:
        """Create PowerPoint PPTX export asset."""
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.enum.text import PP_ALIGN
        from pptx.dml.color import RGBColor
        import tempfile
        import os

        # Create presentation
        prs = Presentation()

        # Add title slide
        title_slide_layout = prs.slide_layouts[0]  # Title slide layout
        slide = prs.slides.add_slide(title_slide_layout)
        title = slide.shapes.title
        subtitle = slide.placeholders[1]

        title.text = (
            presentation.slides[0].title if presentation.slides else "Presentation"
        )
        subtitle.text = (
            f"Generated: {presentation.created_at.strftime('%Y-%m-%d %H:%M')}"
        )

        # Add content slides
        for content_slide in presentation.slides[
            1:
        ]:  # Skip title slide if it's the first one
            # Choose layout based on content
            if content_slide.title and content_slide.key_points:
                slide_layout = prs.slide_layouts[1]  # Title and content
            else:
                slide_layout = prs.slide_layouts[5]  # Blank

            slide = prs.slides.add_slide(slide_layout)

            # Add title
            if content_slide.title and slide.shapes.title:
                slide.shapes.title.text = content_slide.title

            # Add content
            content_parts = []

            if content_slide.key_points:
                content_parts.extend(
                    [f"• {point}" for point in content_slide.key_points]
                )

            if content_slide.teacher_script:
                content_parts.append(f"Teacher: {content_slide.teacher_script}")

            # Add content to slide if we have a content placeholder
            if content_parts and len(slide.placeholders) > 1:
                content_placeholder = slide.placeholders[1]
                content_placeholder.text = "\n".join(content_parts)

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx")
        prs.save(temp_file.name)
        temp_file.close()

        # Get file size
        file_size = os.path.getsize(temp_file.name)

        # Move to permanent location
        final_path = f"presentation_{presentation.id}.pptx"
        os.rename(temp_file.name, final_path)

        return PresentationExport(
            format="pptx",
            url_or_path=final_path,
            generated_at=datetime.utcnow(),
            file_size_bytes=file_size,
        )

    def _create_pdf_export(
        self, presentation: PresentationDocument
    ) -> PresentationExport:
        """Create PDF export asset."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.colors import black, blue
        import tempfile
        import os

        # Create temporary PDF file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_file.close()

        # Create PDF document
        doc = SimpleDocTemplate(temp_file.name, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Add title
        title_style = styles["Title"]
        title_style.textColor = blue
        title = presentation.slides[0].title if presentation.slides else "Presentation"
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))

        # Add metadata
        normal_style = styles["Normal"]
        story.append(
            Paragraph(
                f"<b>Generated:</b> {presentation.created_at.strftime('%Y-%m-%d %H:%M')}",
                normal_style,
            )
        )
        story.append(
            Paragraph(f"<b>Total Slides:</b> {len(presentation.slides)}", normal_style)
        )
        story.append(Spacer(1, 20))

        # Add slides content
        for i, slide in enumerate(presentation.slides):
            # Slide title
            if slide.title:
                heading_style = styles["Heading1"]
                story.append(Paragraph(f"Slide {i + 1}: {slide.title}", heading_style))
                story.append(Spacer(1, 12))

            # Key points
            if slide.key_points:
                story.append(Paragraph("<b>Key Points:</b>", normal_style))
                for point in slide.key_points:
                    story.append(Paragraph(f"• {point}", normal_style))
                story.append(Spacer(1, 6))

            # Teacher script
            if slide.teacher_script:
                story.append(Paragraph("<b>Teacher Script:</b>", normal_style))
                story.append(Paragraph(slide.teacher_script, normal_style))
                story.append(Spacer(1, 6))

            # Duration
            if slide.duration_minutes:
                story.append(
                    Paragraph(
                        f"<b>Duration:</b> {slide.duration_minutes} minutes",
                        normal_style,
                    )
                )
                story.append(Spacer(1, 6))

            # Standards
            if slide.standard_codes:
                story.append(
                    Paragraph(
                        f"<b>Standards:</b> {', '.join(slide.standard_codes)}",
                        normal_style,
                    )
                )
                story.append(Spacer(1, 6))

            # Add separator between slides
            story.append(Spacer(1, 20))

        # Build PDF
        doc.build(story)

        # Get file size
        file_size = os.path.getsize(temp_file.name)

        # Move to permanent location
        final_path = f"presentation_{presentation.id}.pdf"
        os.rename(temp_file.name, final_path)

        return PresentationExport(
            format="pdf",
            url_or_path=final_path,
            generated_at=datetime.utcnow(),
            file_size_bytes=file_size,
        )
