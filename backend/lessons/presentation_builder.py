"""Deterministic slide scaffold builder for presentations.

This module provides pure Python functions to convert LessonDocumentM2
into structured slide decks without external API calls.
"""

from typing import List, Optional
from .presentation_schema import (
    PresentationSlide,
    SourceSection,
    create_slide_from_lesson_section,
)
from .schema_m2 import LessonDocumentM2, LessonActivity


class PresentationScaffoldBuilder:
    """Builds deterministic slide scaffolds from lesson documents."""

    def __init__(self, max_bullets_per_slide: int = 5):
        self.max_bullets_per_slide = max_bullets_per_slide

    def build_scaffold(self, lesson: LessonDocumentM2) -> List[PresentationSlide]:
        """Build a complete slide scaffold from a lesson document.

        Args:
            lesson: The lesson document to convert into slides

        Returns:
            List of presentation slides in order
        """
        slides: List[PresentationSlide] = []
        slide_order = 0

        # Slide 0: Title/Overview
        slides.append(self._build_title_slide(lesson, slide_order))
        slide_order += 1

        # Slide 1: Learning Objectives
        slides.append(self._build_objectives_slide(lesson, slide_order))
        slide_order += 1

        # Slide 2: Materials (if any)
        if lesson.content.materials:
            slides.append(self._build_materials_slide(lesson, slide_order))
            slide_order += 1

        # Slide 3: Prerequisites (if any)
        if lesson.content.prerequisites:
            slides.append(self._build_prerequisites_slide(lesson, slide_order))
            slide_order += 1

        # Slide 4: Warmup (if any)
        if lesson.content.warmup:
            slides.append(self._build_warmup_slide(lesson, slide_order))
            slide_order += 1

        # Slides for each activity
        for activity in lesson.content.activities:
            slides.append(self._build_activity_slide(lesson, activity, slide_order))
            slide_order += 1

        # Assessment slide (if any)
        if lesson.content.assessment:
            slides.append(self._build_assessment_slide(lesson, slide_order))
            slide_order += 1

        # Differentiation slide (if any)
        if lesson.content.differentiation:
            slides.append(self._build_differentiation_slide(lesson, slide_order))
            slide_order += 1

        # Closure/Exit Ticket slide (if any)
        if lesson.content.exit_ticket:
            slides.append(self._build_closure_slide(lesson, slide_order))
            slide_order += 1

        return slides

    def _build_title_slide(
        self, lesson: LessonDocumentM2, order: int
    ) -> PresentationSlide:
        """Build the title/overview slide."""
        # Extract grade and duration info
        grade_info = f"Grade {lesson.grade}" if lesson.grade else ""
        duration_info = (
            f"{lesson.content.timing.total_minutes} minutes"
            if lesson.content.timing.total_minutes
            else ""
        )

        subtitle_parts = [part for part in [grade_info, duration_info] if part]
        subtitle = " | ".join(subtitle_parts) if subtitle_parts else None

        # Extract strand info for key points
        strands_info = []
        if lesson.strands:
            strands_info = [f"Music Strand: {strand}" for strand in lesson.strands[:2]]

        # Add standards count
        if lesson.standards:
            strands_info.append(f"Standards: {len(lesson.standards)} NC standards")

        return create_slide_from_lesson_section(
            order=order,
            title=lesson.title,
            subtitle=subtitle,
            source_section=SourceSection.OVERVIEW,
            key_points=strands_info[: self.max_bullets_per_slide],
            teacher_script=f"Welcome to this {grade_info.lower()} music lesson on {lesson.title.lower()}. "
            f"This lesson is designed for {duration_info.lower()} and aligns with "
            f"North Carolina music education standards.",
            duration_minutes=lesson.content.timing.total_minutes,
        )

    def _build_objectives_slide(
        self, lesson: LessonDocumentM2, order: int
    ) -> PresentationSlide:
        """Build the learning objectives slide."""
        # Use objectives as key points
        objectives = lesson.objectives[: self.max_bullets_per_slide]

        # Extract standard codes for reference
        standard_codes = [standard.code for standard in lesson.standards[:5]]

        return create_slide_from_lesson_section(
            order=order,
            title="Learning Objectives",
            source_section=SourceSection.OBJECTIVES,
            key_points=objectives,
            standard_codes=standard_codes,
            teacher_script="Today we will focus on these specific learning objectives. "
            "Each objective is aligned with North Carolina music standards "
            "and designed to be achievable within our lesson timeframe.",
        )

    def _build_materials_slide(
        self, lesson: LessonDocumentM2, order: int
    ) -> PresentationSlide:
        """Build the materials and setup slide."""
        materials = lesson.content.materials[: self.max_bullets_per_slide]

        return create_slide_from_lesson_section(
            order=order,
            title="Materials & Setup",
            source_section=SourceSection.MATERIALS,
            key_points=materials,
            teacher_script="Before we begin, ensure you have these materials ready. "
            "Having everything prepared will help our lesson run smoothly "
            "and maximize our learning time together.",
        )

    def _build_prerequisites_slide(
        self, lesson: LessonDocumentM2, order: int
    ) -> PresentationSlide:
        """Build the prerequisites slide."""
        # Split prerequisites into bullet points if it's a long text
        prereq_text = lesson.content.prerequisites
        if len(prereq_text) > 100:
            # Split by sentences and create bullets
            sentences = [s.strip() for s in prereq_text.split(".") if s.strip()]
            key_points = sentences[: self.max_bullets_per_slide]
        else:
            key_points = [prereq_text]

        return create_slide_from_lesson_section(
            order=order,
            title="Prerequisites & Prior Knowledge",
            source_section=SourceSection.OVERVIEW,
            key_points=key_points,
            teacher_script="Students should have this prior knowledge before beginning today's lesson. "
            "If needed, take a moment to review these concepts briefly.",
        )

    def _build_warmup_slide(
        self, lesson: LessonDocumentM2, order: int
    ) -> PresentationSlide:
        """Build the warmup activity slide."""
        warmup_text = lesson.content.warmup

        # Split warmup into actionable bullets
        if len(warmup_text) > 150:
            sentences = [s.strip() for s in warmup_text.split(".") if s.strip()]
            key_points = sentences[: self.max_bullets_per_slide]
        else:
            key_points = [warmup_text]

        return create_slide_from_lesson_section(
            order=order,
            title="Warmup Activity",
            source_section=SourceSection.WARMUP,
            key_points=key_points,
            teacher_script="Let's begin with our warmup activity to prepare students for today's learning. "
            "This should take approximately 5-7 minutes and help activate prior knowledge.",
            duration_minutes=5,
        )

    def _build_activity_slide(
        self, lesson: LessonDocumentM2, activity: LessonActivity, order: int
    ) -> PresentationSlide:
        """Build a slide for a specific learning activity."""
        # Use activity steps as key points
        steps = activity.steps[: self.max_bullets_per_slide]

        # Extract aligned standards
        standard_codes = (
            activity.aligned_standards[:5] if activity.aligned_standards else []
        )

        return create_slide_from_lesson_section(
            order=order,
            title=activity.title,
            source_section=SourceSection.ACTIVITY,
            key_points=steps,
            activity_id=activity.id,
            standard_codes=standard_codes,
            teacher_script=f"Guide students through {activity.title.lower()}. "
            f"This activity should take approximately {activity.duration_minutes} minutes. "
            f"Monitor student progress and provide individual support as needed.",
            duration_minutes=activity.duration_minutes,
        )

    def _build_assessment_slide(
        self, lesson: LessonDocumentM2, order: int
    ) -> PresentationSlide:
        """Build the assessment slide."""
        assessment_text = lesson.content.assessment

        # Split assessment into bullets
        if len(assessment_text) > 150:
            sentences = [s.strip() for s in assessment_text.split(".") if s.strip()]
            key_points = sentences[: self.max_bullets_per_slide]
        else:
            key_points = [assessment_text]

        return create_slide_from_lesson_section(
            order=order,
            title="Assessment & Check for Understanding",
            source_section=SourceSection.ASSESSMENT,
            key_points=key_points,
            teacher_script="Use these assessment strategies to check student understanding. "
            "Observe student participation and collect evidence of learning "
            "to inform your next instructional steps.",
        )

    def _build_differentiation_slide(
        self, lesson: LessonDocumentM2, order: int
    ) -> PresentationSlide:
        """Build the differentiation and accommodations slide."""
        diff_text = lesson.content.differentiation

        # Split into bullets if needed
        if len(diff_text) > 150:
            sentences = [s.strip() for s in diff_text.split(".") if s.strip()]
            key_points = sentences[: self.max_bullets_per_slide]
        else:
            key_points = [diff_text]

        return create_slide_from_lesson_section(
            order=order,
            title="Differentiation & Accommodations",
            source_section=SourceSection.DIFFERENTIATION,
            key_points=key_points,
            teacher_script="Consider these differentiation strategies to meet diverse learning needs. "
            "Adjust the pace, provide scaffolding, or extend challenges based on "
            "individual student requirements.",
        )

    def _build_closure_slide(
        self, lesson: LessonDocumentM2, order: int
    ) -> PresentationSlide:
        """Build the closure/exit ticket slide."""
        closure_text = lesson.content.exit_ticket

        # Split into bullets if needed
        if len(closure_text) > 150:
            sentences = [s.strip() for s in closure_text.split(".") if s.strip()]
            key_points = sentences[: self.max_bullets_per_slide]
        else:
            key_points = [closure_text]

        return create_slide_from_lesson_section(
            order=order,
            title="Closure & Exit Ticket",
            source_section=SourceSection.CLOSURE,
            key_points=key_points,
            teacher_script="Conclude the lesson with this closure activity to reinforce learning. "
            "Use the exit ticket to gather quick feedback on student understanding "
            "and prepare for future lessons.",
        )


def build_presentation_scaffold(
    lesson: LessonDocumentM2, max_bullets: int = 5
) -> List[PresentationSlide]:
    """Convenience function to build a presentation scaffold.

    Args:
        lesson: The lesson document to convert
        max_bullets: Maximum number of bullet points per slide

    Returns:
        List of presentation slides
    """
    builder = PresentationScaffoldBuilder(max_bullets_per_slide=max_bullets)
    return builder.build_scaffold(lesson)
