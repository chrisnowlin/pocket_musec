"""Main image processor orchestrating OCR and vision analysis"""

from pathlib import Path
from typing import Dict, Optional, Tuple
import json
import logging

from .ocr_engine import OCREngine
from .vision_analyzer import VisionAnalyzer
from .image_storage import ImageStorage

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Orchestrates complete image processing pipeline

    Combines OCR, vision analysis, and storage
    """

    def __init__(
        self,
        storage_path: str = "data/images",
        api_key: Optional[str] = None
    ):
        """
        Initialize image processor

        Args:
            storage_path: Directory for image storage
            api_key: Chutes API key for vision analysis
        """
        self.ocr_engine = OCREngine()
        self.vision_analyzer = VisionAnalyzer(api_key=api_key)
        self.storage = ImageStorage(storage_path=storage_path)

    def process_image(
        self,
        image_path: str,
        user_id: str,
        original_filename: str,
        analyze_vision: bool = True
    ) -> Dict:
        """
        Process image with OCR and optional vision analysis

        Args:
            image_path: Path to image file
            user_id: User ID
            original_filename: Original filename
            analyze_vision: Whether to run vision analysis

        Returns:
            Dictionary with processing results
        """
        try:
            logger.info(f"Processing image: {original_filename}")

            # Store image
            stored_path, compressed_path, file_size = self.storage.store_image(
                image_path=image_path,
                user_id=user_id,
                original_filename=original_filename
            )

            # Run OCR
            extracted_text, ocr_confidence = self.ocr_engine.extract_text(image_path)

            # Run vision analysis if enabled and available
            vision_summary = None
            if analyze_vision and self.vision_analyzer.is_available():
                vision_summary = self.vision_analyzer.analyze_image(image_path)

            # Detect image type
            image_type = self._detect_image_type(extracted_text, vision_summary)

            # Get image metadata
            metadata = self._extract_metadata(image_path)

            result = {
                "stored_path": stored_path,
                "compressed_path": compressed_path,
                "file_size": file_size,
                "mime_type": self._get_mime_type(original_filename),
                "extracted_text": extracted_text,
                "ocr_confidence": ocr_confidence,
                "vision_summary": vision_summary,
                "image_type": image_type,
                "metadata": metadata
            }

            logger.info(f"Image processed successfully: {image_type}")
            return result

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise

    def process_sheet_music(
        self,
        image_path: str,
        user_id: str,
        original_filename: str
    ) -> Dict:
        """
        Process sheet music image with specialized analysis

        Args:
            image_path: Path to sheet music image
            user_id: User ID
            original_filename: Original filename

        Returns:
            Processing results with musical elements
        """
        # Basic processing
        result = self.process_image(
            image_path=image_path,
            user_id=user_id,
            original_filename=original_filename,
            analyze_vision=False  # We'll use specialized analysis
        )

        # Specialized sheet music analysis
        if self.vision_analyzer.is_available():
            music_analysis = self.vision_analyzer.analyze_sheet_music(image_path)
            if music_analysis:
                result['music_analysis'] = music_analysis
                result['image_type'] = 'sheet_music'

        return result

    def process_diagram(
        self,
        image_path: str,
        user_id: str,
        original_filename: str
    ) -> Dict:
        """
        Process instructional diagram with specialized analysis

        Args:
            image_path: Path to diagram image
            user_id: User ID
            original_filename: Original filename

        Returns:
            Processing results with diagram elements
        """
        # Basic processing
        result = self.process_image(
            image_path=image_path,
            user_id=user_id,
            original_filename=original_filename,
            analyze_vision=False  # We'll use specialized analysis
        )

        # Specialized diagram analysis
        if self.vision_analyzer.is_available():
            diagram_analysis = self.vision_analyzer.analyze_diagram(image_path)
            if diagram_analysis:
                result['diagram_analysis'] = diagram_analysis
                result['image_type'] = 'instructional_diagram'

        return result

    def batch_process(
        self,
        image_paths: list,
        user_id: str,
        analyze_vision: bool = True
    ) -> list:
        """
        Process multiple images in batch

        Args:
            image_paths: List of (path, filename) tuples
            user_id: User ID
            analyze_vision: Whether to run vision analysis

        Returns:
            List of processing results
        """
        results = []

        for image_path, filename in image_paths:
            try:
                result = self.process_image(
                    image_path=image_path,
                    user_id=user_id,
                    original_filename=filename,
                    analyze_vision=analyze_vision
                )
                results.append({
                    "filename": filename,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                logger.error(f"Batch processing failed for {filename}: {e}")
                results.append({
                    "filename": filename,
                    "status": "error",
                    "error": str(e)
                })

        return results

    def _detect_image_type(
        self,
        extracted_text: str,
        vision_summary: Optional[str]
    ) -> str:
        """
        Detect image type based on content

        Args:
            extracted_text: OCR extracted text
            vision_summary: Vision analysis summary

        Returns:
            Image type string
        """
        # Check for musical notation indicators
        music_keywords = [
            'treble', 'bass', 'clef', 'sharp', 'flat', 'measure',
            'tempo', 'allegro', 'andante', 'forte', 'piano'
        ]

        text_lower = extracted_text.lower()
        vision_lower = (vision_summary or "").lower()

        if any(keyword in text_lower or keyword in vision_lower for keyword in music_keywords):
            return "sheet_music"

        # Check for diagram indicators
        diagram_keywords = [
            'diagram', 'chart', 'illustration', 'step', 'process',
            'figure', 'instruction'
        ]

        if any(keyword in text_lower or keyword in vision_lower for keyword in diagram_keywords):
            return "instructional_diagram"

        # Default to general
        return "general"

    def _extract_metadata(self, image_path: str) -> Dict:
        """
        Extract image metadata

        Args:
            image_path: Path to image file

        Returns:
            Metadata dictionary
        """
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "size_bytes": Path(image_path).stat().st_size
                }
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {}

    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename"""
        suffix = Path(filename).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff'
        }
        return mime_types.get(suffix, 'image/jpeg')

    def get_storage_info(self) -> Dict:
        """Get storage quota information"""
        return self.storage.get_quota_info()

    def cleanup_user_images(self, user_id: str) -> int:
        """Delete all images for a user"""
        return self.storage.cleanup_user_images(user_id)
