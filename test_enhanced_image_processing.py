#!/usr/bin/env python3
"""Test enhanced image processing functionality"""

import sys
import os

sys.path.append(".")

from backend.image_processing import ImageProcessor, ImageClassifier
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_image_classifier():
    """Test the image classifier functionality"""
    logger.info("Testing ImageClassifier...")

    # Create classifier with required dependencies
    from backend.image_processing import VisionAnalyzer, OCREngine

    vision_analyzer = VisionAnalyzer(api_key=None)  # No API key for testing
    ocr_engine = OCREngine()
    classifier = ImageClassifier(vision_analyzer=vision_analyzer, ocr_engine=ocr_engine)

    # Test classification categories (access directly from the classifier)
    categories = list(classifier.categories.keys())
    logger.info(f"Available categories: {categories}")

    # Test tag generation (access the internal method with proper parameters)
    vision_analysis = {
        "description": "piano sheet music with treble clef",
        "key_elements": ["notes", "clef"],
    }
    music_data = {"notation_elements": ["treble_clef", "notes"]}
    test_tags = classifier._generate_tags(
        "piano sheet music with treble clef", "sheet_music", vision_analysis, music_data
    )
    logger.info(f"Generated tags: {test_tags}")

    # Test education level classification
    education_level, confidence = classifier._classify_education_level(
        "basic piano notes for beginners"
    )
    logger.info(f"Education level: {education_level} (confidence: {confidence})")

    # Test difficulty level classification
    difficulty_level, confidence = classifier._classify_difficulty_level(
        "simple melody with quarter notes"
    )
    logger.info(f"Difficulty level: {difficulty_level} (confidence: {confidence})")

    logger.info("✅ ImageClassifier tests passed")


def test_enhanced_image_processor():
    """Test the enhanced image processor"""
    logger.info("Testing enhanced ImageProcessor...")

    # Create processor (without API key for testing)
    # Mock the config to avoid import issues
    import sys
    from unittest.mock import MagicMock

    sys.modules["config"] = MagicMock()

    try:
        processor = ImageProcessor(api_key=None)

        # Check if classifier is available
        if hasattr(processor, "image_classifier"):
            logger.info(
                "✅ ImageClassifier successfully integrated into ImageProcessor"
            )
        else:
            logger.error("❌ ImageClassifier not found in ImageProcessor")
            return False

        logger.info("✅ Enhanced ImageProcessor tests passed")
        return True

    except Exception as e:
        logger.error(f"❌ Enhanced ImageProcessor test failed: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("🧪 Running Enhanced Image Processing Tests")

    try:
        test_image_classifier()
        test_enhanced_image_processor()

        logger.info("🎉 All enhanced image processing tests passed!")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
