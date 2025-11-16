"""OCR engine using Tesseract for text extraction"""

from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from typing import Tuple, Optional, Dict
import logging
import numpy as np
import cv2

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
                preprocessed, lang=self.language, output_type=pytesseract.Output.DICT
            )

            # Extract text and calculate confidence
            extracted_text = pytesseract.image_to_string(
                preprocessed, lang=self.language
            ).strip()

            # Calculate average confidence from word-level confidences
            confidences = [
                int(conf)
                for conf in ocr_data["conf"]
                if conf != "-1"  # Filter out invalid confidences
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            logger.info(
                f"OCR extracted {len(extracted_text)} characters with {avg_confidence:.1f}% confidence"
            )

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
        image = image.convert("L")

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
                preprocessed, lang=self.language, output_type=pytesseract.Output.DICT
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
            for line in osd_data.split("\n"):
                if line.startswith("Script:"):
                    script = line.split(":")[1].strip()
                    return script

            return None

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return None

    def preprocess_music_notation(self, image_path: str) -> Image.Image:
        """
        Specialized preprocessing for music notation images

        Args:
            image_path: Path to image file

        Returns:
            Preprocessed PIL Image enhanced for music notation
        """
        try:
            image = Image.open(image_path)

            # Convert to grayscale if not already
            if image.mode != "L":
                image = image.convert("L")

            # Enhance contrast for better notation visibility
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)

            # Apply sharpening filter
            image = image.filter(ImageFilter.SHARPEN)

            # Convert to numpy array for OpenCV operations
            img_array = np.array(image)

            # Apply adaptive thresholding for better binarization
            binary = cv2.adaptiveThreshold(
                img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Remove small noise
            kernel = np.ones((2, 2), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            # Convert back to PIL Image
            processed_image = Image.fromarray(binary)

            return processed_image

        except Exception as e:
            logger.error(f"Music notation preprocessing failed: {e}")
            # Fallback to regular preprocessing
            image = Image.open(image_path)
            return self._preprocess_image(image)

    def extract_music_notation(self, image_path: str) -> Dict:
        """
        Extract music notation elements with specialized processing

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with extracted music notation elements
        """
        try:
            # Use specialized preprocessing for music notation
            processed_image = self.preprocess_music_notation(image_path)

            # Run OCR with music-specific configuration
            custom_config = r"--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGabcdefg♭♯♮𝄞𝄢𝄡𝄟𝄠𝄝𝄤𝄥𝄦𝄧𝄨𝄩𝄪𝄫𝄬𝄭𝄮𝄯𝄰𝄱𝄲𝄳𝄴𝄵𝄶𝄷𝄸𝄹𝄺𝄻𝄼𝄽𝄾𝄿"

            # Extract text with confidence data
            ocr_data = pytesseract.image_to_data(
                processed_image,
                lang=self.language,
                config=custom_config,
                output_type=pytesseract.Output.DICT,
            )

            # Process OCR results for music elements
            music_elements: Dict = {
                "notation_symbols": [],
                "pitch_names": [],
                "numbers": [],
                "accidentals": [],
                "clefs": [],
                "confidence_scores": [],
            }

            # Categorize extracted text
            for i, text in enumerate(ocr_data["text"]):
                if text.strip():
                    confidence = ocr_data["conf"][i] / 100.0
                    music_elements["confidence_scores"].append(confidence)

                    # Music symbol categorization
                    if any(char in text for char in ["♭", "♯", "♮"]):
                        music_elements["accidentals"].append(text)
                    elif any(char in text for char in ["𝄞", "𝄢", "𝄡", "𝄟", "𝄠"]):
                        music_elements["clefs"].append(text)
                    elif any(
                        char in text
                        for char in [
                            "C",
                            "D",
                            "E",
                            "F",
                            "G",
                            "A",
                            "B",
                            "c",
                            "d",
                            "e",
                            "f",
                            "g",
                            "a",
                            "b",
                        ]
                    ):
                        music_elements["pitch_names"].append(text)
                    elif text.isdigit():
                        music_elements["numbers"].append(text)
                    else:
                        music_elements["notation_symbols"].append(text)

            # Calculate overall confidence
            avg_confidence = (
                sum(music_elements["confidence_scores"])
                / len(music_elements["confidence_scores"])
                if music_elements["confidence_scores"]
                else 0.0
            )

            music_elements.update(
                {
                    "average_confidence": avg_confidence,
                    "total_elements": len(music_elements["confidence_scores"]),
                }
            )

            return music_elements

        except Exception as e:
            logger.error(f"Music notation extraction failed: {e}")
            return {"error": str(e), "total_elements": 0}

    def extract_with_music_mode(self, image_path: str) -> Tuple:
        """
        Extract text with music notation enhancement

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (extracted_text, confidence_score, music_elements)
        """
        try:
            # Get regular text extraction
            text, confidence = self.extract_text(image_path)

            # Get music notation elements
            music_elements = self.extract_music_notation(image_path)

            # Combine results
            enhanced_text = text
            if music_elements.get("notation_symbols"):
                enhanced_text += (
                    f" [Music symbols: {', '.join(music_elements['notation_symbols'])}]"
                )

            # Enhanced confidence calculation
            music_confidence = music_elements.get("average_confidence", 0.0)
            enhanced_confidence = max(confidence, music_confidence)

            return enhanced_text, enhanced_confidence, music_elements

        except Exception as e:
            logger.error(f"Enhanced music mode extraction failed: {e}")
            # Fallback to regular extraction
            return self.extract_text(image_path) + ({},)
