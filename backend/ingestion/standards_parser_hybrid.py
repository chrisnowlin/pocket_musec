"""Hybrid NC Music Standards parser with exact extraction and comprehensive coverage"""

import re
from typing import List, Dict, Any, Optional, Tuple, Set
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
    """Hybrid parser for North Carolina Music Standards PDFs with exact extraction"""
    
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
        
        # Improved patterns
        self.standard_id_pattern = r"^(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+"
        self.objective_pattern = r"^(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+"
        
    def parse_standards_document(self, pdf_path: str) -> List[ParsedStandard]:
        """Parse a NC standards PDF document with exact extraction"""
        logger.info(f"Parsing NC standards document: {pdf_path}")
        
        # Read PDF
        pages = self.pdf_reader.read_pdf(pdf_path)
        
        # Extract all text blocks with their positions
        all_blocks = []
        for page_num, page in enumerate(pages):
            for block in page.text_blocks:
                all_blocks.append({
                    'page': page_num,
                    'block': block,
                    'text': block.text.strip()
                })
        
        # Extract standards using comprehensive approach
        self.parsed_standards = self._extract_standards_comprehensive(all_blocks, pages)
        
        logger.info(f"Extracted {len(self.parsed_standards)} standards")
        return self.parsed_standards
    
    def _extract_standards_comprehensive(self, all_blocks: List[Dict], pages: List[ParsedPage]) -> List[ParsedStandard]:
        """Extract standards with comprehensive coverage and exact matching"""
        standards = []
        processed_standard_ids = set()
        
        # First pass: Find all standard IDs and their associated content
        standard_blocks = {}
        
        for i, block_info in enumerate(all_blocks):
            text = block_info['text']
            
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
                standard = self._build_standard(std_id, blocks, current_grade, current_strand)
                if standard:
                    standards.append(standard)
        
        return standards
    
    def _contains_standard_id(self, text: str) -> bool:
        """Check if text contains a standard ID pattern"""
        return bool(re.search(self.standard_id_pattern, text))
    
    def _extract_standard_id(self, text: str) -> Optional[str]:
        """Extract standard ID with exact pattern matching"""
        match = re.search(self.standard_id_pattern, text)
        if match:
            # Get just the ID part (e.g., "K.CN.1" from "K.CN.1 Relate musical...")
            id_part = match.group(0)
            # Ensure we get the base standard ID, not an objective
            if not re.match(self.objective_pattern, id_part):
                return id_part
            else:
                # Extract standard ID from objective (e.g., "K.CN.1" from "K.CN.1.1")
                parts = id_part.split('.')
                if len(parts) >= 3:
                    return '.'.join(parts[:3])
        return None
    
    def _gather_standard_blocks(self, all_blocks: List[Dict], start_idx: int, std_id: str) -> List[Dict]:
        """Gather all blocks related to a standard"""
        related_blocks = []
        
        # Look backward for objectives that come before the standard
        for j in range(start_idx - 1, max(0, start_idx - 10), -1):
            block_text = all_blocks[j]['text']
            if block_text.startswith(std_id + '.'):
                related_blocks.insert(0, all_blocks[j])
            elif self._contains_standard_id(block_text) and not block_text.startswith(std_id):
                # Hit a different standard, stop
                break
        
        # Include the standard block itself
        related_blocks.append(all_blocks[start_idx])
        
        # Look forward for standard text and objectives
        for j in range(start_idx + 1, min(len(all_blocks), start_idx + 20)):
            block_text = all_blocks[j]['text']
            
            # Stop if we hit another standard or a strand/grade header
            if self._contains_standard_id(block_text) and not block_text.startswith(std_id):
                break
            if self._is_strand_header(block_text) or self._is_grade_header(block_text):
                break
            
            # Include objectives and standard text
            if block_text.startswith(std_id + '.') or not self._contains_standard_id(block_text):
                related_blocks.append(all_blocks[j])
        
        return related_blocks
    
    def _build_standard(self, std_id: str, blocks: List[Dict], grade: str, strand: Tuple[str, str]) -> Optional[ParsedStandard]:
        """Build a complete standard from its blocks"""
        standard_text_parts = []
        objectives = []
        objectives_seen = set()
        
        for block_info in blocks:
            text = block_info['text']
            
            # Check if this is an objective
            if self._is_objective(text):
                # Ensure it belongs to this standard
                if text.startswith(std_id + '.'):
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
        standard_text = ' '.join(standard_text_parts)
        
        # Clean up standard text
        standard_text = re.sub(r'\s+', ' ', standard_text).strip()
        
        # Ensure we have the standard ID at the beginning
        if not standard_text.startswith(std_id):
            standard_text = f"{std_id} {standard_text}"
        
        # Ensure proper ending
        if standard_text and not standard_text.endswith('.'):
            standard_text += '.'
        
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
            page_number=blocks[0]['page'] if blocks else 0
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
            "KINDERGARTEN" in text_upper or
            "BEGINNING" in text_upper or
            "INTERMEDIATE" in text_upper or
            "ADVANCED" in text_upper or
            "ACCOMPLISHED" in text_upper or
            bool(re.search(r"\d+TH GRADE", text_upper))
        )
    
    def _extract_grade_from_id(self, std_id: str) -> Optional[str]:
        """Extract grade level from standard ID"""
        parts = std_id.split('.')
        if parts:
            return parts[0]
        return None
    
    def _extract_strand_from_id(self, std_id: str) -> Optional[str]:
        """Extract strand code from standard ID"""
        parts = std_id.split('.')
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
            
            # Create objectives with proper IDs
            for obj_text in parsed.objectives:
                # Extract the objective ID from the text
                obj_id_match = re.match(r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+", obj_text.strip())
                if obj_id_match:
                    objective_id = obj_id_match.group(0)
                else:
                    # Fallback: generate ID
                    objective_id = f"{parsed.standard_id}.{len(objectives)+1}"
                
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