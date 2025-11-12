"""Unified NC Music Standards parser with configurable strategies"""

import re
import os
import json
import base64
import io
import tempfile
from typing import List, Dict, Any, Optional, Tuple, Set, Protocol
from dataclasses import dataclass
import logging
from pathlib import Path
import time
from abc import ABC, abstractmethod
from enum import Enum

# PDF processing
try:
    from pdf2image import convert_from_path

    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logging.warning("pdf2image not available. Install with: pip install pdf2image")

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available. Install with: pip install Pillow")

try:
    import pdfplumber

    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logging.warning("pdfplumber not available. Install with: pip install pdfplumber")

# Internal imports
from .pdf_parser import PDFReader, TextBlock, ParsedPage
from ..repositories.models import Standard, Objective
from ..llm.chutes_client import ChutesClient, Message, ChutesAPIError
from .vision_extraction_helper import (
    extract_standards_from_pdf_multipage,
    get_extraction_statistics,
)

# Import config for formal parser
try:
    from ..config import config
except ImportError:
    config = None
    logging.warning("Config not available, using defaults")

logger = logging.getLogger(__name__)


@dataclass
class ParsedStandard:
    """Represents a parsed standard before normalization"""

    grade_level: str
    strand_code: str
    strand_name: str
    strand_description: str
    standard_id: str
    standard_text: str
    objectives: List[str]
    source_document: str
    page_number: int


class ParsingStrategy(Enum):
    """Available parsing strategies"""

    VISION_FIRST = "vision_first"  # Vision-first with hybrid fallback
    TABLE_BASED = "table_based"  # Table extraction using pdfplumber
    STRUCTURED = "structured"  # Comprehensive text block analysis
    PRECISE = "precise"  # Precise block-by-block analysis
    POSITIONAL = "positional"  # Positional heuristics-based extraction
    AUTO = "auto"  # Automatic strategy selection


class ExtractionStrategy(ABC):
    """Abstract base class for extraction strategies"""

    @abstractmethod
    def extract_standards(self, pdf_path: str, **kwargs) -> List[ParsedStandard]:
        """Extract standards from PDF using this strategy"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this strategy is available (dependencies installed)"""
        pass


class VisionFirstStrategy(ExtractionStrategy):
    """Vision-first strategy using Chutes Qwen VL model with hybrid fallback"""

    def __init__(self, base_parser):
        self.base_parser = base_parser
        self.vision_available = False

        # Check dependencies
        if PDF2IMAGE_AVAILABLE and PIL_AVAILABLE:
            try:
                self.llm_client = ChutesClient()
                self.vision_model = self.llm_client.default_model
                self.vision_available = True
                logger.info(f"Vision processing initialized with {self.vision_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Chutes client: {e}")

    def is_available(self) -> bool:
        return self.vision_available

    def extract_standards(self, pdf_path: str, **kwargs) -> List[ParsedStandard]:
        """Extract standards using vision-first approach with fallback"""
        if not self.is_available():
            logger.warning("Vision processing not available, using fallback")
            return self._fallback_extraction(pdf_path)

        try:
            start_time = time.time()
            standards = self._extract_with_vision(pdf_path)
            elapsed_time = time.time() - start_time

            logger.info(f"Vision extraction successful in {elapsed_time:.2f}s")
            logger.info(f"Extracted {len(standards)} standards")

            # Validate results
            if self.base_parser._validate_extraction(standards):
                return standards
            else:
                logger.warning("Vision extraction validation failed, falling back")
                return self._fallback_extraction(pdf_path)

        except Exception as e:
            logger.error(f"Vision extraction failed: {e}, falling back")
            return self._fallback_extraction(pdf_path)

    def _extract_with_vision(self, pdf_path: str) -> List[ParsedStandard]:
        """Extract standards using improved vision model helper"""
        logger.info(
            "Using enhanced vision extraction with 300 DPI and multi-page processing"
        )

        # Use the new vision extraction helper with improved features:
        # - 300 DPI for better quality
        # - Multi-page processing to handle page boundaries
        # - Intelligent merging of overlapping content
        # - JSON-structured output with fallback
        extracted_standards = extract_standards_from_pdf_multipage(
            pdf_path=pdf_path,
            llm_client=self.llm_client,
            page_range=None,  # Process all pages
            grade_filter=None,  # Extract all grades
            dpi=300,  # High quality extraction
        )

        # Log statistics
        stats = get_extraction_statistics(extracted_standards)
        logger.info(
            f"Vision extraction complete: {stats['total_standards']} standards, "
            f"{stats['total_objectives']} objectives"
        )
        logger.info(f"Distribution by grade: {stats['by_grade']}")
        logger.info(f"Distribution by strand: {stats['by_strand']}")

        # Convert from vision helper format to ParsedStandard format
        parsed_standards = []
        for std_data in extracted_standards:
            # Extract grade and strand from ID
            std_id = std_data["id"]
            parts = std_id.split(".")
            if len(parts) < 3:
                logger.warning(f"Invalid standard ID format: {std_id}")
                continue

            grade_level = parts[0]
            strand_code = parts[1]

            # Get strand info
            strand_info = self.base_parser.strand_mappings.get(
                strand_code, ("Unknown", "Unknown strand")
            )

            # Convert objectives from dict format to string format
            objectives_text = []
            for obj in std_data.get("objectives", []):
                obj_id = obj.get("id", "")
                obj_text = obj.get("text", "")
                if obj_id and obj_text:
                    objectives_text.append(f"{obj_id} {obj_text}")

            parsed_std = ParsedStandard(
                grade_level=grade_level,
                strand_code=strand_code,
                strand_name=strand_info[0],
                strand_description=strand_info[1],
                standard_id=std_id,
                standard_text=std_data.get("text", ""),
                objectives=objectives_text,
                source_document=os.path.basename(pdf_path),
                page_number=std_data.get("page", 0),
            )
            parsed_standards.append(parsed_std)

        # Sort standards by ID
        sorted_standards = sorted(
            parsed_standards,
            key=lambda s: (
                self.base_parser._grade_sort_key(s.grade_level),
                s.strand_code,
                self.base_parser._standard_number(s.standard_id),
            ),
        )

        return sorted_standards

    def _process_page_with_vision(
        self, image: Image.Image, page_num: int
    ) -> List[ParsedStandard]:
        """Process a single page with vision model"""
        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG", optimize=True, quality=85)
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Create extraction prompt
        prompt = self._create_vision_prompt(page_num)

        # Prepare message with image
        messages = [
            Message(
                role="user",
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_base64}"},
                    },
                ],
            )
        ]

        # Call Chutes API with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.llm_client.chat_completion(
                    messages=messages,
                    model=self.vision_model,
                    temperature=config.llm.vision_temperature if config else 0.1,
                    max_tokens=config.llm.vision_max_tokens if config else 4000,
                    timeout=config.processing.request_timeout if config else 60,
                )

                return self._parse_vision_response(response.content, page_num)

            except ChutesAPIError as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        f"Chutes API error on attempt {attempt + 1}, retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    raise

        return []

    def _create_vision_prompt(self, page_num: int) -> str:
        """Create optimized prompt for vision extraction"""
        return f"""Analyze this page from a North Carolina Music Standards document.

Extract ALL standards and objectives with their EXACT text. Follow this structure:

STANDARDS format: ID (like K.CN.1) + descriptive text
OBJECTIVES format: ID (like K.CN.1.1) + specific learning objective

Return a JSON array with this structure:
[
  {{
    "type": "standard",
    "id": "K.CN.1",
    "grade": "K",
    "strand": "CN",
    "text": "Complete standard text here",
    "page": {page_num}
  }},
  {{
    "type": "objective",
    "id": "K.CN.1.1",
    "standard_id": "K.CN.1",
    "text": "Complete objective text here",
    "page": {page_num}
  }}
]

IMPORTANT:
- Extract COMPLETE text, not fragments
- Include ALL standards and objectives visible
- Preserve exact wording and punctuation
- Handle multi-column layouts correctly
- If text continues from previous page, still include it"""

    def _parse_vision_response(
        self, response: str, page_num: int
    ) -> List[ParsedStandard]:
        """Parse JSON response from vision model into standards"""
        try:
            # Extract JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "[" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                json_str = response[start:end]
            else:
                json_str = response

            items = json.loads(json_str)

            # Group by standard
            standards_dict = {}
            objectives_dict = {}

            for item in items:
                if item.get("type") == "standard":
                    std_id = item.get("id")
                    if std_id:
                        standards_dict[std_id] = item
                elif item.get("type") == "objective":
                    std_id = item.get("standard_id")
                    if std_id:
                        if std_id not in objectives_dict:
                            objectives_dict[std_id] = []
                        objectives_dict[std_id].append(item)

            # Build ParsedStandard objects
            parsed_standards = []

            for std_id, std_data in standards_dict.items():
                grade = std_data.get("grade", std_id.split(".")[0])
                strand_code = std_data.get(
                    "strand", std_id.split(".")[1] if "." in std_id else "CN"
                )

                # Get objectives for this standard
                objectives = []
                if std_id in objectives_dict:
                    for obj in objectives_dict[std_id]:
                        obj_text = f"{obj['id']} {obj['text']}"
                        objectives.append(obj_text)

                # Sort objectives by ID
                objectives.sort()

                parsed_standard = ParsedStandard(
                    grade_level=grade,
                    strand_code=strand_code,
                    strand_name=self.base_parser.strand_mappings.get(
                        strand_code, ("Unknown", "")
                    )[0],
                    strand_description=self.base_parser.strand_mappings.get(
                        strand_code, ("", "Unknown")
                    )[1],
                    standard_id=std_id,
                    standard_text=f"{std_id} {std_data.get('text', '')}",
                    objectives=objectives,
                    source_document="",
                    page_number=page_num,
                )

                parsed_standards.append(parsed_standard)

            return parsed_standards

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse vision response on page {page_num}: {e}")
            return []

    def _fallback_extraction(self, pdf_path: str) -> List[ParsedStandard]:
        """Fallback to table-based extraction"""
        if not PDFPLUMBER_AVAILABLE:
            logger.error("No fallback available - pdfplumber not installed")
            return []

        logger.info("Using table-based parser as fallback")
        table_strategy = TableBasedStrategy(self.base_parser)
        return table_strategy.extract_standards(pdf_path)


