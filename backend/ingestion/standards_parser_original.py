"""NC Music Standards-specific parser with positional heuristics"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from .pdf_parser import PDFReader, TextBlock, ParsedPage
from ..repositories.models import Standard, Objective

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
    """Parser for North Carolina Music Standards PDFs"""
    
    def __init__(self):
        self.pdf_reader = PDFReader()
        self.parsed_standards: List[ParsedStandard] = []
        
        # NC Standards strand mappings
        self.strand_mappings = {
            "CN": ("Connect", "Connect music with other arts, other disciplines, and diverse contexts"),
            "CR": ("Create", "Conceive and develop new artistic ideas and work"),
            "PR": ("Present", "Analyze, interpret, and select artistic work for presentation"),
            "RE": ("Respond", "Interpret and intent and meaning in artistic work")
        }
        
        # Grade level patterns (more specific to avoid matching objective IDs)
        self.grade_patterns = [
            r"^Kindergarten$|^K$",
            r"^Grade\s+(\d+)$",
            r"^(\d+)th?\s+Grade$",
            r"^Beginning$|^Intermediate$|^Advanced$|^Accomplished$",
            r"Kindergarten General Music",
            r"(\d+)th Grade General Music"
        ]
        
        # Standard ID patterns
        self.standard_id_patterns = [
            r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+",
            r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+"
        ]
        
        # Objective patterns
        self.objective_patterns = [
            r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+.*"
        ]
    
    def parse_standards_document(self, pdf_path: str) -> List[ParsedStandard]:
        """Parse a NC standards PDF document"""
        logger.info(f"Parsing NC standards document: {pdf_path}")
        
        # Read PDF
        pages = self.pdf_reader.read_pdf(pdf_path)
        
        # Extract standards using heuristics
        self.parsed_standards = self._extract_standards(pages)
        
        logger.info(f"Extracted {len(self.parsed_standards)} standards")
        return self.parsed_standards
    
    def _extract_standards(self, pages: List[ParsedPage]) -> List[ParsedStandard]:
        """Extract standards from parsed pages using heuristics"""
        standards = []
        current_grade = None
        current_strand = None
        
        for page in pages:
            page_standards = self._parse_page(page, current_grade, current_strand)
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
        
        logger.info(f"Extracted {len(standards)} standards, deduplicated to {len(unique_standards)} unique standards")
        return unique_standards
    
    def _parse_page(self, page: ParsedPage, current_grade: Optional[str], 
                   current_strand: Optional[Tuple[str, str]]) -> List[ParsedStandard]:
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
                        page_number=page.page_number
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
    
    def _extract_grade_level(self, text: str) -> Optional[str]:
        """Extract grade level from text"""
        text = text.strip()
        
        # Direct matches (exact)
        if text.upper() == "KINDERGARTEN":
            return "K"
        elif text.upper() == "K":
            return "K"
        elif text.upper() == "BEGINNING":
            return "BE"
        elif text.upper() == "INTERMEDIATE":
            return "IN"
        elif text.upper() == "ADVANCED":
            return "AD"
        elif text.upper() == "ACCOMPLISHED":
            return "AC"
        
        # Pattern matches (more specific)
        for pattern in self.grade_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.groups():
                    # For grade number patterns
                    grade = match.group(1)
                    if grade.isdigit():
                        return grade
                    else:
                        return grade
                else:
                    # For full text matches
                    if "KINDERGARTEN" in text.upper():
                        return "K"
                    elif "BEGINNING" in text.upper():
                        return "BE"
                    elif "INTERMEDIATE" in text.upper():
                        return "IN"
                    elif "ADVANCED" in text.upper():
                        return "AD"
                    elif "ACCOMPLISHED" in text.upper():
                        return "AC"
        
        return None
    
    def _extract_strand(self, text: str) -> Optional[Tuple[str, str]]:
        """Extract strand information from text"""
        text = text.strip().upper()
        
        # Check for exact strand name matches first (CONNECT, CREATE, PRESENT, RESPOND)
        for code, (name, description) in self.strand_mappings.items():
            if text == name.upper() or text == code:
                return (code, name)
        
        # Check for strand descriptions (more specific patterns)
        if "CONNECT" in text and "EXPLORE AND RELATE" in text:
            return ("CN", "Connect")
        elif "CREATE" in text and "CREATE AND ADAPT" in text:
            return ("CR", "Create")
        elif "PRESENT" in text and "ANALYZE" in text:
            return ("PR", "Present")
        elif "RESPOND" in text and "INTERPRET" in text:
            return ("RE", "Respond")
        
        return None
    
    def _extract_standard_id(self, text: str) -> Optional[str]:
        """Extract standard ID from text"""
        # Pattern for standard IDs like K.CN.1, 5.CR.2, etc.
        pattern = r"(?:K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+"
        match = re.search(pattern, text.upper())
        
        if match:
            return match.group(0)
        
        return None
    
    def _extract_standard_content(self, blocks: List[TextBlock], start_idx: int) -> Tuple[str, List[str]]:
        """Extract standard text and objectives from blocks starting at start_idx"""
        if start_idx >= len(blocks):
            return "", []
        
        # The standard text is usually the block after the ID or part of it
        standard_text = ""
        objectives = []
        
        i = start_idx + 1
        if i < len(blocks):
            # Check if the next block contains the standard text
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
                # We've reached the next standard or strand
                break
            elif text and not standard_text and not self._is_objective(text):
                # This might be the standard text if we didn't capture it earlier
                # and it's not an objective
                standard_text = text
            
            i += 1
            blocks_checked += 1
        
        return standard_text, objectives
    
    def _is_objective(self, text: str) -> bool:
        """Check if text looks like an objective"""
        # Pattern for objectives like K.CN.1.1, 5.CR.2.3, etc.
        pattern = r"(?:K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+"
        return bool(re.match(pattern, text.strip()))
    
    def _extract_objective_from_text(self, text: str) -> Optional[str]:
        """Extract objective from text, even if embedded in larger text block"""
        # Pattern to find objectives anywhere in text (capture the full match)
        pattern = r"(?:K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+[^.]*(?:\.|$)"
        match = re.search(pattern, text)
        
        if match:
            objective = match.group(0).strip()
            # Clean up - ensure it ends properly
            if objective and not objective.endswith(('.', '!', '?')):
                # If it doesn't end with punctuation, it might be cut off
                # Try to find the next sentence boundary in the original text
                start_idx = text.find(objective)
                if start_idx != -1:
                    remaining_text = text[start_idx + len(objective):]
                    next_period = remaining_text.find('.')
                    if next_period != -1 and next_period < 100:  # Reasonable sentence length
                        objective += remaining_text[:next_period + 1]
            return objective
        
        return None
    
    def normalize_to_models(self, source_document: str) -> Tuple[List[Standard], List[Objective]]:
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
                ingestion_date="2024-01-01",  # Would use current date
                version="2024"
            )
            standards.append(standard)
            
            # Create objectives
            for i, obj_text in enumerate(parsed.objectives):
                objective_id = f"{parsed.standard_id}.{i+1}"
                objective = Objective(
                    objective_id=objective_id,
                    standard_id=parsed.standard_id,
                    objective_text=obj_text
                )
                objectives.append(objective)
        
        return standards, objectives
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about parsed standards"""
        if not self.parsed_standards:
            return {}
        
        grade_distribution = {}
        strand_distribution = {}
        
        for standard in self.parsed_standards:
            # Count by grade
            grade = standard.grade_level
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
            
            # Count by strand
            strand = standard.strand_code
            strand_distribution[strand] = strand_distribution.get(strand, 0) + 1
        
        return {
            "total_standards": len(self.parsed_standards),
            "total_objectives": sum(len(s.objectives) for s in self.parsed_standards),
            "average_objectives_per_standard": sum(len(s.objectives) for s in self.parsed_standards) / len(self.parsed_standards) if self.parsed_standards else 0,
            "grade_distribution": grade_distribution,
            "strand_distribution": strand_distribution
        }