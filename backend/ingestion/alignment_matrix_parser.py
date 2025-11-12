"""Parser for NC Music Standards Alignment Documents

Alignment documents include:
- Horizontal Alignment (standards across grades within same strand)
- Vertical Alignment (progression of skills across grades)
- Matrix/grid layouts showing relationships between standards
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
import logging

try:
    import pdfplumber

    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logging.warning("pdfplumber not available. Install with: pip install pdfplumber")

from .pdf_parser import PDFReader, ParsedPage

logger = logging.getLogger(__name__)


@dataclass
class AlignmentRelationship:
    """Represents a relationship between standards"""

    standard_id: str
    related_standard_ids: List[str]
    relationship_type: str  # 'horizontal', 'vertical', 'prerequisite', 'builds_on'
    grade_level: str
    strand_code: str
    description: str
    page_number: int


@dataclass
class ProgressionMapping:
    """Represents skill progression across grades"""

    skill_name: str
    grade_levels: List[str]
    standard_mappings: Dict[str, str]  # grade -> standard_id
    progression_notes: str


class AlignmentMatrixParser:
    """Parser for alignment documents with matrix/grid layouts"""

    def __init__(self):
        self.pdf_reader = PDFReader()
        self.relationships: List[AlignmentRelationship] = []
        self.progressions: List[ProgressionMapping] = []

        # Pattern for standard IDs (non-capturing groups to get full match)
        self.standard_pattern = r"(?:K|\d+|BE|IN|AD|AC)\.(?:CN|CR|PR|RE)\.\d+"

        # Grade ordering for progression analysis
        # Note: Kindergarten is stored as "0" in database for proper sorting before Grade 1
        self.grade_order = [
            "0",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "BE",
            "IN",
            "AD",
            "AC",
        ]

    def parse_alignment_document(
        self, pdf_path: str, alignment_type: str = "auto"
    ) -> List[AlignmentRelationship]:
        """
        Parse an alignment document

        Args:
            pdf_path: Path to the PDF document
            alignment_type: Type of alignment ('horizontal', 'vertical', 'auto')

        Returns:
            List of alignment relationships
        """
        logger.info(f"Parsing alignment document: {pdf_path}")

        # Read PDF
        pages = self.pdf_reader.read_pdf(pdf_path)

        # Auto-detect alignment type if needed
        if alignment_type == "auto":
            alignment_type = self._detect_alignment_type(pages)
            logger.info(f"Auto-detected alignment type: {alignment_type}")

        # Try table-based extraction first (most alignment docs use tables)
        if PDFPLUMBER_AVAILABLE:
            try:
                self.relationships = self._extract_from_tables(pdf_path, alignment_type)
                logger.info(
                    f"Table extraction found {len(self.relationships)} relationships"
                )

                # If no relationships found from tables, fall back to text
                if not self.relationships:
                    logger.info("No tables found, using text-based extraction")
                    self.relationships = self._extract_from_text(pages, alignment_type)

            except Exception as e:
                logger.warning(
                    f"Table extraction failed: {e}, falling back to text-based"
                )
                self.relationships = self._extract_from_text(pages, alignment_type)
        else:
            # Fallback to text-based extraction
            self.relationships = self._extract_from_text(pages, alignment_type)

        # Extract progressions if vertical alignment
        if alignment_type == "vertical":
            self.progressions = self._extract_progressions(pages)
            logger.info(f"Extracted {len(self.progressions)} progression mappings")

        logger.info(f"Extracted {len(self.relationships)} alignment relationships")
        return self.relationships

    def _detect_alignment_type(self, pages: List[ParsedPage]) -> str:
        """Detect the type of alignment document"""

        first_page_text = " ".join(page.raw_text.lower() for page in pages[:2])

        if "horizontal" in first_page_text:
            return "horizontal"
        elif "vertical" in first_page_text:
            return "vertical"
        elif "progression" in first_page_text:
            return "vertical"

        return "general"

    def _extract_from_tables(
        self, pdf_path: str, alignment_type: str
    ) -> List[AlignmentRelationship]:
        """Extract alignment relationships from PDF tables"""

        relationships = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                tables = page.extract_tables()

                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    # Process table based on alignment type
                    if alignment_type == "horizontal":
                        relationships.extend(
                            self._process_horizontal_table(table, page_num)
                        )
                    elif alignment_type == "vertical":
                        relationships.extend(
                            self._process_vertical_table(table, page_num)
                        )
                    else:
                        relationships.extend(
                            self._process_general_table(table, page_num)
                        )

        return relationships

    def _process_horizontal_table(
        self, table: List[List[Optional[str]]], page_num: int
    ) -> List[AlignmentRelationship]:
        """Process table showing horizontal alignment (same grade, different strands)"""

        relationships = []
        headers = table[0] if table else []

        # Find columns with standard IDs
        std_columns = []
        for col_idx, header in enumerate(headers):
            if header and re.search(self.standard_pattern, str(header)):
                std_columns.append(col_idx)

        # Process each row
        for row in table[1:]:
            if not row:
                continue

            # Extract standards from this row
            row_standards = []
            for col_idx in std_columns:
                if col_idx < len(row) and row[col_idx]:
                    std_ids = re.findall(self.standard_pattern, str(row[col_idx]))
                    row_standards.extend(std_ids)

            # Create relationships between standards in same row
            for i, std_id in enumerate(row_standards):
                related_ids = row_standards[:i] + row_standards[i + 1 :]
                if related_ids:
                    grade, strand = self._parse_standard_id(std_id)
                    relationships.append(
                        AlignmentRelationship(
                            standard_id=std_id,
                            related_standard_ids=related_ids,
                            relationship_type="horizontal",
                            grade_level=grade or "Unknown",
                            strand_code=strand or "Unknown",
                            description=f"Aligned with {len(related_ids)} standards in grade {grade}",
                            page_number=page_num,
                        )
                    )

        return relationships

    def _process_vertical_table(
        self, table: List[List[Optional[str]]], page_num: int
    ) -> List[AlignmentRelationship]:
        """Process table showing vertical alignment (progression across grades)"""

        relationships = []

        # Typically: first column is skill/concept, other columns are grades
        if not table or len(table) < 2:
            return relationships

        headers = table[0]

        # Process each row (each row represents a skill progression)
        for row in table[1:]:
            if not row or len(row) < 2:
                continue

            skill_name = str(row[0]) if row[0] else ""

            # Extract standards from grade columns
            grade_standards = {}
            for col_idx in range(1, len(row)):
                if col_idx < len(headers) and col_idx < len(row) and headers[col_idx]:
                    grade = self._extract_grade_from_header(headers[col_idx])
                    if grade and row[col_idx]:
                        std_ids = re.findall(self.standard_pattern, str(row[col_idx]))
                        if std_ids:
                            grade_standards[grade] = std_ids

            # Create progression relationships
            sorted_grades = sorted(
                grade_standards.keys(),
                key=lambda g: self.grade_order.index(g)
                if g in self.grade_order
                else 99,
            )

            for i, grade in enumerate(sorted_grades):
                for std_id in grade_standards[grade]:
                    # Link to previous and next grades
                    related_ids = []
                    if i > 0:
                        related_ids.extend(grade_standards[sorted_grades[i - 1]])
                    if i < len(sorted_grades) - 1:
                        related_ids.extend(grade_standards[sorted_grades[i + 1]])

                    if related_ids:
                        _, strand = self._parse_standard_id(std_id)
                        relationships.append(
                            AlignmentRelationship(
                                standard_id=std_id,
                                related_standard_ids=related_ids,
                                relationship_type="vertical",
                                grade_level=grade,
                                strand_code=strand or "Unknown",
                                description=f"Progression: {skill_name}",
                                page_number=page_num,
                            )
                        )

        return relationships

    def _process_general_table(
        self, table: List[List[Optional[str]]], page_num: int
    ) -> List[AlignmentRelationship]:
        """Process general alignment table"""

        relationships = []

        # Extract all standard IDs from table
        all_standards = set()
        for row in table:
            for cell in row:
                if cell:
                    std_ids = re.findall(self.standard_pattern, str(cell))
                    all_standards.update(std_ids)

        # Create basic relationships based on co-occurrence
        for std_id in all_standards:
            grade, strand = self._parse_standard_id(std_id)
            related_ids = [s for s in all_standards if s != std_id][
                :5
            ]  # Limit to 5 related

            if related_ids:
                relationships.append(
                    AlignmentRelationship(
                        standard_id=std_id,
                        related_standard_ids=related_ids,
                        relationship_type="general",
                        grade_level=grade or "Unknown",
                        strand_code=strand or "Unknown",
                        description="Related standards",
                        page_number=page_num,
                    )
                )

        return relationships

    def _extract_from_text(
        self, pages: List[ParsedPage], alignment_type: str
    ) -> List[AlignmentRelationship]:
        """Enhanced text-based extraction with proximity analysis"""

        relationships = []

        for page in pages:
            # Extract all standard IDs with their positions in text
            text = page.raw_text

            # Find all matches with positions
            matches = []
            for match in re.finditer(self.standard_pattern, text):
                std_id = match.group(0)
                position = match.start()
                matches.append((std_id, position))

            if not matches:
                continue

            # Group standards by proximity (within 200 characters)
            proximity_threshold = 200

            for i, (std_id, pos) in enumerate(matches):
                grade, strand = self._parse_standard_id(std_id)

                # Find nearby standards
                related_ids = []
                for j, (other_id, other_pos) in enumerate(matches):
                    if i != j and abs(pos - other_pos) < proximity_threshold:
                        related_ids.append(other_id)

                # If no nearby standards, try grouping by same grade or strand on page
                if not related_ids:
                    for j, (other_id, other_pos) in enumerate(matches):
                        if i != j:
                            other_grade, other_strand = self._parse_standard_id(
                                other_id
                            )
                            # Group by same grade (horizontal) or same strand (vertical)
                            if alignment_type == "horizontal" and grade == other_grade:
                                related_ids.append(other_id)
                            elif (
                                alignment_type == "vertical" and strand == other_strand
                            ):
                                related_ids.append(other_id)

                # Limit to top 5 related standards
                related_ids = list(set(related_ids))[:5]

                if related_ids:
                    # Determine relationship description
                    if alignment_type == "horizontal":
                        desc = f"Standards aligned within grade {grade}"
                    elif alignment_type == "vertical":
                        desc = f"Standards showing {strand} strand progression"
                    else:
                        desc = "Related standards"

                    relationships.append(
                        AlignmentRelationship(
                            standard_id=std_id,
                            related_standard_ids=related_ids,
                            relationship_type=alignment_type,
                            grade_level=grade or "Unknown",
                            strand_code=strand or "Unknown",
                            description=desc,
                            page_number=page.page_number,
                        )
                    )

        return relationships

    def _extract_progressions(
        self, pages: List[ParsedPage]
    ) -> List[ProgressionMapping]:
        """Extract skill progressions from vertical alignment"""

        # This would need more sophisticated parsing
        # Placeholder for now
        return []

    def _parse_standard_id(self, std_id: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse standard ID into grade and strand"""

        match = re.match(r"^(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)", std_id)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def _extract_grade_from_header(self, header: Optional[str]) -> Optional[str]:
        """Extract grade level from table header"""

        if not header:
            return None

        header_upper = str(header).upper()

        for grade in self.grade_order:
            if grade in header_upper:
                return grade

        # Check for grade names
        # Note: Kindergarten is stored as "0" in database for proper sorting before Grade 1
        grade_names = {
            "KINDERGARTEN": "0",
            "FIRST": "1",
            "SECOND": "2",
            "THIRD": "3",
            "FOURTH": "4",
            "FIFTH": "5",
            "SIXTH": "6",
            "SEVENTH": "7",
            "EIGHTH": "8",
            "BEGINNING": "BE",
            "INTERMEDIATE": "IN",
            "ADVANCED": "AD",
            "ACCOMPLISHED": "AC",
        }

        for name, grade in grade_names.items():
            if name in header_upper:
                return grade

        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about parsed alignments"""

        if not self.relationships:
            return {}

        relationship_type_dist = {}
        strand_dist = {}
        grade_dist = {}

        for rel in self.relationships:
            relationship_type_dist[rel.relationship_type] = (
                relationship_type_dist.get(rel.relationship_type, 0) + 1
            )
            strand_dist[rel.strand_code] = strand_dist.get(rel.strand_code, 0) + 1
            grade_dist[rel.grade_level] = grade_dist.get(rel.grade_level, 0) + 1

        return {
            "total_relationships": len(self.relationships),
            "total_progressions": len(self.progressions),
            "relationship_type_distribution": relationship_type_dist,
            "strand_distribution": strand_dist,
            "grade_distribution": grade_dist,
            "average_related_standards": sum(
                len(r.related_standard_ids) for r in self.relationships
            )
            / len(self.relationships)
            if self.relationships
            else 0,
        }