class TableBasedStrategy(ExtractionStrategy):
    """Table-based extraction strategy using pdfplumber"""

    def __init__(self, base_parser):
        self.base_parser = base_parser

    def is_available(self) -> bool:
        return PDFPLUMBER_AVAILABLE

    def extract_standards(self, pdf_path: str, **kwargs) -> List[ParsedStandard]:
        """Extract standards using table extraction"""
        if not self.is_available():
            raise RuntimeError("pdfplumber not available")

        max_page = kwargs.get("max_page")
        logger.info(f"Parsing NC standards document using table extraction: {pdf_path}")
        if max_page:
            logger.info(f"Parsing up to page {max_page}")

        pdf_path_obj = Path(pdf_path)
        if not pdf_path_obj.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        standards = []
        current_grade = None
        current_strand_code = None
        current_strand_name = None

        with pdfplumber.open(pdf_path_obj) as pdf:
            pages_to_process = pdf.pages[:max_page] if max_page else pdf.pages

            for page_num, page in enumerate(pages_to_process, 1):
                logger.debug(f"Processing page {page_num}")

                # Extract text to detect grade level and strand headers
                page_text = page.extract_text()

                # Detect grade level
                grade = self.base_parser._extract_grade_from_text(page_text)
                if grade:
                    current_grade = grade
                    logger.debug(f"Found grade level: {grade}")

                # Detect strand
                strand_info = self.base_parser._extract_strand_from_text(page_text)
                if strand_info:
                    current_strand_code, current_strand_name = strand_info
                    logger.debug(
                        f"Found strand: {current_strand_code} - {current_strand_name}"
                    )

                # Extract tables
                tables = page.extract_tables()

                for table in tables:
                    if not table:
                        continue

                    # Extract strand from this table's first row if it exists
                    table_strand_info = self.base_parser._extract_strand_from_table(
                        table
                    )
                    if table_strand_info:
                        current_strand_code, current_strand_name = table_strand_info
                        logger.debug(
                            f"Found strand in table: {current_strand_code} - {current_strand_name}"
                        )

                    # Process table rows
                    page_standards = self.base_parser._extract_standards_from_table(
                        table,
                        current_grade,
                        current_strand_code,
                        current_strand_name,
                        page_num,
                    )
                    standards.extend(page_standards)

        # Deduplicate standards (keep the one with more objectives)
        deduplicated = {}
        for std in standards:
            if std.standard_id not in deduplicated:
                deduplicated[std.standard_id] = std
            else:
                # Keep the standard with more objectives
                if len(std.objectives) > len(deduplicated[std.standard_id].objectives):
                    deduplicated[std.standard_id] = std

        standards = list(deduplicated.values())

        logger.info(
            f"Extracted {len(standards)} standards from tables (after deduplication)"
        )
        return standards


