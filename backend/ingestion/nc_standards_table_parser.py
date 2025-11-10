"""Table-based NC Music Standards parser for accurate extraction"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logging.warning("pdfplumber not available. Install with: pip install pdfplumber")

from backend.repositories.models import Standard, Objective

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


class NCStandardsParser:
    """Table-based parser for North Carolina Music Standards PDFs"""
    
    def __init__(self):
        self.parsed_standards: List[ParsedStandard] = []
        
        # NC Standards strand mappings
        self.strand_mappings = {
            "CN": ("Connect", "Connect music with other arts, other disciplines, and diverse contexts"),
            "CR": ("Create", "Conceive and develop new artistic ideas and work"),
            "PR": ("Present", "Analyze, interpret, and select artistic work for presentation"),
            "RE": ("Respond", "Interpret and intent and meaning in artistic work")
        }
        
        # Patterns for validation
        self.standard_id_pattern = r"^(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+"
        self.objective_pattern = r"^(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+"
        
    def parse_standards_document(self, pdf_path: str, max_page: Optional[int] = None) -> List[ParsedStandard]:
        """
        Parse a NC standards PDF document using table extraction
        
        Args:
            pdf_path: Path to the PDF file
            max_page: Maximum page number to parse (1-indexed). If None, parse all pages.
                     For General Music standards only, use max_page=34.
        """
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
                grade = self._extract_grade_from_text(page_text)
                if grade:
                    current_grade = grade
                    logger.debug(f"Found grade level: {grade}")
                
                # Detect strand
                strand_info = self._extract_strand_from_text(page_text)
                if strand_info:
                    current_strand_code, current_strand_name = strand_info
                    logger.debug(f"Found strand: {current_strand_code} - {current_strand_name}")
                
                # Extract tables
                tables = page.extract_tables()
                
                for table in tables:
                    if not table:
                        continue
                    
                    # Extract strand from this table's first row if it exists
                    table_strand_info = self._extract_strand_from_table(table)
                    if table_strand_info:
                        current_strand_code, current_strand_name = table_strand_info
                        logger.debug(f"Found strand in table: {current_strand_code} - {current_strand_name}")
                    
                    # Process table rows
                    page_standards = self._extract_standards_from_table(
                        table, 
                        current_grade, 
                        current_strand_code,
                        current_strand_name,
                        page_num
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
        
        logger.info(f"Extracted {len(standards)} standards from tables (after deduplication)")
        self.parsed_standards = standards
        return standards
    
    def _extract_standards_from_table(
        self, 
        table: List[List[str]], 
        grade: Optional[str],
        strand_code: Optional[str],
        strand_name: Optional[str],
        page_num: int
    ) -> List[ParsedStandard]:
        """Extract standards from a table structure (handles 2-column and 4-column formats)"""
        standards = []
        current_standard = None
        current_standard_text_parts = []
        current_objectives = []
        
        # Detect table format (2-column or 4-column)
        # 4-column tables have standard text in column 1 and objectives in column 3
        is_four_column = len(table[0]) > 2 if table else False
        
        standard_col = 1 if is_four_column else 0
        objectives_col = 3 if is_four_column else 1
        
        for row in table:
            if not row or len(row) <= standard_col:
                continue
            
            # Get cells based on format
            standard_cell = row[standard_col] if len(row) > standard_col and row[standard_col] else ""
            objectives_cell = row[objectives_col] if len(row) > objectives_col and row[objectives_col] else ""
            
            # Also check column 0 in 4-column format (sometimes standards appear there too)
            if is_four_column and len(row) > 0 and row[0]:
                alt_cell = row[0]
                if self._contains_standard_id(alt_cell):
                    standard_cell = alt_cell
            
            # Skip header rows
            if "Standard" in standard_cell or "Objectives" in objectives_cell:
                continue
            
            # Skip strand description rows
            if any(strand in standard_cell for strand in ["CN -", "CR -", "PR -", "RE -"]):
                continue
            
            # Check if cell contains a standard ID
            if standard_cell and self._contains_standard_id(standard_cell):
                # Save previous standard if exists
                if current_standard and current_standard_text_parts:
                    full_text = ' '.join(current_standard_text_parts)
                    std = self._build_standard(
                        current_standard,
                        full_text,
                        current_objectives,
                        grade,
                        strand_code,
                        strand_name,
                        page_num
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
                # This is continuation of standard text (for 4-column format where text spans multiple rows)
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
            full_text = ' '.join(current_standard_text_parts)
            std = self._build_standard(
                current_standard,
                full_text,
                current_objectives,
                grade,
                strand_code,
                strand_name,
                page_num
            )
            if std:
                standards.append(std)
        
        return standards
    
    def _is_header_text(self, text: str) -> bool:
        """Check if text is a header or meta text that should be skipped"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in [
            "standard", "objectives", "cn -", "cr -", "pr -", "re -"
        ])
    
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
            standard_text = re.sub(r'\s+', ' ', standard_text)
            return standard_text
        return ""
    
    def _extract_objectives(self, text: str) -> List[str]:
        """Extract all objectives from text"""
        objectives = []
        
        # Split by objective pattern
        lines = text.split('\n')
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
    
    def _extract_grade_from_text(self, text: str) -> Optional[str]:
        """Extract grade level from page text"""
        text_upper = text.upper()
        
        # Check for specific grade patterns
        if "KINDERGARTEN" in text_upper:
            return "K"
        
        # Check for numbered grades (First Grade, Second Grade, etc.)
        grade_map = {
            "FIRST GRADE": "1",
            "SECOND GRADE": "2",
            "THIRD GRADE": "3",
            "FOURTH GRADE": "4",
            "FIFTH GRADE": "5",
            "SIXTH GRADE": "6",
            "SEVENTH GRADE": "7",
            "EIGHTH GRADE": "8"
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
            "RESPOND": "RE"
        }
        
        for keyword, code in strand_keywords.items():
            if keyword in text_upper:
                strand_name = self.strand_mappings.get(code, (keyword.title(), ""))[0]
                return (code, strand_name)
        
        return None
    
    def _extract_strand_from_table(self, table: List[List[str]]) -> Optional[Tuple[str, str]]:
        """Extract strand code and name from table's first row"""
        if not table or len(table) < 1:
            return None
        
        # Check the first row for strand header
        first_row = table[0]
        if first_row and first_row[0]:
            return self._extract_strand_from_text(first_row[0])
        
        return None
    
    def _build_standard(
        self,
        standard_id: str,
        standard_text: str,
        objectives: List[str],
        grade: Optional[str],
        strand_code: Optional[str],
        strand_name: Optional[str],
        page_num: int
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
        if full_standard_text and not full_standard_text.endswith('.'):
            full_standard_text += '.'
        
        return ParsedStandard(
            grade_level=grade,
            strand_code=strand_code,
            strand_name=strand_name_full,
            strand_description=strand_description,
            standard_id=standard_id,
            standard_text=full_standard_text,
            objectives=objectives,
            source_document="",
            page_number=page_num
        )
    
    def to_database_models(self, source_document: str = "", version: str = "1.0") -> Tuple[List[Standard], List[Objective]]:
        """Convert parsed standards to database models"""
        standards = []
        objectives = []
        
        from datetime import datetime
        ingestion_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for parsed_std in self.parsed_standards:
            # Update source document
            parsed_std.source_document = source_document
            
            # Create Standard model
            standard = Standard(
                standard_id=parsed_std.standard_id,
                grade_level=parsed_std.grade_level,
                strand_code=parsed_std.strand_code,
                strand_name=parsed_std.strand_name,
                strand_description=parsed_std.strand_description,
                standard_text=parsed_std.standard_text,
                source_document=source_document,
                ingestion_date=ingestion_date,
                version=version
            )
            standards.append(standard)
            
            # Create Objective models
            for obj_text in parsed_std.objectives:
                # Extract objective ID
                obj_match = re.match(self.objective_pattern, obj_text)
                if obj_match:
                    obj_id = obj_match.group(0)
                    objective = Objective(
                        objective_id=obj_id,
                        standard_id=parsed_std.standard_id,
                        objective_text=obj_text
                    )
                    objectives.append(objective)
        
        return standards, objectives
