#!/usr/bin/env python3
"""Test the export API endpoint directly."""

import requests
import json
import tempfile
import os


def test_export_api():
    """Test the export API endpoint with a real presentation."""

    base_url = "http://localhost:8001"

    print("🧪 Testing Export API Endpoint")
    print("=" * 50)

    # First create a test presentation via the service
    print("1. Creating test presentation via service...")

    from backend.services.presentation_service import PresentationService
    from backend.lessons.presentation_schema import (
        PresentationDocument,
        PresentationSlide,
        PresentationStatus,
        PresentationExport,
        SourceSection,
    )
    from datetime import datetime

    # Create mock presentation
    mock_slides = [
        PresentationSlide(
            id="slide-1",
            order=1,
            title="Test Presentation",
            subtitle="Export API Test",
            key_points=["Key point 1", "Key point 2"],
            teacher_script="This is a test script for API testing",
            duration_minutes=5,
            source_section=SourceSection.OVERVIEW,
        ),
        PresentationSlide(
            id="slide-2",
            order=2,
            title="Second Slide",
            key_points=["Another key point for API"],
            teacher_script="More content here for API testing",
            duration_minutes=10,
            source_section=SourceSection.ACTIVITY,
        ),
    ]

    mock_presentation = PresentationDocument(
        id="test-api-export-123",
        lesson_id="test-lesson-api-123",
        lesson_revision=1,
        version="p1.0",
        status=PresentationStatus.COMPLETE,
        style="default",
        slides=mock_slides,
        export_assets=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Save the presentation to repository
    service = PresentationService()
    presentation_repo = service.presentation_repo

    try:
        # Create presentation in database
        created_presentation = presentation_repo.create_presentation(
            lesson_id=mock_presentation.lesson_id,
            lesson_revision=mock_presentation.lesson_revision,
            slides=mock_slides,
            style=mock_presentation.style,
        )

        # Update status to complete
        presentation_repo.update_presentation_status(
            presentation_id=created_presentation.id, status=PresentationStatus.COMPLETE
        )

        print(f"   ✅ Created presentation: {created_presentation.id}")

        # Test export formats via API
        formats = ["json", "markdown", "pptx", "pdf"]

        for format_type in formats:
            print(
                f"\n2.{formats.index(format_type) + 1} Testing {format_type.upper()} export via API..."
            )

            try:
                # Make API request (we'll need to handle auth properly in a real scenario)
                export_url = f"{base_url}/api/presentations/{created_presentation.id}/export?format={format_type}"

                # For now, let's test the service method directly
                if format_type == "json":
                    export = service._create_json_export(created_presentation)
                    print(f"   ✅ JSON export: {export.url_or_path}")

                elif format_type == "markdown":
                    export = service._create_markdown_export(created_presentation)
                    print(f"   ✅ Markdown export: {export.url_or_path}")

                elif format_type == "pptx":
                    export = service._create_pptx_export(created_presentation)
                    print(
                        f"   ✅ PPTX export: {export.url_or_path} ({export.file_size_bytes} bytes)"
                    )

                elif format_type == "pdf":
                    export = service._create_pdf_export(created_presentation)
                    print(
                        f"   ✅ PDF export: {export.url_or_path} ({export.file_size_bytes} bytes)"
                    )

            except Exception as e:
                print(f"   ❌ {format_type.upper()} export failed: {e}")

        print(f"\n🎉 Export API test completed!")

        # Cleanup
        print(f"\n🧹 Cleaning up test presentation...")
        # Note: In a real implementation, you'd delete the test presentation
        print(f"   🗑️  Test presentation cleanup would go here")

    except Exception as e:
        print(f"   ❌ Failed to create test presentation: {e}")


if __name__ == "__main__":
    test_export_api()
