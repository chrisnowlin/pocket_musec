"""OCR engine using Tesseract for text extraction"""

from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class OCREngine:
    """
    Handles OCR processing using Tesseract

    Extracts text from images with preprocessing for better accuracy
    """

    def __init__(self, language: str = "eng"):
        """
        Initialize OCR engine

        Args:
            language: Tesseract language code (default: eng)
        """
        self.language = language

    def extract_text(self, image_path: str) -> Tuple[str, float]:
        """
        Extract text from image using OCR

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            # Open and preprocess image
            image = Image.open(image_path)
            preprocessed = self._preprocess_image(image)

            # Run OCR with data for confidence scores
            ocr_data = pytesseract.image_to_data(
                preprocessed,
                lang=self.language,
                output_type=pytesseract.Output.DICT
            )

            # Extract text and calculate confidence
            extracted_text = pytesseract.image_to_string(
                preprocessed,
                lang=self.language
            ).strip()

            # Calculate average confidence from word-level confidences
            confidences = [
                int(conf) for conf in ocr_data['conf']
                if conf != '-1'  # Filter out invalid confidences
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            logger.info(f"OCR extracted {len(extracted_text)} characters with {avg_confidence:.1f}% confidence")

            return extracted_text, avg_confidence / 100.0  # Convert to 0-1 range

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return "", 0.0

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy

        Args:
            image: PIL Image object

        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        image = image.convert('L')

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)

        # Denoise
        image = image.filter(ImageFilter.MedianFilter(size=3))

        # Increase resolution for better OCR (if small)
        width, height = image.size
        if width < 1000 or height < 1000:
            scale_factor = 2
            new_size = (width * scale_factor, height * scale_factor)
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        return image

    def extract_with_layout(self, image_path: str) -> dict:
        """
        Extract text with layout information

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with layout data (blocks, paragraphs, lines, words)
        """
        try:
            image = Image.open(image_path)
            preprocessed = self._preprocess_image(image)

            # Get detailed layout data
            data = pytesseract.image_to_data(
                preprocessed,
                lang=self.language,
                output_type=pytesseract.Output.DICT
            )

            return data

        except Exception as e:
            logger.error(f"Layout extraction failed: {e}")
            return {}

    def detect_language(self, image_path: str) -> Optional[str]:
        """
        Detect language in image

        Args:
            image_path: Path to image file

        Returns:
            Detected language code or None
        """
        try:
            image = Image.open(image_path)
            preprocessed = self._preprocess_image(image)

            # Detect languages with OSD (Orientation and Script Detection)
            osd_data = pytesseract.image_to_osd(preprocessed)

            # Parse language from OSD output
            for line in osd_data.split('\n'):
                if line.startswith('Script:'):
                    script = line.split(':')[1].strip()
                    return script

            return None

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return None
