"""Image classification and auto-tagging system"""

from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import json

from .vision_analyzer import VisionAnalyzer
from .ocr_engine import OCREngine

logger = logging.getLogger(__name__)


class ImageClassifier:
    """
    Intelligent image classification and auto-tagging system

    Analyzes images to automatically classify content and generate relevant tags
    for improved searchability and organization.
    """

    def __init__(self, vision_analyzer: VisionAnalyzer, ocr_engine: OCREngine):
        """
        Initialize classifier with analysis engines

        Args:
            vision_analyzer: Vision analyzer instance
            ocr_engine: OCR engine instance
        """
        self.vision_analyzer = vision_analyzer
        self.ocr_engine = ocr_engine

        # Classification categories and keywords
        self.categories = {
            "sheet_music": {
                "keywords": [
                    "clef",
                    "staff",
                    "measure",
                    "note",
                    "rest",
                    "treble",
                    "bass",
                    "allegro",
                    "andante",
                    "tempo",
                    "key",
                    "signature",
                    "sharp",
                    "flat",
                    "natural",
                ],
                "visual_indicators": [
                    "staff lines",
                    "musical notation",
                    "notes on staff",
                    "clef symbols",
                ],
                "confidence_threshold": 0.7,
            },
            "musical_instruments": {
                "keywords": [
                    "piano",
                    "violin",
                    "guitar",
                    "flute",
                    "drum",
                    "trumpet",
                    "saxophone",
                    "cello",
                    "clarinet",
                    "oboe",
                ],
                "visual_indicators": [
                    "instrument",
                    "strings",
                    "keys",
                    "fretboard",
                    "bow",
                    "mouthpiece",
                ],
                "confidence_threshold": 0.6,
            },
            "instructional_diagram": {
                "keywords": [
                    "diagram",
                    "chart",
                    "illustration",
                    "figure",
                    "step",
                    "process",
                    "instruction",
                    "how to",
                    "technique",
                ],
                "visual_indicators": [
                    "arrows",
                    "labels",
                    "numbered steps",
                    "flowchart",
                    "annotation",
                ],
                "confidence_threshold": 0.6,
            },
            "music_theory": {
                "keywords": [
                    "theory",
                    "harmony",
                    "chord",
                    "scale",
                    "interval",
                    "progression",
                    "cadence",
                    "mode",
                ],
                "visual_indicators": [
                    "circle of fifths",
                    "chord chart",
                    "scale diagram",
                    "interval chart",
                ],
                "confidence_threshold": 0.7,
            },
            "performance": {
                "keywords": [
                    "performance",
                    "concert",
                    "recital",
                    "orchestra",
                    "ensemble",
                    "solo",
                    "conductor",
                    "stage",
                ],
                "visual_indicators": [
                    "stage",
                    "audience",
                    "music stands",
                    "conductor podium",
                    "ensemble seating",
                ],
                "confidence_threshold": 0.6,
            },
            "classroom": {
                "keywords": [
                    "classroom",
                    "teacher",
                    "student",
                    "lesson",
                    "school",
                    "education",
                    "blackboard",
                    "whiteboard",
                ],
                "visual_indicators": [
                    "desks",
                    "chairs",
                    "blackboard",
                    "teacher",
                    "students",
                    "classroom setting",
                ],
                "confidence_threshold": 0.6,
            },
            "handwritten": {
                "keywords": ["handwritten", "manuscript", "script", "cursive"],
                "visual_indicators": [
                    "handwriting",
                    "manuscript style",
                    "personal notation",
                ],
                "confidence_threshold": 0.8,
            },
        }

        # Educational level indicators
        self.education_levels = {
            "elementary": {
                "keywords": [
                    "elementary",
                    "primary",
                    "grade",
                    "beginner",
                    "basic",
                    "simple",
                ],
                "confidence_threshold": 0.6,
            },
            "middle_school": {
                "keywords": [
                    "middle school",
                    "junior high",
                    "grade 6",
                    "grade 7",
                    "grade 8",
                ],
                "confidence_threshold": 0.6,
            },
            "high_school": {
                "keywords": [
                    "high school",
                    "secondary",
                    "grade 9",
                    "grade 10",
                    "grade 11",
                    "grade 12",
                    "advanced",
                ],
                "confidence_threshold": 0.6,
            },
            "college": {
                "keywords": [
                    "university",
                    "college",
                    "conservatory",
                    "advanced",
                    "professional",
                    "degree",
                ],
                "confidence_threshold": 0.7,
            },
        }

        # Difficulty level indicators
        self.difficulty_levels = {
            "beginner": {
                "keywords": [
                    "beginner",
                    "basic",
                    "elementary",
                    "introductory",
                    "level 1",
                    "starting",
                ],
                "confidence_threshold": 0.6,
            },
            "intermediate": {
                "keywords": [
                    "intermediate",
                    "moderate",
                    "level 2",
                    "grade 2",
                    "some experience",
                ],
                "confidence_threshold": 0.6,
            },
            "advanced": {
                "keywords": [
                    "advanced",
                    "difficult",
                    "complex",
                    "level 3",
                    "professional",
                    "expert",
                ],
                "confidence_threshold": 0.7,
            },
        }

    def classify_image(self, image_path: str) -> Dict[str, any]:
        """
        Classify image and generate auto-tags

        Args:
            image_path: Path to image file

        Returns:
            Classification dictionary with categories, tags, and metadata
        """
        try:
            logger.info(f"Classifying image: {Path(image_path).name}")

            # Get structured vision analysis
            vision_analysis = self.vision_analyzer.analyze_image_structured(
                image_path, "general"
            )

            # Get OCR text analysis
            ocr_text, ocr_confidence, music_data = (
                self.ocr_engine.extract_with_music_mode(image_path)
            )

            # Combine all text data
            all_text = f"{ocr_text} {vision_analysis.get('description', '') if vision_analysis else ''}".lower()

            # Classify main category
            primary_category, category_confidence = self._classify_category(
                all_text, vision_analysis
            )

            # Determine educational level
            education_level, education_confidence = self._classify_education_level(
                all_text
            )

            # Determine difficulty level
            difficulty_level, difficulty_confidence = self._classify_difficulty_level(
                all_text
            )

            # Generate auto-tags
            auto_tags = self._generate_tags(
                all_text, primary_category, vision_analysis, music_data
            )

            # Extract musical elements if applicable
            musical_elements = self._extract_musical_metadata(
                music_data, vision_analysis
            )

            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(
                category_confidence,
                education_confidence,
                difficulty_confidence,
                ocr_confidence,
            )

            classification = {
                "primary_category": primary_category,
                "category_confidence": category_confidence,
                "educational_level": education_level,
                "education_confidence": education_confidence,
                "difficulty_level": difficulty_level,
                "difficulty_confidence": difficulty_confidence,
                "auto_tags": auto_tags,
                "musical_elements": musical_elements,
                "ocr_confidence": ocr_confidence,
                "overall_confidence": overall_confidence,
                "processing_metadata": {
                    "has_vision_analysis": vision_analysis is not None,
                    "has_ocr_text": len(ocr_text.strip()) > 0,
                    "has_musical_symbols": len(music_data.get("musical_symbols", []))
                    > 0,
                    "text_length": len(all_text),
                    "vision_confidence": vision_analysis.get("confidence_score", 0.0)
                    if vision_analysis
                    else 0.0,
                },
            }

            logger.info(
                f"Image classified as: {primary_category} ({category_confidence:.2f} confidence)"
            )
            return classification

        except Exception as e:
            logger.error(f"Image classification failed: {e}")
            return {
                "primary_category": "unknown",
                "category_confidence": 0.0,
                "educational_level": "unknown",
                "education_confidence": 0.0,
                "difficulty_level": "unknown",
                "difficulty_confidence": 0.0,
                "auto_tags": [],
                "musical_elements": {},
                "ocr_confidence": 0.0,
                "overall_confidence": 0.0,
                "error": str(e),
            }

    def _classify_category(
        self, text: str, vision_analysis: Optional[Dict]
    ) -> Tuple[str, float]:
        """Classify the main category of the image"""
        category_scores = {}

        # Score based on text keywords
        for category, config in self.categories.items():
            keyword_matches = sum(
                1 for keyword in config["keywords"] if keyword in text
            )
            text_score = keyword_matches / len(config["keywords"])
            category_scores[category] = text_score

        # Boost scores based on vision analysis
        if vision_analysis:
            vision_type = vision_analysis.get("image_type", "").lower()
            vision_desc = vision_analysis.get("description", "").lower()

            for category in category_scores:
                if category.replace("_", "") in vision_type:
                    category_scores[category] += 0.3

                # Check for visual indicators in description
                for indicator in self.categories[category]["visual_indicators"]:
                    if indicator in vision_desc:
                        category_scores[category] += 0.2

        # Select best category
        if not category_scores:
            return "unknown", 0.0

        best_category = max(category_scores, key=category_scores.get)
        best_score = category_scores[best_category]

        # Apply confidence threshold
        threshold = self.categories[best_category]["confidence_threshold"]
        if best_score >= threshold:
            return best_category, min(best_score, 1.0)
        else:
            return "general", best_score

    def _classify_education_level(self, text: str) -> Tuple[str, float]:
        """Classify the educational level"""
        level_scores = {}

        for level, config in self.education_levels.items():
            keyword_matches = sum(
                1 for keyword in config["keywords"] if keyword in text
            )
            score = keyword_matches / len(config["keywords"])
            level_scores[level] = score

        if not level_scores:
            return "unknown", 0.0

        best_level = max(level_scores, key=level_scores.get)
        best_score = level_scores[best_level]

        threshold = self.education_levels[best_level]["confidence_threshold"]
        if best_score >= threshold:
            return best_level, min(best_score, 1.0)
        else:
            return "unknown", best_score

    def _classify_difficulty_level(self, text: str) -> Tuple[str, float]:
        """Classify the difficulty level"""
        level_scores = {}

        for level, config in self.difficulty_levels.items():
            keyword_matches = sum(
                1 for keyword in config["keywords"] if keyword in text
            )
            score = keyword_matches / len(config["keywords"])
            level_scores[level] = score

        if not level_scores:
            return "unknown", 0.0

        best_level = max(level_scores, key=level_scores.get)
        best_score = level_scores[best_level]

        threshold = self.difficulty_levels[best_level]["confidence_threshold"]
        if best_score >= threshold:
            return best_level, min(best_score, 1.0)
        else:
            return "unknown", best_score

    def _generate_tags(
        self,
        text: str,
        category: str,
        vision_analysis: Optional[Dict],
        music_data: Dict,
    ) -> List[str]:
        """Generate relevant auto-tags"""
        tags = set()

        # Add category as tag
        tags.add(category)

        # Add educational and difficulty tags
        if "educational_level" in locals():
            tags.add(f"level: {education_level}")
        if "difficulty_level" in locals():
            tags.add(f"difficulty: {difficulty_level}")

        # Extract keywords from text
        all_keywords = []
        for config in self.categories.values():
            all_keywords.extend(config["keywords"])

        for keyword in all_keywords:
            if keyword in text and len(keyword) > 2:  # Filter very short keywords
                tags.add(keyword)

        # Add vision-based tags
        if vision_analysis:
            key_elements = vision_analysis.get("key_elements", [])
            tags.update(
                [
                    elem.lower().replace(" ", "_")
                    for elem in key_elements
                    if len(elem) > 2
                ]
            )

        # Add musical element tags
        if music_data.get("musical_symbols"):
            tags.add("has_musical_notation")

        if music_data.get("detected_elements"):
            for element_type, elements in music_data["detected_elements"].items():
                if elements:
                    tags.add(f"has_{element_type}")

        # Clean up and limit tags
        cleaned_tags = []
        for tag in tags:
            if isinstance(tag, str) and len(tag.strip()) > 0:
                cleaned_tags.append(tag.strip().lower())

        # Remove duplicates and limit to 20 most relevant tags
        unique_tags = list(set(cleaned_tags))[:20]

        return sorted(unique_tags)

    def _extract_musical_metadata(
        self, music_data: Dict, vision_analysis: Optional[Dict]
    ) -> Dict:
        """Extract musical metadata from analysis results"""
        musical_elements = {
            "has_notation": len(music_data.get("musical_symbols", [])) > 0,
            "notation_symbols": music_data.get("musical_symbols", []),
            "detected_elements": music_data.get("detected_elements", {}),
            "symbol_count": music_data.get("total_symbols", 0),
            "text_count": music_data.get("total_text", 0),
        }

        # Add vision-based musical analysis if available
        if vision_analysis and vision_analysis.get("image_type") == "sheet_music":
            musical_elements.update(
                {
                    "title": vision_analysis.get("title"),
                    "composer": vision_analysis.get("composer"),
                    "key_signature": vision_analysis.get("key_signature"),
                    "time_signature": vision_analysis.get("time_signature"),
                    "tempo": vision_analysis.get("tempo"),
                    "instruments": vision_analysis.get("instruments", []),
                }
            )

        return musical_elements

    def _calculate_overall_confidence(
        self,
        category_conf: float,
        education_conf: float,
        difficulty_conf: float,
        ocr_conf: float,
    ) -> float:
        """Calculate overall classification confidence"""
        # Weight different factors
        weights = {"category": 0.4, "education": 0.2, "difficulty": 0.2, "ocr": 0.2}

        weighted_score = (
            category_conf * weights["category"]
            + education_conf * weights["education"]
            + difficulty_conf * weights["difficulty"]
            + ocr_conf * weights["ocr"]
        )

        return min(weighted_score, 1.0)

    def batch_classify_images(self, image_paths: List[str]) -> List[Tuple[str, Dict]]:
        """
        Classify multiple images in batch

        Args:
            image_paths: List of image file paths

        Returns:
            List of (image_path, classification) tuples
        """
        results = []

        for image_path in image_paths:
            try:
                classification = self.classify_image(image_path)
                results.append((image_path, classification))
                logger.info(f"Batch classification completed: {Path(image_path).name}")
            except Exception as e:
                logger.error(f"Batch classification failed for {image_path}: {e}")
                results.append((image_path, {"error": str(e)}))

        return results

    def get_category_stats(self, classifications: List[Dict]) -> Dict[str, int]:
        """
        Get statistics of categories in batch classifications

        Args:
            classifications: List of classification results

        Returns:
            Dictionary with category counts
        """
        stats = {}

        for classification in classifications:
            if "error" not in classification:
                category = classification.get("primary_category", "unknown")
                stats[category] = stats.get(category, 0) + 1

        return stats
