"""Backend lesson-related modules"""

from .schema_m2 import (
    LessonDocumentM2,
    LessonStandard,
    LessonActivity,
    LessonTiming,
    LessonContent,
    build_m2_lesson_document,
)

from .presentation_schema import (
    PresentationDocument,
    PresentationSlide,
    PresentationExport,
    PresentationStatus,
    SourceSection,
    build_presentation_document,
    create_slide_from_lesson_section,
)

from .presentation_builder import (
    PresentationScaffoldBuilder,
    build_presentation_scaffold,
)

__all__ = [
    # Lesson schema m2.0
    "LessonDocumentM2",
    "LessonStandard",
    "LessonActivity",
    "LessonTiming",
    "LessonContent",
    "build_m2_lesson_document",
    # Presentation schema p1.0
    "PresentationDocument",
    "PresentationSlide",
    "PresentationExport",
    "PresentationStatus",
    "SourceSection",
    "build_presentation_document",
    "create_slide_from_lesson_section",
    # Presentation builder
    "PresentationScaffoldBuilder",
    "build_presentation_scaffold",
]
