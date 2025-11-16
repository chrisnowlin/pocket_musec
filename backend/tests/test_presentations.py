"""Tests for presentation generation functionality"""

import pytest
import tempfile
import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock

from lessons.presentation_schema import (
    PresentationDocument,
    PresentationSlide,
    PresentationStatus,
    SourceSection,
    build_presentation_document,
)
from lessons.presentation_builder import (
    PresentationScaffoldBuilder,
    build_presentation_scaffold,
)
from lessons.schema_m2 import (
    LessonDocumentM2,
    LessonContent,
    LessonActivity,
    LessonStandard,
    LessonTiming,
)
from auth.models import Lesson
from repositories.presentation_repository import PresentationRepository
from services.presentation_service import PresentationService
from services.presentation_jobs import create_presentation_job, get_job_manager


class TestPresentationSchema:
    """Test presentation schema models and helpers"""

    def test_presentation_slide_creation(self):
        """Test creating a presentation slide"""
        slide = PresentationSlide(
            id="test-slide-1",
            order=1,
            title="Test Slide",
            teacher_script="Teacher script here",
            duration_minutes=5,
            source_section=SourceSection.OVERVIEW,
        )

        assert slide.id == "test-slide-1"
        assert slide.order == 1
        assert slide.source_section == SourceSection.OVERVIEW
        assert slide.title == "Test Slide"
        assert slide.duration_minutes == 5

    def test_presentation_document_creation(self):
        """Test creating a presentation document"""
        slides = [
            PresentationSlide(
                id="slide-1",
                order=1,
                title="Title Slide",
                teacher_script="Welcome students",
                duration_minutes=2,
                source_section=SourceSection.OVERVIEW,
            )
        ]

        presentation = PresentationDocument(
            id="test-presentation-1",
            lesson_id="test-lesson-1",
            lesson_revision=1,
            version="p1.0",
            status=PresentationStatus.COMPLETE,
            slides=slides,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert presentation.id == "test-presentation-1"
        assert presentation.lesson_id == "test-lesson-1"
        assert presentation.lesson_revision == 1
        assert presentation.status == PresentationStatus.COMPLETE
        assert len(presentation.slides) == 1

    def test_build_presentation_document(self):
        """Test building presentation document from slides"""
        slides = [
            PresentationSlide(
                id="slide-1",
                order=1,
                title="Title",
                teacher_script="Script",
                duration_minutes=5,
                source_section=SourceSection.OVERVIEW,
            )
        ]

        presentation = build_presentation_document(
            lesson_id="lesson-1",
            lesson_revision=1,
            slides=slides,
        )

        assert presentation.lesson_id == "lesson-1"
        assert presentation.lesson_revision == 1
        assert presentation.version == "p1.0"
        assert len(presentation.slides) == 1


class TestPresentationBuilder:
    """Test presentation scaffold builder"""

    def test_presentation_scaffold_builder(self):
        """Test the scaffold builder class"""
        builder = PresentationScaffoldBuilder()

        # Create a mock lesson document
        lesson = LessonDocumentM2(
            id="lesson-1",
            version="m2.0",
            title="Test Lesson",
            grade="3rd Grade",
            strands=["Music"],
            standards=[
                LessonStandard(
                    code="M.3.1",
                    title="Music Standard 1",
                    summary="Basic music concepts",
                )
            ],
            objectives=["Objective 1", "Objective 2"],
            content=LessonContent(
                timing=LessonTiming(total_minutes=45),
                activities=[
                    LessonActivity(
                        id="activity-1",
                        title="Activity 1",
                        duration_minutes=10,
                        steps=["Step 1", "Step 2"],
                    )
                ],
                assessment="Assessment description",
                homework="Homework description",
            ),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            revision=1,
        )

        # Build scaffold
        scaffold = builder.build_scaffold(lesson)

        assert len(scaffold) > 0
        assert all(slide.order == i for i, slide in enumerate(scaffold))
        assert all(slide.source_section in SourceSection for slide in scaffold)
        assert all(slide.title for slide in scaffold)
        assert all(slide.teacher_script for slide in scaffold)

    def test_build_presentation_scaffold_function(self):
        """Test the scaffold builder function"""
        lesson = LessonDocumentM2(
            id="lesson-1",
            version="m2.0",
            title="Test Lesson",
            grade="3rd Grade",
            strands=["Music"],
            standards=[
                LessonStandard(
                    code="M.3.1",
                    title="Music Standard 1",
                    summary="Basic music concepts",
                )
            ],
            objectives=["Objective 1"],
            content=LessonContent(
                timing=LessonTiming(total_minutes=45),
                activities=[],
                assessment="Assessment",
                homework="Homework",
            ),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            revision=1,
        )

        scaffold = build_presentation_scaffold(lesson)

        assert isinstance(scaffold, list)
        assert len(scaffold) > 0
        assert all(isinstance(slide, PresentationSlide) for slide in scaffold)


class TestPresentationRepository:
    """Test presentation repository operations"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        # Initialize database
        from repositories.database import DatabaseManager

        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()

        # Run migrations
        from repositories.migrations import MigrationManager

        migration_manager = MigrationManager(db_path)
        migration_manager.migrate()

        yield db_manager

        # Cleanup
        os.unlink(db_path)

    @pytest.fixture
    def presentation_repo(self, temp_db):
        """Create presentation repository for testing"""
        return PresentationRepository(temp_db)

    def test_create_presentation(self, presentation_repo):
        """Test creating a presentation"""
        slides = [
            PresentationSlide(
                id="slide-1",
                order=1,
                title="Title Slide",
                teacher_script="Welcome script",
                duration_minutes=3,
                source_section=SourceSection.OVERVIEW,
            )
        ]

        created = presentation_repo.create_presentation(
            lesson_id="lesson-1",
            lesson_revision=1,
            slides=slides,
        )

        assert created is not None
        assert created.lesson_id == "lesson-1"
        assert created.lesson_revision == 1
        assert created.status == PresentationStatus.PENDING

    def test_get_presentation(self, presentation_repo):
        """Test retrieving a presentation"""
        # Create presentation first
        slides = [
            PresentationSlide(
                id="slide-1",
                order=1,
                title="Title",
                teacher_script="Script",
                duration_minutes=5,
                source_section=SourceSection.OVERVIEW,
            )
        ]

        created = presentation_repo.create_presentation(
            lesson_id="lesson-1",
            lesson_revision=1,
            slides=slides,
        )

        # Retrieve presentation
        retrieved = presentation_repo.get_presentation(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.id == created.id
        assert len(retrieved.slides) == len(created.slides)

    def test_list_presentations_by_lesson(self, presentation_repo):
        """Test listing presentations for a lesson"""
        lesson_id = "test-lesson-1"

        # Create multiple presentations for the same lesson
        for i in range(3):
            slides = [
                PresentationSlide(
                    id=f"slide-{i}-1",
                    order=1,
                    title=f"Presentation {i}",
                    teacher_script=f"Script {i}",
                    duration_minutes=5,
                    source_section=SourceSection.OVERVIEW,
                )
            ]

            presentation_repo.create_presentation(
                lesson_id=lesson_id,
                lesson_revision=i,  # Use different revision to avoid unique constraint
                slides=slides,
            )

        # List presentations
        presentations = presentation_repo.list_presentations_for_lesson(lesson_id)

        assert len(presentations) == 3
        assert all(p.lesson_id == lesson_id for p in presentations)

    def test_delete_presentation(self, presentation_repo):
        """Test deleting a presentation"""
        # Create presentation first
        slides = [
            PresentationSlide(
                id="slide-1",
                order=1,
                title="Title",
                teacher_script="Script",
                duration_minutes=5,
                source_section=SourceSection.OVERVIEW,
            )
        ]

        created = presentation_repo.create_presentation(
            lesson_id="lesson-1",
            lesson_revision=1,
            slides=slides,
        )

        # Delete presentation
        deleted = presentation_repo.delete_presentation(created.id)
        assert deleted is True

        # Verify it's gone
        retrieved = presentation_repo.get_presentation(created.id)
        assert retrieved is None


class TestPresentationService:
    """Test presentation service orchestration"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        from repositories.database import DatabaseManager

        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()

        from repositories.migrations import MigrationManager

        migration_manager = MigrationManager(db_path)
        migration_manager.migrate()

        yield db_manager

        os.unlink(db_path)

    @pytest.fixture
    def presentation_service(self, temp_db):
        """Create presentation service for testing"""
        presentation_repo = PresentationRepository(temp_db)
        lesson_repo = Mock()  # Mock lesson repository

        return PresentationService(
            presentation_repo=presentation_repo,
            lesson_repo=lesson_repo,
            chutes_client=None,  # Disable LLM for testing
        )

    def test_generate_presentation_scaffold_only(self, presentation_service):
        """Test generating presentation without LLM polish"""
        # Mock lesson data (the raw Lesson from repository)
        lesson = Lesson(
            id="lesson-1",
            session_id="session-1",
            user_id="test-user",
            title="Test Lesson",
            content="""{
                "id": "lesson-1",
                "version": "m2.0",
                "title": "Test Lesson",
                "grade": "3rd Grade",
                "strands": ["Music"],
                "standards": [{
                    "code": "M.3.1",
                    "title": "Music Standard 1",
                    "summary": "Basic music concepts"
                }],
                "objectives": ["Objective 1", "Objective 2"],
                "content": {
                    "timing": {"total_minutes": 45},
                    "activities": [{
                        "id": "activity-1",
                        "title": "Activity 1",
                        "duration_minutes": 10,
                        "steps": ["Step 1", "Step 2"]
                    }],
                    "assessment": "Assessment description",
                    "homework": "Homework description"
                },
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "revision": 1
            }""",
        )

        # Mock lesson repository to return the lesson
        presentation_service.lesson_repo.get_lesson = Mock(return_value=lesson)

        # Generate presentation
        presentation = presentation_service.generate_presentation(
            lesson_id="lesson-1", user_id="test-user", use_llm_polish=False
        )

        assert presentation is not None
        assert presentation.lesson_id == "lesson-1"
        assert presentation.status == PresentationStatus.COMPLETE
        assert len(presentation.slides) > 0
        assert all(slide.teacher_script for slide in presentation.slides)


class TestPresentationJobs:
    """Test presentation job management"""

    def test_create_presentation_job(self):
        """Test creating a presentation job"""
        job_id = create_presentation_job(
            lesson_id="test-lesson-1",
            user_id="test-user",
            use_llm_polish=False,
            timeout_seconds=30,
        )

        assert job_id is not None
        assert isinstance(job_id, str)

    def test_job_manager_lifecycle(self):
        """Test job manager lifecycle"""
        job_manager = get_job_manager()

        # Create a job
        job_id = create_presentation_job(
            lesson_id="test-lesson-1",
            user_id="test-user",
            use_llm_polish=False,
            timeout_seconds=30,
        )

        # Check initial status
        status = job_manager.get_job_status(job_id)
        assert status is not None
        assert status["status"] in ["pending", "running", "completed"]

        # Execute job (synchronously for testing)
        # Note: This will fail because the lesson doesn't exist, but we're testing
        # that the job manager handles failures gracefully
        result = job_manager.execute_job(job_id, "default")
        # Result will be None because the lesson doesn't exist - that's expected

        # Check final status - should be failed since lesson doesn't exist
        final_status = job_manager.get_job_status(job_id)
        assert final_status["status"] in ["failed", "completed"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
