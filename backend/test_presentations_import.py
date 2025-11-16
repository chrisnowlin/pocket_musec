#!/usr/bin/env python3
"""Test script to verify presentation imports work correctly"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)


def test_presentation_imports():
    """Test that all presentation-related modules can be imported"""

    print("Testing presentation imports...")

    try:
        # Test presentation schema
        from lessons.presentation_schema import (
            PresentationDocument,
            PresentationSlide,
            PresentationStatus,
            PresentationExport,
        )

        print("✅ Presentation schema imports successful")

        # Test presentation builder
        from lessons.presentation_builder import (
            PresentationScaffoldBuilder,
            build_presentation_scaffold,
        )

        print("✅ Presentation builder imports successful")

        # Test presentation polish
        from lessons.presentation_polish import (
            PresentationPolishService,
            polish_presentation_slides,
        )

        print("✅ Presentation polish imports successful")

        # Test presentation repository
        from repositories.presentation_repository import PresentationRepository

        print("✅ Presentation repository imports successful")

        # Test presentation service
        from services.presentation_service import PresentationService

        print("✅ Presentation service imports successful")

        # Test presentation jobs
        from services.presentation_jobs import (
            get_job_manager,
            create_presentation_job,
            get_presentation_job_status,
        )

        print("✅ Presentation jobs imports successful")

        print("\n🎉 All presentation imports successful!")
        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_presentation_imports()
    sys.exit(0 if success else 1)
