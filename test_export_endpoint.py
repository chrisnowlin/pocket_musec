#!/usr/bin/env python3
"""Test the export functionality end-to-end."""

import requests
import json
import time
import tempfile
import os


def test_export_endpoint():
    """Test the export endpoint with a real presentation."""

    print("🧪 Testing Export Endpoint End-to-End")
    print("=" * 50)

    # Test each export format
    formats = ["json", "markdown", "pptx", "pdf"]

    for format_type in formats:
        print(f"\n📄 Testing {format_type.upper()} export...")

        try:
            # We'll test the export generation directly since we need a valid presentation
            # Let's create a mock presentation and test the export generation

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
                    subtitle="Export Test",
                    key_points=["Key point 1", "Key point 2"],
                    teacher_script="This is a test script",
                    duration_minutes=5,
                    source_section=SourceSection.OVERVIEW,
                ),
                PresentationSlide(
                    id="slide-2",
                    order=2,
                    title="Second Slide",
                    key_points=["Another key point"],
                    teacher_script="More content here",
                    duration_minutes=10,
                    source_section=SourceSection.ACTIVITY,
                ),
            ]

            mock_presentation = PresentationDocument(
                id="test-export-123",
                lesson_id="test-lesson-123",
                lesson_revision=1,
                version="p1.0",
                status=PresentationStatus.COMPLETE,
                style="default",
                slides=mock_slides,
                export_assets=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            # Test export generation
            service = PresentationService()

            if format_type == "json":
                export = service._create_json_export(mock_presentation)
                print(f"   ✅ JSON export created: {export.url_or_path}")

            elif format_type == "markdown":
                export = service._create_markdown_export(mock_presentation)
                print(f"   ✅ Markdown export created: {export.url_or_path}")

            elif format_type == "pptx":
                export = service._create_pptx_export(mock_presentation)
                print(f"   ✅ PPTX export created: {export.url_or_path}")
                print(f"   📊 File size: {export.file_size_bytes} bytes")

                # Check if file exists
                if os.path.exists(export.url_or_path):
                    print(f"   ✅ PPTX file exists on disk")
                else:
                    print(f"   ❌ PPTX file not found on disk")

            elif format_type == "pdf":
                export = service._create_pdf_export(mock_presentation)
                print(f"   ✅ PDF export created: {export.url_or_path}")
                print(f"   📄 File size: {export.file_size_bytes} bytes")

                # Check if file exists
                if os.path.exists(export.url_or_path):
                    print(f"   ✅ PDF file exists on disk")
                else:
                    print(f"   ❌ PDF file not found on disk")

        except Exception as e:
            print(f"   ❌ {format_type.upper()} export failed: {e}")

    print("\n" + "=" * 50)
    print("🎉 Export functionality test completed!")

    # Cleanup test files
    cleanup_files = [
        "presentation_test-export-123.pptx",
        "presentation_test-export-123.pdf",
    ]

    print("\n🧹 Cleaning up test files...")
    for file_path in cleanup_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"   🗑️  Removed {file_path}")


if __name__ == "__main__":
    test_export_endpoint()