class StructuredStrategy(ExtractionStrategy):
    """Comprehensive text block analysis strategy"""

    def __init__(self, base_parser):
        self.base_parser = base_parser
        self.pdf_reader = PDFReader()

    def is_available(self) -> bool:
        return True  # Always available as it uses our own PDFReader

    def extract_standards(self, pdf_path: str, **kwargs) -> List[ParsedStandard]:
        """Extract standards using comprehensive text block analysis"""
        logger.info(f"Parsing NC standards document: {pdf_path}")

        # Read PDF
        pages = self.pdf_reader.read_pdf(pdf_path)

        # Extract all text blocks with their positions
        all_blocks = []
        for page_num, page in enumerate(pages):
            for block in page.text_blocks:
                all_blocks.append(
                    {"page": page_num, "block": block, "text": block.text.strip()}
                )

        # Extract standards using comprehensive approach
        standards = self.base_parser._extract_standards_comprehensive(all_blocks, pages)

        logger.info(f"Extracted {len(standards)} standards")
        return standards


class PreciseStrategy(ExtractionStrategy):
    """Precise block-by-block analysis strategy"""

    def __init__(self, base_parser):
        self.base_parser = base_parser
        self.pdf_reader = PDFReader()

    def is_available(self) -> bool:
        return True  # Always available as it uses our own PDFReader

    def extract_standards(self, pdf_path: str, **kwargs) -> List[ParsedStandard]:
        """Extract standards using precise block-by-block analysis"""
        logger.info(f"Parsing NC standards document: {pdf_path}")

        # Read PDF
        pages = self.pdf_reader.read_pdf(pdf_path)

        # Extract standards using precise heuristics
        standards = self.base_parser._extract_standards_precise(pages)

        logger.info(f"Extracted {len(standards)} standards")
        return standards


class PositionalStrategy(ExtractionStrategy):
    """Positional heuristics-based extraction strategy"""

    def __init__(self, base_parser):
        self.base_parser = base_parser
        self.pdf_reader = PDFReader()

    def is_available(self) -> bool:
        return True  # Always available as it uses our own PDFReader

    def extract_standards(self, pdf_path: str, **kwargs) -> List[ParsedStandard]:
        """Extract standards using positional heuristics"""
        logger.info(f"Parsing NC standards document: {pdf_path}")

        # Read PDF
        pages = self.pdf_reader.read_pdf(pdf_path)

        # Extract standards using heuristics
        standards = self.base_parser._extract_standards_positional(pages)

        logger.info(f"Extracted {len(standards)} standards")
        return standards


