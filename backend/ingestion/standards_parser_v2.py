"""Refined NC Music Standards parser with exact extraction"""

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
    """Precise parser for North Carolina Music Standards PDFs"""
    
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
        
        # More precise patterns
        self.standard_id_pattern = r"^(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+"
        self.objective_pattern = r"^(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+"
        
    def parse_standards_document(self, pdf_path: str) -> List[ParsedStandard]:
        """Parse a NC standards PDF document with exact extraction"""
        logger.info(f"Parsing NC standards document: {pdf_path}")
        
        # Read PDF
        pages = self.pdf_reader.read_pdf(pdf_path)
        
        # Extract standards using precise heuristics
        self.parsed_standards = self._extract_standards_precise(pages)
        
        logger.info(f"Extracted {len(self.parsed_standards)} standards")
        return self.parsed_standards
    
    def _extract_standards_precise(self, pages: List[ParsedPage]) -> List[ParsedStandard]:
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
                
                if standard_id and current_grade and current_strand and not self._is_objective_precise(text):
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
    
    def _extract_complete_standard(self, blocks: List[TextBlock], start_idx: int, 
                                  grade: str, strand: Tuple[str, str], page_num: int) -> Tuple[Optional[ParsedStandard], int]:
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
            if (self._extract_standard_id_precise(text) or 
                self._extract_strand_precise(text) or 
                self._extract_grade_level_precise(text)):
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
        import re
        embedded_objectives = re.findall(r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+\s+[^.]*\.", combined_text)
        
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
        standard_text = re.sub(r'\s+', ' ', standard_text).strip()
        if standard_text and not standard_text.endswith('.'):
            standard_text += '.'
        
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
            page_number=page_num
        )
        
        return parsed_standard, i
    
    def _extract_standard_id_precise(self, text: str) -> Optional[str]:
        """Extract standard ID with exact pattern matching"""
        match = re.match(self.standard_id_pattern, text.strip())
        if match:
            # Extract just the ID part (e.g., "K.CN.1" from "K.CN.1 Relate musical...")
            id_part = match.group(0)
            # Split on first space to get just the ID
            return id_part.split()[0] if ' ' in id_part else id_part
        return None
    
    def _is_objective_precise(self, text: str) -> bool:
        """Check if text is exactly an objective"""
        return bool(re.match(self.objective_pattern, text.strip()))
    
    def _extract_grade_level_precise(self, text: str) -> Optional[str]:
        """Extract grade level with precise matching"""
        text_upper = text.strip().upper()
        
        # Exact matches for specific grade indicators
        if text_upper == "KINDERGARTEN":
            return "K"
        elif text_upper == "K":
            return "K"
        elif text_upper == "BEGINNING":
            return "BE"
        elif text_upper == "INTERMEDIATE":
            return "IN"
        elif text_upper == "ADVANCED":
            return "AD"
        elif text_upper == "ACCOMPLISHED":
            return "AC"
        
        # Pattern matches for grade levels in context
        if "KINDERGARTEN GENERAL MUSIC" in text_upper:
            return "K"
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
                ingestion_date="2024-01-01",
                version="2024"
            )
            standards.append(standard)
            
            # Create objectives with proper numbering
            for i, obj_text in enumerate(parsed.objectives):
                # Extract the objective ID from the text itself
                obj_id_match = re.match(r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+", obj_text.strip())
                if obj_id_match:
                    objective_id = obj_id_match.group(0)
                else:
                    # Fallback: generate ID based on standard
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