"""Parser for NC Music Standards Unpacking Documents

Unpacking documents are grade-level narrative explanations that provide
detailed guidance on implementing music standards. They typically include:
- Grade-level focus (K-8, Beginning, Intermediate, Advanced, Accomplished)
- Narrative descriptions of standards
- Teaching strategies and examples
- Assessment guidance
- Less structured format than formal standards
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from .pdf_parser import PDFReader, TextBlock, ParsedPage

logger = logging.getLogger(__name__)


@dataclass
class UnpackingSection:
    """Represents a section of unpacking content"""

    grade_level: str
    strand_code: Optional[str]
    standard_id: Optional[str]
    section_title: str
    content: str
    page_number: int
    teaching_strategies: List[str]
    assessment_guidance: List[str]


class UnpackingNarrativeParser:
    """Parser for grade-level unpacking documents with narrative content"""

    def __init__(self):
        self.pdf_reader = PDFReader()
        self.sections: List[UnpackingSection] = []

        # Patterns for extracting structured information from narrative
        self.standard_reference_pattern = r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+"
        self.grade_pattern = r"(Kindergarten|First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Beginning|Intermediate|Advanced|Accomplished)"

        # Keywords that indicate different section types
        self.teaching_keywords = [
            "teaching",
            "instruction",
            "strategies",
            "activities",
            "examples",
            "practice",
        ]
        self.assessment_keywords = [
            "assessment",
            "evaluate",
            "measure",
            "demonstrate",
            "evidence",
        ]

    def parse_unpacking_document(self, pdf_path: str) -> List[UnpackingSection]:
        """
        Parse an unpacking document to extract narrative content

        Args:
            pdf_path: Path to the PDF document

        Returns:
            List of unpacking sections
        """
        logger.info(f"Parsing unpacking document: {pdf_path}")

        # Read PDF
        pages = self.pdf_reader.read_pdf(pdf_path)

        # Extract grade level from document
        grade_level = self._extract_grade_level(pages)
        logger.info(f"Detected grade level: {grade_level}")

        # Process pages to extract sections
        self.sections = self._extract_sections(pages, grade_level)

        logger.info(f"Extracted {len(self.sections)} unpacking sections")
        return self.sections

    def _extract_grade_level(self, pages: List[ParsedPage]) -> str:
        """Extract grade level from document content"""

        # Check first few pages for grade level indicators
        for page in pages[:3]:
            text = page.raw_text.lower()

            if "kindergarten" in text:
                return "K"
            elif "first grade" in text:
                return "1"
            elif "second grade" in text:
                return "2"
            elif "third grade" in text:
                return "3"
            elif "fourth grade" in text:
                return "4"
            elif "fifth grade" in text:
                return "5"
            elif "sixth grade" in text:
                return "6"
            elif "seventh grade" in text:
                return "7"
            elif "eighth grade" in text:
                return "8"
            elif "beginning" in text:
                return "BE"
            elif "intermediate" in text:
                return "IN"
            elif "advanced" in text:
                return "AD"
            elif "accomplished" in text:
                return "AC"

        return "Unknown"

    def _extract_sections(
        self, pages: List[ParsedPage], grade_level: str
    ) -> List[UnpackingSection]:
        """Extract narrative sections from pages"""

        sections = []
        current_section = None
        current_content = []

        for page in pages:
            for block in page.text_blocks:
                text = block.text.strip()

                # Skip empty blocks
                if not text:
                    continue

                # Check if this is a section header (larger font or specific keywords)
                if self._is_section_header(block):
                    # Save previous section if exists
                    if current_section and current_content:
                        current_section.content = " ".join(current_content)
                        sections.append(current_section)

                    # Start new section
                    current_section = UnpackingSection(
                        grade_level=grade_level,
                        strand_code=self._extract_strand_code(text),
                        standard_id=self._extract_standard_id(text),
                        section_title=text,
                        content="",
                        page_number=page.page_number,
                        teaching_strategies=[],
                        assessment_guidance=[],
                    )
                    current_content = []

                # Add content to current section
                elif current_section:
                    current_content.append(text)

                    # Extract teaching strategies
                    if self._contains_teaching_content(text):
                        current_section.teaching_strategies.append(text)

                    # Extract assessment guidance
                    if self._contains_assessment_content(text):
                        current_section.assessment_guidance.append(text)

        # Save final section
        if current_section and current_content:
            current_section.content = " ".join(current_content)
            sections.append(current_section)

        return sections

    def _is_section_header(self, block: TextBlock) -> bool:
        """Determine if a text block is a section header"""

        # Headers typically have larger font size
        if block.font_size and block.font_size > 12:
            return True

        # Check for header keywords
        text_lower = block.text.lower()
        header_keywords = [
            "connect",
            "create",
            "present",
            "respond",
            "strand",
            "standard",
        ]

        return any(keyword in text_lower for keyword in header_keywords)

    def _extract_strand_code(self, text: str) -> Optional[str]:
        """Extract strand code from text"""

        text_upper = text.upper()
        if "CONNECT" in text_upper or "CN" in text_upper:
            return "CN"
        elif "CREATE" in text_upper or "CR" in text_upper:
            return "CR"
        elif "PRESENT" in text_upper or "PR" in text_upper:
            return "PR"
        elif "RESPOND" in text_upper or "RE" in text_upper:
            return "RE"

        return None

    def _extract_standard_id(self, text: str) -> Optional[str]:
        """Extract standard ID from text"""

        match = re.search(self.standard_reference_pattern, text)
        return match.group(0) if match else None

    def _contains_teaching_content(self, text: str) -> bool:
        """Check if text contains teaching-related content"""

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.teaching_keywords)

    def _contains_assessment_content(self, text: str) -> bool:
        """Check if text contains assessment-related content"""

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.assessment_keywords)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about parsed content"""

        if not self.sections:
            return {}

        strand_dist = {}
        for section in self.sections:
            if section.strand_code:
                strand_dist[section.strand_code] = (
                    strand_dist.get(section.strand_code, 0) + 1
                )

        return {
            "total_sections": len(self.sections),
            "sections_with_teaching_strategies": sum(
                1 for s in self.sections if s.teaching_strategies
            ),
            "sections_with_assessment_guidance": sum(
                1 for s in self.sections if s.assessment_guidance
            ),
            "strand_distribution": strand_dist,
            "average_content_length": sum(len(s.content) for s in self.sections)
            / len(self.sections)
            if self.sections
            else 0,
        }
