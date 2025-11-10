"""Parser for NC Music Reference and Resource Documents

Reference documents include:
- Glossaries (term definitions)
- FAQs (question and answer format)
- PD Catalogs (professional development listings)
- Skills Appendices
- Implementation guides
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from .pdf_parser import PDFReader, TextBlock, ParsedPage

logger = logging.getLogger(__name__)


@dataclass
class GlossaryEntry:
    """Represents a glossary term and definition"""

    term: str
    definition: str
    page_number: int
    related_standards: List[str]


@dataclass
class FAQEntry:
    """Represents a FAQ question and answer"""

    question: str
    answer: str
    page_number: int
    category: Optional[str]


@dataclass
class ResourceEntry:
    """Represents a general resource entry"""

    title: str
    description: str
    content_type: str  # 'glossary', 'faq', 'catalog', 'appendix'
    page_number: int
    metadata: Dict[str, Any]


class ReferenceResourceParser:
    """Parser for reference and resource documents"""

    def __init__(self):
        self.pdf_reader = PDFReader()
        self.entries: List[ResourceEntry] = []
        self.glossary_entries: List[GlossaryEntry] = []
        self.faq_entries: List[FAQEntry] = []

        # Patterns for different content types
        self.question_patterns = [
            r"^Q\d*[:.]\s*",
            r"^\d+\.\s+",
            r"^What\s+",
            r"^How\s+",
            r"^Why\s+",
            r"^When\s+",
            r"^Where\s+",
        ]
        self.answer_patterns = [r"^A\d*[:.]\s*", r"^Answer[:.]\s*"]

    def parse_reference_document(
        self, pdf_path: str, doc_type: str = "auto"
    ) -> List[ResourceEntry]:
        """
        Parse a reference/resource document

        Args:
            pdf_path: Path to the PDF document
            doc_type: Type of document ('glossary', 'faq', 'catalog', 'auto')

        Returns:
            List of resource entries
        """
        logger.info(f"Parsing reference document: {pdf_path}")

        # Read PDF
        pages = self.pdf_reader.read_pdf(pdf_path)

        # Auto-detect document type if needed
        if doc_type == "auto":
            doc_type = self._detect_document_type(pages)
            logger.info(f"Auto-detected document type: {doc_type}")

        # Parse based on document type
        if doc_type == "glossary":
            self.glossary_entries = self._parse_glossary(pages)
            self.entries = [
                ResourceEntry(
                    title=entry.term,
                    description=entry.definition,
                    content_type="glossary",
                    page_number=entry.page_number,
                    metadata={"related_standards": entry.related_standards},
                )
                for entry in self.glossary_entries
            ]
        elif doc_type == "faq":
            self.faq_entries = self._parse_faq(pages)
            self.entries = [
                ResourceEntry(
                    title=entry.question,
                    description=entry.answer,
                    content_type="faq",
                    page_number=entry.page_number,
                    metadata={"category": entry.category},
                )
                for entry in self.faq_entries
            ]
        else:
            # Generic catalog/resource parsing
            self.entries = self._parse_generic_resources(pages, doc_type)

        logger.info(f"Extracted {len(self.entries)} resource entries")
        return self.entries

    def _detect_document_type(self, pages: List[ParsedPage]) -> str:
        """Detect the type of reference document"""

        # Check first few pages for indicators
        first_page_text = " ".join(page.raw_text.lower() for page in pages[:3])

        if "glossary" in first_page_text or "definitions" in first_page_text:
            return "glossary"
        elif "faq" in first_page_text or "frequently asked" in first_page_text:
            return "faq"
        elif (
            "catalog" in first_page_text
            or "professional development" in first_page_text
        ):
            return "catalog"
        elif "appendix" in first_page_text:
            return "appendix"

        return "resource"

    def _parse_glossary(self, pages: List[ParsedPage]) -> List[GlossaryEntry]:
        """Parse glossary document"""

        entries = []
        current_term = None
        current_definition = []

        for page in pages:
            for block in page.text_blocks:
                text = block.text.strip()

                if not text:
                    continue

                # Check if this is a new term (typically bold or larger font)
                if self._is_glossary_term(block, text):
                    # Save previous entry
                    if current_term and current_definition:
                        entries.append(
                            GlossaryEntry(
                                term=current_term,
                                definition=" ".join(current_definition),
                                page_number=page.page_number,
                                related_standards=self._extract_standard_refs(
                                    " ".join(current_definition)
                                ),
                            )
                        )

                    # Start new entry
                    current_term = text.rstrip(":.-")
                    current_definition = []

                # Add to definition
                elif current_term:
                    current_definition.append(text)

        # Save final entry
        if current_term and current_definition:
            entries.append(
                GlossaryEntry(
                    term=current_term,
                    definition=" ".join(current_definition),
                    page_number=pages[-1].page_number if pages else 0,
                    related_standards=self._extract_standard_refs(
                        " ".join(current_definition)
                    ),
                )
            )

        return entries

    def _parse_faq(self, pages: List[ParsedPage]) -> List[FAQEntry]:
        """Parse FAQ document"""

        entries = []
        current_question = None
        current_answer = []
        current_category = None

        for page in pages:
            for block in page.text_blocks:
                text = block.text.strip()

                if not text:
                    continue

                # Check for category header
                if self._is_category_header(block):
                    current_category = text
                    continue

                # Check if this is a question
                if self._is_question(text):
                    # Save previous Q&A
                    if current_question and current_answer:
                        entries.append(
                            FAQEntry(
                                question=current_question,
                                answer=" ".join(current_answer),
                                page_number=page.page_number,
                                category=current_category,
                            )
                        )

                    # Start new Q&A
                    current_question = self._clean_question(text)
                    current_answer = []

                # Check if this is an answer
                elif self._is_answer(text):
                    current_answer.append(self._clean_answer(text))

                # Add to current answer
                elif current_question:
                    current_answer.append(text)

        # Save final Q&A
        if current_question and current_answer:
            entries.append(
                FAQEntry(
                    question=current_question,
                    answer=" ".join(current_answer),
                    page_number=pages[-1].page_number if pages else 0,
                    category=current_category,
                )
            )

        return entries

    def _parse_generic_resources(
        self, pages: List[ParsedPage], doc_type: str
    ) -> List[ResourceEntry]:
        """Parse generic resource document"""

        entries = []

        for page in pages:
            # Group text blocks into sections
            current_title = None
            current_content = []

            for block in page.text_blocks:
                text = block.text.strip()

                if not text:
                    continue

                # Headers are typically larger font or bold
                if self._is_section_header(block):
                    # Save previous section
                    if current_title and current_content:
                        entries.append(
                            ResourceEntry(
                                title=current_title,
                                description=" ".join(current_content),
                                content_type=doc_type,
                                page_number=page.page_number,
                                metadata={},
                            )
                        )

                    # Start new section
                    current_title = text
                    current_content = []
                else:
                    current_content.append(text)

            # Save final section of page
            if current_title and current_content:
                entries.append(
                    ResourceEntry(
                        title=current_title,
                        description=" ".join(current_content),
                        content_type=doc_type,
                        page_number=page.page_number,
                        metadata={},
                    )
                )

        return entries

    def _is_glossary_term(self, block: TextBlock, text: str) -> bool:
        """Check if text block is a glossary term"""

        # Terms typically have larger font or bold
        if block.font_size and block.font_size > 11:
            return True

        # Terms often followed by colon or dash
        if text.endswith(":") or text.endswith(" -"):
            return True

        # All caps might indicate a term
        if text.isupper() and len(text.split()) <= 4:
            return True

        return False

    def _is_category_header(self, block: TextBlock) -> bool:
        """Check if block is a category header"""

        return bool(block.font_size and block.font_size > 12)

    def _is_question(self, text: str) -> bool:
        """Check if text is a question"""

        return any(
            re.match(pattern, text, re.IGNORECASE) for pattern in self.question_patterns
        )

    def _is_answer(self, text: str) -> bool:
        """Check if text is an answer"""

        return any(
            re.match(pattern, text, re.IGNORECASE) for pattern in self.answer_patterns
        )

    def _is_section_header(self, block: TextBlock) -> bool:
        """Check if block is a section header"""

        return bool(block.font_size and block.font_size > 11)

    def _clean_question(self, text: str) -> str:
        """Remove question markers from text"""

        for pattern in self.question_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        return text.strip()

    def _clean_answer(self, text: str) -> str:
        """Remove answer markers from text"""

        for pattern in self.answer_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        return text.strip()

    def _extract_standard_refs(self, text: str) -> List[str]:
        """Extract standard references from text"""

        pattern = r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+(?:\.\d+)?"
        matches = re.findall(pattern, text)
        return [
            ".".join(match) if isinstance(match, tuple) else match for match in matches
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about parsed content"""

        if not self.entries:
            return {}

        content_type_dist = {}
        for entry in self.entries:
            content_type_dist[entry.content_type] = (
                content_type_dist.get(entry.content_type, 0) + 1
            )

        return {
            "total_entries": len(self.entries),
            "glossary_entries": len(self.glossary_entries),
            "faq_entries": len(self.faq_entries),
            "content_type_distribution": content_type_dist,
            "average_description_length": sum(len(e.description) for e in self.entries)
            / len(self.entries)
            if self.entries
            else 0,
        }
