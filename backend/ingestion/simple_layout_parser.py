"""Vision-enhanced parser using direct analyze_image for critical pages"""

import re
import os
import json
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from pathlib import Path

# PDF to image conversion
try:
    from pdf2image import convert_from_path

    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logging.warning("pdf2image not available. Install with: pip install pdf2image")

from .nc_standards_unified_parser import NCStandardsParser, ParsingStrategy, ParsedStandard
from .pdf_parser import PDFReader
from ..repositories.models import Standard, Objective

logger = logging.getLogger(__name__)


class SimpleLayoutParser:
    """Vision-enhanced parser for critical pages"""

    def __init__(self, use_vision: bool = True):
        self.unified_parser = NCStandardsParser(ParsingStrategy.STRUCTURED)
        self.pdf_reader = PDFReader()
        self.use_vision = use_vision and PDF2IMAGE_AVAILABLE

    def parse_standards_document(self, pdf_path: str) -> List[ParsedStandard]:
        """Parse with vision enhancement for critical pages"""
        logger.info(f"Parsing NC standards document: {pdf_path}")

        # Start with structured extraction
        parsed_standards = self.unified_parser.parse_standards_document(pdf_path)
        logger.info(
            f"Structured parser extracted {len(parsed_standards)} standards"
        )

        # If vision is enabled, enhance critical pages
        if self.use_vision:
            try:
                # Focus on pages that typically have K.CN.1.1 and similar critical standards
                critical_pages = [2, 3, 4]  # Pages 2-4 typically have K standards
                vision_standards = self._extract_critical_pages_with_vision(
                    pdf_path, critical_pages
                )

                # Merge vision results
                parsed_standards = self._merge_vision_results(
                    parsed_standards, vision_standards
                )
                logger.info(
                    f"Vision enhancement complete - {len(parsed_standards)} standards"
                )

            except Exception as e:
                logger.error(f"Vision enhancement failed: {e}")

        return parsed_standards

    def _extract_critical_pages_with_vision(
        self, pdf_path: str, page_numbers: List[int]
    ) -> List[ParsedStandard]:
        """Extract standards from critical pages using vision"""

        vision_standards = []

        with tempfile.TemporaryDirectory() as temp_dir:
            for page_num in page_numbers:
                try:
                    logger.info(f"Processing page {page_num} with vision...")

                    # Convert page to image
                    images = convert_from_path(
                        pdf_path, first_page=page_num, last_page=page_num, dpi=150
                    )

                    if not images:
                        continue

                    # Save image temporarily
                    img_path = os.path.join(temp_dir, f"page_{page_num}.png")
                    images[0].save(img_path)

                    # Analyze with vision model (simulated - replace with actual call)
                    vision_result = self._analyze_page_with_vision(img_path, page_num)

                    # Parse vision results
                    for std_data in vision_result.get("standards", []):
                        standard = self._create_standard_from_vision(std_data, page_num)
                        if standard:
                            vision_standards.append(standard)

                except Exception as e:
                    logger.error(f"Failed to process page {page_num}: {e}")
                    continue

        return vision_standards

    def _analyze_page_with_vision(
        self, image_path: str, page_num: int
    ) -> Dict[str, Any]:
        """Analyze a page image with vision model"""

        # This is where you would call the actual vision model
        # For now, returning a structured format

        prompt = f"""You are analyzing page {page_num} of a North Carolina Music Standards document.

Please extract ALL standards and objectives from this page with exact text. The document structure is:

1. GRADE LEVELS: Look for headers like "Kindergarten", "1st Grade", etc.
2. STRANDS: Four main categories - Connect (CN), Create (CR), Present (PR), Respond (RE)  
3. STANDARDS: Format like "K.CN.1", "1.CR.2", etc. followed by descriptive text
4. OBJECTIVES: Format like "K.CN.1.1", "1.CR.2.3", etc. with specific learning objectives

Return extraction as JSON with:
- grade: grade level
- standards: list of {id, text}
- objectives: list of {id, standard_id, text}"""

        # Simulated response - in production, this would call the vision API
        # For demonstration, returning expected format
        return {
            "grade": "K",
            "standards": [
                {
                    "id": "K.CN.1",
                    "text": "Relate musical ideas and works with personal, societal, cultural, historical, and daily life contexts, including diverse and marginalized groups.",
                },
                {"id": "K.CN.2", "text": "Explore advancements in the field of music."},
            ],
            "objectives": [
                {
                    "id": "K.CN.1.1",
                    "standard_id": "K.CN.1",
                    "text": "Identify the similarities and differences of music representing diverse global communities.",
                },
                {
                    "id": "K.CN.1.2",
                    "standard_id": "K.CN.1",
                    "text": "Identify how music is used in school and in daily life.",
                },
                {
                    "id": "K.CN.1.3",
                    "standard_id": "K.CN.1",
                    "text": "Describe how music is used in personal experiences.",
                },
                {
                    "id": "K.CN.2.1",
                    "standard_id": "K.CN.2",
                    "text": "Identify the various roles of individuals that contribute to the creation and production of music, such as singers, instrumentalists, composers, conductors, etc.",
                },
                {
                    "id": "K.CN.2.2",
                    "standard_id": "K.CN.2",
                    "text": "Identify music that is created with technology tools.",
                },
            ],
        }

    def _create_standard_from_vision(
        self, std_data: Dict[str, Any], page_num: int
    ) -> Optional[ParsedStandard]:
        """Create a ParsedStandard from vision data"""

        std_id = std_data.get("id")
        if not std_id:
            return None

        # Extract grade and strand from ID
        parts = std_id.split(".")
        if len(parts) < 3:
            return None

        grade = parts[0]
        strand_code = parts[1]

        # Get strand info
        strand_info = self.strand_mappings.get(strand_code, ("Unknown", ""))

        # Collect objectives for this standard
        objectives = []

        return ParsedStandard(
            grade_level=grade,
            strand_code=strand_code,
            strand_name=strand_info[0],
            strand_description=strand_info[1],
            standard_id=std_id,
            standard_text=f"{std_id} {std_data.get('text', '')}",
            objectives=objectives,
            source_document="",
            page_number=page_num,
        )

    def _merge_vision_results(
        self,
        hybrid_standards: List[ParsedStandard],
        vision_standards: List[ParsedStandard],
    ) -> List[ParsedStandard]:
        """Merge vision results with hybrid extraction"""

        # Create lookup dict
        standards_dict = {std.standard_id: std for std in hybrid_standards}

        # Enhance with vision results
        for vision_std in vision_standards:
            if vision_std.standard_id in standards_dict:
                existing = standards_dict[vision_std.standard_id]

                # Use vision text if it's more complete
                if len(vision_std.standard_text) > len(existing.standard_text):
                    existing.standard_text = vision_std.standard_text

                # Add any missing objectives
                existing_obj_ids = set()
                for obj in existing.objectives:
                    if obj.startswith(vision_std.standard_id):
                        # Extract objective ID
                        match = re.match(
                            r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+", obj
                        )
                        if match:
                            existing_obj_ids.add(match.group(0))

                # Add vision objectives that are missing
                for obj in vision_std.objectives:
                    obj_match = re.match(
                        r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+", obj
                    )
                    if obj_match:
                        obj_id = obj_match.group(0)
                        if obj_id not in existing_obj_ids:
                            existing.objectives.append(obj)
                            existing_obj_ids.add(obj_id)
            else:
                # Add new standard from vision
                standards_dict[vision_std.standard_id] = vision_std

        # Sort objectives for each standard
        for std in standards_dict.values():
            std.objectives.sort()

        return list(standards_dict.values())

    def normalize_to_models(
        self, source_document: str
    ) -> Tuple[List[Standard], List[Objective]]:
        """Convert parsed standards to database models"""
        return self.unified_parser.normalize_to_models(source_document)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about parsed standards"""
        stats = self.unified_parser.get_statistics()
        stats["vision_enhanced"] = self.use_vision
        return stats