class NCStandardsParser:
    """Unified NC Standards parser with configurable strategies"""

    def __init__(self, strategy: ParsingStrategy = ParsingStrategy.AUTO):
        """
        Initialize parser with specified strategy

        Args:
            strategy: Parsing strategy to use (default: AUTO)
        """
        self.parsed_standards: List[ParsedStandard] = []
        self.strategy = strategy

        # Initialize strategies
        self.strategies = {
            ParsingStrategy.VISION_FIRST: VisionFirstStrategy(self),
            ParsingStrategy.TABLE_BASED: TableBasedStrategy(self),
            ParsingStrategy.STRUCTURED: StructuredStrategy(self),
            ParsingStrategy.PRECISE: PreciseStrategy(self),
            ParsingStrategy.POSITIONAL: PositionalStrategy(self),
        }

        # NC Standards strand mappings (common to all parsers)
        self.strand_mappings = {
            "CN": (
                "Connect",
                "Connect music with other arts, other disciplines, and diverse contexts",
            ),
            "CR": ("Create", "Conceive and develop new artistic ideas and work"),
            "PR": (
                "Present",
                "Analyze, interpret, and select artistic work for presentation",
            ),
            "RE": ("Respond", "Interpret and intent and meaning in artistic work"),
        }

        # Patterns for validation (common to all parsers)
        self.standard_id_pattern = r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+"
        self.objective_pattern = r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+"

    def parse_standards_document(self, pdf_path: str, **kwargs) -> List[ParsedStandard]:
        """
        Parse NC standards PDF using the configured strategy

        Args:
            pdf_path: Path to the PDF document
            **kwargs: Additional arguments for specific strategies

        Returns:
            List of parsed standards
        """
        logger.info(f"Parsing NC standards document: {pdf_path}")

        # Determine strategy to use
        strategy_to_use = self._select_strategy()
        logger.info(f"Using strategy: {strategy_to_use.value}")

        # Get the strategy instance
        strategy_instance = self.strategies[strategy_to_use]

        # Check if strategy is available
        if not strategy_instance.is_available():
            logger.warning(
                f"Strategy {strategy_to_use.value} not available, falling back"
            )
            strategy_to_use = self._get_fallback_strategy()
            strategy_instance = self.strategies[strategy_to_use]

        # Extract standards using the selected strategy
        try:
            self.parsed_standards = strategy_instance.extract_standards(
                pdf_path, **kwargs
            )
            logger.info(
                f"Successfully extracted {len(self.parsed_standards)} standards"
            )
            return self.parsed_standards
        except Exception as e:
            logger.error(f"Strategy {strategy_to_use.value} failed: {e}")

            # Try fallback strategies
            for fallback_strategy in self._get_fallback_strategies():
                if fallback_strategy == strategy_to_use:
                    continue

                logger.info(f"Trying fallback strategy: {fallback_strategy.value}")
                fallback_instance = self.strategies[fallback_strategy]

                if fallback_instance.is_available():
                    try:
                        self.parsed_standards = fallback_instance.extract_standards(
                            pdf_path, **kwargs
                        )
                        logger.info(
                            f"Fallback strategy {fallback_strategy.value} succeeded"
                        )
                        return self.parsed_standards
                    except Exception as fallback_error:
                        logger.error(
                            f"Fallback strategy {fallback_strategy.value} failed: {fallback_error}"
                        )
                        continue

            # All strategies failed
            logger.error("All parsing strategies failed")
            self.parsed_standards = []
            return []

    def _select_strategy(self) -> ParsingStrategy:
        """Select the appropriate strategy based on configuration"""
        if self.strategy != ParsingStrategy.AUTO:
            return self.strategy

        # Auto-select strategy based on availability and preferences
        # Prefer vision-first if available, then table-based, then structured
        if self.strategies[ParsingStrategy.VISION_FIRST].is_available():
            return ParsingStrategy.VISION_FIRST
        elif self.strategies[ParsingStrategy.TABLE_BASED].is_available():
            return ParsingStrategy.TABLE_BASED
        else:
            return ParsingStrategy.STRUCTURED  # Always available

    def _get_fallback_strategy(self) -> ParsingStrategy:
        """Get the best available fallback strategy"""
        # Try table-based first, then structured
        if self.strategies[ParsingStrategy.TABLE_BASED].is_available():
            return ParsingStrategy.TABLE_BASED
        else:
            return ParsingStrategy.STRUCTURED

    def _get_fallback_strategies(self) -> List[ParsingStrategy]:
        """Get ordered list of fallback strategies"""
        return [
            ParsingStrategy.TABLE_BASED,
            ParsingStrategy.STRUCTURED,
            ParsingStrategy.PRECISE,
            ParsingStrategy.POSITIONAL,
        ]

    # Common helper methods (consolidated from all parsers)

    def _validate_extraction(self, standards: List[ParsedStandard]) -> bool:
        """Validate extraction results for completeness"""
        if not standards:
            return False

        # Check for minimum expected standards
        if len(standards) < 50:  # NC standards typically have 80+ standards
            logger.warning(f"Only {len(standards)} standards found, expected more")
            return False

        # Check grade distribution
        grades = set(s.grade_level for s in standards)
        expected_grades = {"K", "1", "2", "3", "4", "5", "6", "7", "8"}

        if not expected_grades.issubset(grades):
            missing = expected_grades - grades
            logger.warning(f"Missing grades: {missing}")
            return False

        # Check strand distribution
        strands = set(s.strand_code for s in standards)
        expected_strands = {"CN", "CR", "PR", "RE"}

        if strands != expected_strands:
            logger.warning(f"Unexpected strand distribution: {strands}")
            return False

        # Check for objectives
        total_objectives = sum(len(s.objectives) for s in standards)
        if total_objectives < 100:  # Typically 150+ objectives
            logger.warning(f"Only {total_objectives} objectives found, expected more")
            return False

        # Specific check for K.CN.1.1
        k_cn_1 = next((s for s in standards if s.standard_id == "K.CN.1"), None)
        if k_cn_1:
            has_k_cn_1_1 = any("K.CN.1.1" in obj for obj in k_cn_1.objectives)
            if not has_k_cn_1_1:
                logger.warning("K.CN.1.1 not found in K.CN.1 objectives")
                return False

        return True

    def _extract_objective_ids(self, objectives: List[str]) -> Set[str]:
        """Extract objective IDs from objective text list"""
        ids = set()
        for obj in objectives:
            obj_id = self._extract_objective_id(obj)
            if obj_id:
                ids.add(obj_id)
        return ids

    def _extract_objective_id(self, objective_text: str) -> Optional[str]:
        """Extract objective ID from objective text"""
        match = re.match(self.objective_pattern, objective_text.strip())
        return match.group(0) if match else None

    def _grade_sort_key(self, grade: str) -> tuple:
        """Generate sort key for grade levels"""
        # Handle both "0" (new format) and "K" (legacy format) for backward compatibility
        if grade == "0" or grade == "K":
            return (0, "0")
        elif grade.isdigit():
            return (1, int(grade))
        else:
            # BE, IN, AD, AC
            order = {"BE": 2, "IN": 3, "AD": 4, "AC": 5}
            return (order.get(grade, 99), grade)

    def _standard_number(self, standard_id: str) -> int:
        """Extract standard number for sorting"""
        parts = standard_id.split(".")
        if len(parts) >= 3:
            try:
                return int(parts[2])
            except ValueError:
                return 0
        return 0

    # Table-based strategy helper methods
    def _extract_grade_from_text(self, text: str) -> Optional[str]:
        """Extract grade level from page text"""
        text_upper = text.upper()

        # Check for specific grade patterns
        # Note: Kindergarten is stored as "0" in database for proper sorting before Grade 1
        if "KINDERGARTEN" in text_upper:
            return "0"

        # Check for numbered grades (First Grade, Second Grade, etc.)
        grade_map = {
            "FIRST GRADE": "1",
            "SECOND GRADE": "2",
            "THIRD GRADE": "3",
            "FOURTH GRADE": "4",
            "FIFTH GRADE": "5",
            "SIXTH GRADE": "6",
            "SEVENTH GRADE": "7",
            "EIGHTH GRADE": "8",
        }

        for grade_text, grade_code in grade_map.items():
            if grade_text in text_upper:
                return grade_code

        # Check for proficiency levels
        if "ACCOMPLISHED" in text_upper:
            return "AC"
        if "ADVANCED" in text_upper:
            return "AD"

        return None

    def _extract_strand_from_text(self, text: str) -> Optional[Tuple[str, str]]:
        """Extract strand code and name from page text"""
        text_upper = text.upper()

        strand_keywords = {
            "CONNECT": "CN",
            "CREATE": "CR",
            "PRESENT": "PR",
            "RESPOND": "RE",
        }

        for keyword, code in strand_keywords.items():
            if keyword in text_upper:
                strand_name = self.strand_mappings.get(code, (keyword.title(), ""))[0]
                return (code, strand_name)

        return None

    def _extract_strand_from_table(
        self, table: List[List[str]]
    ) -> Optional[Tuple[str, str]]:
        """Extract strand code and name from table's first row"""
        if not table or len(table) < 1:
            return None

        # Check the first row for strand header
        first_row = table[0]
        if first_row and first_row[0]:
            return self._extract_strand_from_text(first_row[0])

        return None

    def _extract_standards_from_table(
        self,
        table: List[List[str]],
        grade: Optional[str],
        strand_code: Optional[str],
        strand_name: Optional[str],
        page_num: int,
    ) -> List[ParsedStandard]:
        """Extract standards from a table structure (handles 2-column and 4-column formats)"""
        standards = []
        current_standard = None
        current_standard_text_parts = []
        current_objectives = []

        # Detect table format (2-column or 4-column)
        is_four_column = len(table[0]) > 2 if table else False

        standard_col = 1 if is_four_column else 0
        objectives_col = 3 if is_four_column else 1

        for row in table:
            if not row or len(row) <= standard_col:
                continue

            # Get cells based on format
            standard_cell = (
                row[standard_col]
                if len(row) > standard_col and row[standard_col]
                else ""
            )
            objectives_cell = (
                row[objectives_col]
                if len(row) > objectives_col and row[objectives_col]
                else ""
            )

            # Also check column 0 in 4-column format (sometimes standards appear there too)
            if is_four_column and len(row) > 0 and row[0]:
                alt_cell = row[0]
                if self._contains_standard_id(alt_cell):
                    standard_cell = alt_cell

            # Skip header rows
            if "Standard" in standard_cell or "Objectives" in objectives_cell:
                continue

            # Skip strand description rows
            if any(
                strand in standard_cell for strand in ["CN -", "CR -", "PR -", "RE -"]
            ):
                continue

            # Check if cell contains a standard ID
            if standard_cell and self._contains_standard_id(standard_cell):
                # Save previous standard if exists
                if current_standard and current_standard_text_parts:
                    full_text = " ".join(current_standard_text_parts)
                    std = self._build_standard(
                        current_standard,
                        full_text,
                        current_objectives,
                        grade,
                        strand_code,
                        strand_name,
                        page_num,
                    )
                    if std:
                        standards.append(std)

                # Start new standard
                current_standard = self._extract_standard_id(standard_cell)
                if current_standard:
                    text = self._extract_standard_text(standard_cell, current_standard)
                    current_standard_text_parts = [text] if text else []
                else:
                    current_standard_text_parts = []
                current_objectives = []

                # Process objectives from objectives cell
                if objectives_cell and self._contains_objective(objectives_cell):
                    objectives = self._extract_objectives(objectives_cell)
                    current_objectives.extend(objectives)

            elif standard_cell and current_standard:
                # This is continuation of standard text
                if not self._is_header_text(standard_cell):
                    current_standard_text_parts.append(standard_cell.strip())

                # Also check for objectives in this row
                if objectives_cell and self._contains_objective(objectives_cell):
                    objectives = self._extract_objectives(objectives_cell)
                    current_objectives.extend(objectives)

            elif objectives_cell and self._contains_objective(objectives_cell):
                # Additional objectives for current standard
                objectives = self._extract_objectives(objectives_cell)
                current_objectives.extend(objectives)

        # Don't forget the last standard
        if current_standard and current_standard_text_parts:
            full_text = " ".join(current_standard_text_parts)
            std = self._build_standard(
                current_standard,
                full_text,
                current_objectives,
                grade,
                strand_code,
                strand_name,
                page_num,
            )
            if std:
                standards.append(std)

        return standards

    def _is_header_text(self, text: str) -> bool:
        """Check if text is a header or meta text that should be skipped"""
        text_lower = text.lower()
        return any(
            keyword in text_lower
            for keyword in ["standard", "objectives", "cn -", "cr -", "pr -", "re -"]
        )

    def _contains_standard_id(self, text: str) -> bool:
        """Check if text contains a standard ID"""
        return bool(re.search(self.standard_id_pattern, text))

    def _contains_objective(self, text: str) -> bool:
        """Check if text contains an objective"""
        return bool(re.search(self.objective_pattern, text))

    def _extract_standard_id(self, text: str) -> Optional[str]:
        """Extract standard ID from text"""
        match = re.search(self.standard_id_pattern, text)
        if match:
            return match.group(0)
        return None

    def _extract_standard_text(self, text: str, standard_id: str) -> str:
        """Extract standard text (everything after the standard ID)"""
        # Remove the standard ID and get the remaining text
        parts = text.split(standard_id, 1)
        if len(parts) > 1:
            standard_text = parts[1].strip()
            # Clean up whitespace
            standard_text = re.sub(r"\s+", " ", standard_text)
            return standard_text
        return ""

    def _extract_objectives(self, text: str) -> List[str]:
        """Extract all objectives from text"""
        objectives = []

        # Split by objective pattern
        lines = text.split("\n")
        current_objective = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this line starts a new objective
            if re.match(self.objective_pattern, line):
                # Save previous objective if exists
                if current_objective:
                    objectives.append(current_objective.strip())
                # Start new objective
                current_objective = line
            else:
                # Continue current objective
                if current_objective:
                    current_objective += " " + line

        # Don't forget the last objective
        if current_objective:
            objectives.append(current_objective.strip())

        return objectives

    def _build_standard(
        self,
        standard_id: str,
        standard_text: str,
        objectives: List[str],
        grade: Optional[str],
        strand_code: Optional[str],
        strand_name: Optional[str],
        page_num: int,
    ) -> Optional[ParsedStandard]:
        """Build a ParsedStandard object"""

        # Validate we have required fields
        if not grade or not strand_code:
            logger.warning(f"Missing grade or strand for standard {standard_id}")
            return None

        # Get strand info
        if strand_code not in self.strand_mappings:
            logger.warning(f"Unknown strand code: {strand_code}")
            return None

        strand_name_full, strand_description = self.strand_mappings[strand_code]

        # Build complete standard text with ID
        full_standard_text = f"{standard_id} {standard_text}"

        # Ensure proper ending
        if full_standard_text and not full_standard_text.endswith("."):
            full_standard_text += "."

        return ParsedStandard(
            grade_level=grade,
            strand_code=strand_code,
            strand_name=strand_name_full,
            strand_description=strand_description,
            standard_id=standard_id,
            standard_text=full_standard_text,
            objectives=objectives,
            source_document="",
            page_number=page_num,
        )

    # Structured strategy helper methods
    def _extract_standards_comprehensive(
        self, all_blocks: List[Dict], pages: List[ParsedPage]
    ) -> List[ParsedStandard]:
        """Extract standards with comprehensive coverage and exact matching"""
        standards = []
        processed_standard_ids = set()

        # First pass: Find all standard IDs and their associated content
        standard_blocks = {}

        for i, block_info in enumerate(all_blocks):
            text = block_info["text"]

            # Check if this block contains a standard ID
            if self._contains_standard_id(text):
                std_id = self._extract_standard_id(text)
                if std_id and std_id not in processed_standard_ids:
                    # Found a new standard
                    processed_standard_ids.add(std_id)

                    # Gather all related blocks
                    related_blocks = self._gather_standard_blocks(all_blocks, i, std_id)
                    standard_blocks[std_id] = related_blocks

        # Second pass: Process each standard with its related content
        current_grade = None
        current_strand = None

        for std_id in sorted(standard_blocks.keys()):
            blocks = standard_blocks[std_id]

            # Extract grade and strand from the standard ID
            grade = self._extract_grade_from_id(std_id)
            strand_code = self._extract_strand_from_id(std_id)

            if grade:
                current_grade = grade
            if strand_code:
                current_strand = self._get_strand_info(strand_code)

            if current_grade and current_strand:
                # Build the complete standard
                standard = self._build_standard_from_blocks(
                    std_id, blocks, current_grade, current_strand
                )
                if standard:
                    standards.append(standard)

        return standards

    def _gather_standard_blocks(
        self, all_blocks: List[Dict], start_idx: int, std_id: str
    ) -> List[Dict]:
        """Gather all blocks related to a standard"""
        related_blocks = []

        # Look backward for objectives that come before the standard
        for j in range(start_idx - 1, max(0, start_idx - 10), -1):
            block_text = all_blocks[j]["text"]
            if block_text.startswith(std_id + "."):
                related_blocks.insert(0, all_blocks[j])
            elif self._contains_standard_id(block_text) and not block_text.startswith(
                std_id
            ):
                # Hit a different standard, stop
                break

        # Include the standard block itself
        related_blocks.append(all_blocks[start_idx])

        # Look forward for standard text and objectives
        for j in range(start_idx + 1, min(len(all_blocks), start_idx + 20)):
            block_text = all_blocks[j]["text"]

            # Stop if we hit another standard or a strand/grade header
            if self._contains_standard_id(block_text) and not block_text.startswith(
                std_id
            ):
                break
            if self._is_strand_header(block_text) or self._is_grade_header(block_text):
                break

            # Include objectives and standard text
            if block_text.startswith(std_id + ".") or not self._contains_standard_id(
                block_text
            ):
                related_blocks.append(all_blocks[j])

        return related_blocks

    def _build_standard_from_blocks(
        self, std_id: str, blocks: List[Dict], grade: str, strand: Tuple[str, str]
    ) -> Optional[ParsedStandard]:
        """Build a complete standard from its blocks"""
        standard_text_parts = []
        objectives = []
        objectives_seen = set()

        for block_info in blocks:
            text = block_info["text"]

            # Check if this is an objective
            if self._is_objective(text):
                # Ensure it belongs to this standard
                if text.startswith(std_id + "."):
                    # Extract objective ID to avoid duplicates
                    obj_match = re.match(self.objective_pattern, text)
                    if obj_match:
                        obj_id = obj_match.group(0)
                        if obj_id not in objectives_seen:
                            objectives_seen.add(obj_id)
                            objectives.append(text)
            elif std_id in text:
                # This is the standard ID block, extract the text after the ID
                parts = text.split(std_id, 1)
                if len(parts) > 1 and parts[1].strip():
                    standard_text_parts.append(parts[1].strip())
            elif not self._contains_standard_id(text):
                # This is additional standard text
                standard_text_parts.append(text)

        # Combine standard text
        standard_text = " ".join(standard_text_parts)

        # Clean up standard text
        standard_text = re.sub(r"\s+", " ", standard_text).strip()

        # Ensure we have the standard ID at the beginning
        if not standard_text.startswith(std_id):
            standard_text = f"{std_id} {standard_text}"

        # Ensure proper ending
        if standard_text and not standard_text.endswith("."):
            standard_text += "."

        # Create the parsed standard
        return ParsedStandard(
            grade_level=grade,
            strand_code=strand[0],
            strand_name=strand[1],
            strand_description=self.strand_mappings[strand[0]][1],
            standard_id=std_id,
            standard_text=standard_text,
            objectives=objectives,
            source_document="",
            page_number=blocks[0]["page"] if blocks else 0,
        )

    def _is_objective(self, text: str) -> bool:
        """Check if text is exactly an objective"""
        return bool(re.match(self.objective_pattern, text.strip()))

    def _is_strand_header(self, text: str) -> bool:
        """Check if text is a strand header"""
        text_upper = text.strip().upper()
        return text_upper in ["CONNECT", "CREATE", "PRESENT", "RESPOND"]

    def _is_grade_header(self, text: str) -> bool:
        """Check if text is a grade level header"""
        text_upper = text.strip().upper()
        return (
            "KINDERGARTEN" in text_upper
            or "BEGINNING" in text_upper
            or "INTERMEDIATE" in text_upper
            or "ADVANCED" in text_upper
            or "ACCOMPLISHED" in text_upper
            or bool(re.search(r"\d+TH GRADE", text_upper))
        )

    def _extract_grade_from_id(self, std_id: str) -> Optional[str]:
        """Extract grade level from standard ID"""
        parts = std_id.split(".")
        if parts:
            return parts[0]
        return None

    def _extract_strand_from_id(self, std_id: str) -> Optional[str]:
        """Extract strand code from standard ID"""
        parts = std_id.split(".")
        if len(parts) >= 2:
            return parts[1]
        return None

    def _get_strand_info(self, strand_code: str) -> Optional[Tuple[str, str]]:
        """Get full strand information from code"""
        if strand_code == "CN":
            return ("CN", "Connect")
        elif strand_code == "CR":
            return ("CR", "Create")
        elif strand_code == "PR":
            return ("PR", "Present")
        elif strand_code == "RE":
            return ("RE", "Respond")
        return None

    # Precise strategy helper methods
    def _extract_standards_precise(
        self, pages: List[ParsedPage]
    ) -> List[ParsedStandard]:
        """Extract standards with precise block-by-block analysis"""
        standards = []
        current_grade = None
        current_strand = None

        for page_num, page in enumerate(pages):
            # Get text blocks in reading order
            blocks = sorted(page.text_blocks, key=lambda b: (b.y0, b.x0))

            i = 0
            while i < len(blocks):
                block = blocks[i]
                text = block.text.strip()

                # Check for grade level headers
                grade = self._extract_grade_level_precise(text)
                if grade:
                    current_grade = grade
                    i += 1
                    continue

                # Check for strand headers
                strand = self._extract_strand_precise(text)
                if strand:
                    current_strand = strand
                    i += 1
                    continue

                # Check for standard ID (but prioritize objectives)
                standard_id = self._extract_standard_id_precise(text)

                if (
                    standard_id
                    and current_grade
                    and current_strand
                    and not self._is_objective_precise(text)
                ):
                    # Extract the complete standard and its objectives
                    standard, next_i = self._extract_complete_standard(
                        blocks, i, current_grade, current_strand, page_num
                    )
                    if standard:
                        standards.append(standard)
                    i = next_i
                    continue

                i += 1

        return standards

    def _extract_complete_standard(
        self,
        blocks: List[TextBlock],
        start_idx: int,
        grade: str,
        strand: Tuple[str, str],
        page_num: int,
    ) -> Tuple[Optional[ParsedStandard], int]:
        """Extract a complete standard with its text and all objectives"""

        # The standard ID is at start_idx
        standard_id_block = blocks[start_idx]
        standard_id = self._extract_standard_id_precise(standard_id_block.text.strip())

        if not standard_id:
            return None, start_idx + 1

        # Collect all text blocks that belong to this standard
        standard_text_parts = []
        objectives = []

        # First, look backwards to collect objectives that come before the standard
        for j in range(start_idx - 1, -1, -1):
            prev_text = blocks[j].text.strip()
            if self._is_objective_precise(prev_text):
                # Check if this objective belongs to our standard (matches our standard_id prefix)
                if prev_text.startswith(standard_id):
                    objectives.insert(0, prev_text)  # Add to beginning
                else:
                    break  # This objective belongs to a different standard
            else:
                break  # Not an objective, stop looking back

        i = start_idx + 1
        while i < len(blocks):
            block = blocks[i]
            text = block.text.strip()

            # Stop if we hit the next standard, strand, or grade
            if (
                self._extract_standard_id_precise(text)
                or self._extract_strand_precise(text)
                or self._extract_grade_level_precise(text)
            ):
                break

            # Check if this is an objective (starts with objective pattern)
            if self._is_objective_precise(text):
                # Only add objectives that belong to this standard
                if text.startswith(standard_id):
                    objectives.append(text)
                # If it's an objective for a different standard, we should stop
                # as we've moved past this standard's content
                else:
                    break
            elif text:
                # This is part of the standard text
                standard_text_parts.append(text)

            i += 1

        # Also look for objectives that might be mixed into the standard text
        # Sometimes objectives get embedded in the text blocks
        combined_text = " ".join(standard_text_parts)
        embedded_objectives = re.findall(
            r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+\s+[^.]*\.", combined_text
        )

        for embedded_obj in embedded_objectives:
            if isinstance(embedded_obj, str) and embedded_obj.startswith(standard_id):
                # Clean up and add to objectives
                clean_obj = re.sub(r"\s+", " ", embedded_obj.strip())
                if clean_obj not in objectives:
                    objectives.append(clean_obj)
                # Remove from standard text
                combined_text = combined_text.replace(embedded_obj, "")

        # Update standard text with cleaned version
        standard_text = combined_text

        # Combine standard text parts and clean up
        standard_text = " ".join(standard_text_parts)

        # Clean up standard text - remove fragments and ensure proper ending
        standard_text = re.sub(r"\s+", " ", standard_text).strip()
        if standard_text and not standard_text.endswith("."):
            standard_text += "."

        # Create the parsed standard
        parsed_standard = ParsedStandard(
            grade_level=grade,
            strand_code=strand[0],
            strand_name=strand[1],
            strand_description=self.strand_mappings[strand[0]][1],
            standard_id=standard_id,
            standard_text=standard_text,
            objectives=objectives,
            source_document="",  # Will be set by caller
            page_number=page_num,
        )

        return parsed_standard, i

    def _extract_standard_id_precise(self, text: str) -> Optional[str]:
        """Extract standard ID with exact pattern matching"""
        match = re.match(self.standard_id_pattern, text.strip())
        if match:
            # Extract just the ID part (e.g., "K.CN.1" from "K.CN.1 Relate musical...")
            id_part = match.group(0)
            # Split on first space to get just the ID
            return id_part.split()[0] if " " in id_part else id_part
        return None

    def _is_objective_precise(self, text: str) -> bool:
        """Check if text is exactly an objective"""
        return bool(re.match(self.objective_pattern, text.strip()))

    def _extract_grade_level_precise(self, text: str) -> Optional[str]:
        """Extract grade level with precise matching"""
        text_upper = text.strip().upper()

        # Exact matches for specific grade indicators
        # Note: Kindergarten is stored as "0" in database for proper sorting before Grade 1
        if text_upper == "KINDERGARTEN":
            return "0"
        elif text_upper == "K":
            return "0"
        elif text_upper == "BEGINNING":
            return "BE"
        elif text_upper == "INTERMEDIATE":
            return "IN"
        elif text_upper == "ADVANCED":
            return "AD"
        elif text_upper == "ACCOMPLISHED":
            return "AC"

        # Pattern matches for grade levels in context
        # Note: Kindergarten is stored as "0" in database for proper sorting before Grade 1
        if "KINDERGARTEN GENERAL MUSIC" in text_upper:
            return "0"
        elif re.match(r"^(\d+)TH GRADE GENERAL MUSIC$", text_upper):
            match = re.match(r"^(\d+)TH GRADE GENERAL MUSIC$", text_upper)
            return match.group(1) if match else None

        return None

    def _extract_strand_precise(self, text: str) -> Optional[Tuple[str, str]]:
        """Extract strand with precise matching"""
        text_upper = text.strip().upper()

        # Exact strand names
        if text_upper == "CONNECT":
            return ("CN", "Connect")
        elif text_upper == "CREATE":
            return ("CR", "Create")
        elif text_upper == "PRESENT":
            return ("PR", "Present")
        elif text_upper == "RESPOND":
            return ("RE", "Respond")

        return None

    # Positional strategy helper methods
    def _extract_standards_positional(
        self, pages: List[ParsedPage]
    ) -> List[ParsedStandard]:
        """Extract standards from parsed pages using heuristics"""
        standards = []
        current_grade = None
        current_strand = None

        for page in pages:
            page_standards = self._parse_page_positional(
                page, current_grade, current_strand
            )
            standards.extend(page_standards)

            # Update current context from page
            if page_standards:
                last_standard = page_standards[-1]
                current_grade = last_standard.grade_level
                current_strand = (last_standard.strand_code, last_standard.strand_name)

        # Deduplicate standards by standard_id
        seen_ids = set()
        unique_standards = []
        for standard in standards:
            if standard.standard_id not in seen_ids:
                seen_ids.add(standard.standard_id)
                unique_standards.append(standard)

        logger.info(
            f"Extracted {len(standards)} standards, deduplicated to {len(unique_standards)} unique standards"
        )
        return unique_standards

    def _parse_page_positional(
        self,
        page: ParsedPage,
        current_grade: Optional[str],
        current_strand: Optional[Tuple[str, str]],
    ) -> List[ParsedStandard]:
        """Parse a single page for standards"""
        standards = []

        # Get text blocks in reading order
        blocks = sorted(page.text_blocks, key=lambda b: (b.y0, b.x0))

        i = 0
        while i < len(blocks):
            block = blocks[i]
            text = block.text.strip()

            # Check for grade level headers
            grade = self._extract_grade_level(text)
            if grade:
                current_grade = grade
                i += 1
                continue

            # Check for standard IDs FIRST (before strands to avoid conflicts)
            standard_id = self._extract_standard_id(text)
            if standard_id and current_grade and current_strand:
                standard_text, objectives = self._extract_standard_content(blocks, i)

                if standard_text:
                    parsed_standard = ParsedStandard(
                        grade_level=current_grade,
                        strand_code=current_strand[0],
                        strand_name=current_strand[1],
                        strand_description=self.strand_mappings[current_strand[0]][1],
                        standard_id=standard_id,
                        standard_text=standard_text,
                        objectives=objectives,
                        source_document="",  # Will be set by caller
                        page_number=page.page_number,
                    )
                    standards.append(parsed_standard)

                i += 1  # Move to next block
            else:
                # Check for strand headers (only if not a standard ID)
                strand = self._extract_strand(text)
                if strand:
                    current_strand = strand
                    i += 1
                else:
                    i += 1

        return standards

    def _extract_standard_content(
        self, blocks: List[TextBlock], start_idx: int
    ) -> Tuple[str, List[str]]:
        """Extract standard text and objectives from blocks starting at start_idx"""
        if start_idx >= len(blocks):
            return "", []

        # The standard text is usually in block after ID or part of it
        standard_text = ""
        objectives = []

        i = start_idx + 1
        if i < len(blocks):
            # Check if next block contains standard text
            next_block = blocks[i]
            if not self._is_objective(next_block.text):
                standard_text = next_block.text
                i += 1

        # Collect objectives - look for objectives in the next several blocks
        max_blocks_to_check = 10  # Limit how far we look ahead
        blocks_checked = 0

        while i < len(blocks) and blocks_checked < max_blocks_to_check:
            block = blocks[i]
            text = block.text.strip()

            # Check if this block contains an objective (even if embedded in other text)
            extracted_objective = self._extract_objective_from_text(text)
            if extracted_objective:
                objectives.append(extracted_objective)
            elif self._extract_standard_id(text) or self._extract_strand(text):
                # We've reached to next standard or strand
                break
            elif text and not standard_text and not self._is_objective(text):
                # This might be standard text if we didn't capture it earlier
                # and it's not an objective
                standard_text = text

            i += 1
            blocks_checked += 1

        return standard_text, objectives

    def _extract_objective_from_text(self, text: str) -> Optional[str]:
        """Extract objective from text, even if embedded in larger text block"""
        # Pattern to find objectives anywhere in text (capture full match)
        pattern = r"(?:K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+[^.]*(?:\.|$)"
        match = re.search(pattern, text)

        if match:
            objective = match.group(0).strip()
            # Clean up - ensure it ends properly
            if objective and not objective.endswith((".", "!", "?")):
                # If it doesn't end with punctuation, it might be cut off
                # Try to find the next sentence boundary in the original text
                start_idx = text.find(objective)
                if start_idx != -1:
                    remaining_text = text[start_idx + len(objective) :]
                    next_period = remaining_text.find(".")
                    if (
                        next_period != -1 and next_period < 100
                    ):  # Reasonable sentence length
                        objective += remaining_text[: next_period + 1]
            return objective

        return None

    # Common methods for all strategies
    def normalize_to_models(
        self, source_document: str
    ) -> Tuple[List[Standard], List[Objective]]:
        """Convert parsed standards to database models"""
        standards = []
        objectives = []

        for parsed in self.parsed_standards:
            # Create standard
            standard = Standard(
                standard_id=parsed.standard_id,
                grade_level=parsed.grade_level,
                strand_code=parsed.strand_code,
                strand_name=parsed.strand_name,
                strand_description=parsed.strand_description,
                standard_text=parsed.standard_text,
                source_document=source_document,
                ingestion_date="2024-01-01",
                version="2024",
            )
            standards.append(standard)

            # Create objectives
            for obj_text in parsed.objectives:
                # Extract objective ID
                obj_match = re.match(self.objective_pattern, obj_text)
                if obj_match:
                    objective_id = obj_match.group(0)
                else:
                    # Fallback
                    objective_id = f"{parsed.standard_id}.{len(objectives) + 1}"

                objective = Objective(
                    objective_id=objective_id,
                    standard_id=parsed.standard_id,
                    objective_text=obj_text,
                )
                objectives.append(objective)

        return standards, objectives

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about parsed standards"""
        if not self.parsed_standards:
            return {}

        grade_dist = {}
        strand_dist = {}

        for std in self.parsed_standards:
            grade_dist[std.grade_level] = grade_dist.get(std.grade_level, 0) + 1
            strand_dist[std.strand_code] = strand_dist.get(std.strand_code, 0) + 1

        return {
            "total_standards": len(self.parsed_standards),
            "total_objectives": sum(len(s.objectives) for s in self.parsed_standards),
            "average_objectives_per_standard": (
                sum(len(s.objectives) for s in self.parsed_standards)
                / len(self.parsed_standards)
                if self.parsed_standards
                else 0
            ),
            "grade_distribution": grade_dist,
            "strand_distribution": strand_dist,
            "parsing_strategy": self.strategy.value
            if self.strategy != ParsingStrategy.AUTO
            else "auto_selected",
        }
