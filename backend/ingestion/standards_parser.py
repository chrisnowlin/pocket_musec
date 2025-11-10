"""Production NC Music Standards parser - Vision-first with hybrid fallback"""

import re
import os
import json
import base64
import io
import tempfile
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
import logging
from pathlib import Path
import time

# PDF to image conversion
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

# Import fallback parser
from .standards_parser_hybrid import NCStandardsParser as HybridParser
from .pdf_parser import PDFReader
from ..repositories.models import Standard, Objective
from ..llm.chutes_client import ChutesClient, Message, ChutesAPIError

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
    """Vision-first parser using Chutes Qwen VL model with hybrid fallback"""
    
    def __init__(self, force_fallback: bool = False):
        """
        Initialize parser
        
        Args:
            force_fallback: If True, skip vision and use hybrid parser directly
        """
        self.pdf_reader = PDFReader()
        self.parsed_standards: List[ParsedStandard] = []
        self.force_fallback = force_fallback
        
        # Check if vision processing is available
        self.vision_available = (
            not force_fallback and 
            PDF2IMAGE_AVAILABLE and 
            PIL_AVAILABLE
        )
        
        # Initialize Chutes client for vision processing
        if self.vision_available:
            try:
                self.llm_client = ChutesClient()
                self.vision_model = self.llm_client.default_model
                logger.info(f"Vision processing initialized with {self.vision_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Chutes client: {e}")
                self.vision_available = False
        
        # Initialize hybrid parser as fallback
        self.hybrid_parser = HybridParser()
        
        # NC Standards strand mappings
        self.strand_mappings = {
            "CN": ("Connect", "Connect music with other arts, other disciplines, and diverse contexts"),
            "CR": ("Create", "Conceive and develop new artistic ideas and work"),
            "PR": ("Present", "Analyze, interpret, and select artistic work for presentation"),
            "RE": ("Respond", "Interpret and intent and meaning in artistic work")
        }
        
        # Patterns for validation
        self.standard_id_pattern = r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+"
        self.objective_pattern = r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+"
        
    def parse_standards_document(self, pdf_path: str) -> List[ParsedStandard]:
        """
        Parse NC standards PDF using vision-first approach with fallback
        
        Args:
            pdf_path: Path to the PDF document
            
        Returns:
            List of parsed standards
        """
        logger.info(f"Parsing NC standards document: {pdf_path}")
        logger.info(f"Vision processing: {'enabled' if self.vision_available else 'disabled (using fallback)'}")
        
        # Try vision-first extraction
        if self.vision_available:
            try:
                start_time = time.time()
                self.parsed_standards = self._extract_with_vision(pdf_path)
                elapsed_time = time.time() - start_time
                
                logger.info(f"Vision extraction successful in {elapsed_time:.2f}s")
                logger.info(f"Extracted {len(self.parsed_standards)} standards")
                
                # Validate vision results
                if self._validate_extraction(self.parsed_standards):
                    return self.parsed_standards
                else:
                    logger.warning("Vision extraction validation failed, falling back to hybrid")
                    
            except ChutesAPIError as e:
                logger.error(f"Chutes API error: {e}, falling back to hybrid parser")
            except Exception as e:
                logger.error(f"Vision extraction failed: {e}, falling back to hybrid parser")
        
        # Fallback to hybrid parser
        logger.info("Using hybrid parser (fallback mode)")
        self.parsed_standards = self.hybrid_parser.parse_standards_document(pdf_path)
        logger.info(f"Hybrid parser extracted {len(self.parsed_standards)} standards")
        
        return self.parsed_standards
    
    def _extract_with_vision(self, pdf_path: str) -> List[ParsedStandard]:
        """
        Extract standards using Chutes Qwen VL model for all pages
        
        Args:
            pdf_path: Path to PDF document
            
        Returns:
            List of parsed standards
        """
        all_standards = {}  # Use dict to prevent duplicates
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert PDF to images
            logger.info("Converting PDF to images...")
            images = convert_from_path(
                pdf_path,
                dpi=150,  # Good balance of quality and size
                output_folder=temp_dir
            )
            
            total_pages = len(images)
            logger.info(f"Processing {total_pages} pages with vision model")
            
            # Process each page
            for page_num, image in enumerate(images, 1):
                # Skip cover pages and appendices
                if page_num == 1 or page_num > 40:  # Adjust based on document structure
                    continue
                
                try:
                    logger.info(f"Processing page {page_num}/{total_pages}...")
                    
                    # Process page with vision
                    page_results = self._process_page_with_vision(image, page_num)
                    
                    # Add standards from this page
                    for std in page_results:
                        # Use standard_id as key to prevent duplicates
                        if std.standard_id not in all_standards:
                            all_standards[std.standard_id] = std
                        else:
                            # Merge objectives if standard already exists
                            existing = all_standards[std.standard_id]
                            existing_obj_ids = self._extract_objective_ids(existing.objectives)
                            
                            for obj in std.objectives:
                                obj_id = self._extract_objective_id(obj)
                                if obj_id and obj_id not in existing_obj_ids:
                                    existing.objectives.append(obj)
                                    existing_obj_ids.add(obj_id)
                    
                    # Add small delay to avoid rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Failed to process page {page_num}: {e}")
                    continue
        
        # Sort standards by ID for consistent ordering
        sorted_standards = sorted(all_standards.values(), key=lambda s: (
            self._grade_sort_key(s.grade_level),
            s.strand_code,
            self._standard_number(s.standard_id)
        ))
        
        return sorted_standards
    
    def _process_page_with_vision(self, image: Image.Image, page_num: int) -> List[ParsedStandard]:
        """
        Process a single page image with Chutes Qwen VL model
        
        Args:
            image: PIL Image object
            page_num: Page number
            
        Returns:
            List of standards found on this page
        """
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
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                ]
            )
        ]
        
        # Call Chutes API with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.llm_client.chat_completion(
                    messages=messages,
                    model=self.vision_model,
                    temperature=0.1,  # Low temperature for accuracy
                    max_tokens=3000,  # Enough for detailed extraction
                    timeout=30  # 30 second timeout per page
                )
                
                # Parse response and create standards
                return self._parse_vision_response(response.content, page_num)
                
            except ChutesAPIError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Chutes API error on attempt {attempt + 1}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
    
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
    
    def _parse_vision_response(self, response: str, page_num: int) -> List[ParsedStandard]:
        """Parse JSON response from vision model into standards"""
        
        try:
            # Extract JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "[" in response:
                # Find JSON array
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
                if item.get('type') == 'standard':
                    std_id = item.get('id')
                    if std_id:
                        standards_dict[std_id] = item
                elif item.get('type') == 'objective':
                    std_id = item.get('standard_id')
                    if std_id:
                        if std_id not in objectives_dict:
                            objectives_dict[std_id] = []
                        objectives_dict[std_id].append(item)
            
            # Build ParsedStandard objects
            parsed_standards = []
            
            for std_id, std_data in standards_dict.items():
                grade = std_data.get('grade', std_id.split('.')[0])
                strand_code = std_data.get('strand', std_id.split('.')[1] if '.' in std_id else 'CN')
                
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
                    strand_name=self.strand_mappings.get(strand_code, ("Unknown", ""))[0],
                    strand_description=self.strand_mappings.get(strand_code, ("", "Unknown"))[1],
                    standard_id=std_id,
                    standard_text=f"{std_id} {std_data.get('text', '')}",
                    objectives=objectives,
                    source_document="",
                    page_number=page_num
                )
                
                parsed_standards.append(parsed_standard)
            
            return parsed_standards
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse vision response on page {page_num}: {e}")
            return []
    
    def _validate_extraction(self, standards: List[ParsedStandard]) -> bool:
        """
        Validate extraction results for completeness
        
        Args:
            standards: List of parsed standards
            
        Returns:
            True if extraction seems complete and valid
        """
        if not standards:
            return False
        
        # Check for minimum expected standards
        if len(standards) < 50:  # NC standards typically have 80+ standards
            logger.warning(f"Only {len(standards)} standards found, expected more")
            return False
        
        # Check grade distribution
        grades = set(s.grade_level for s in standards)
        expected_grades = {'K', '1', '2', '3', '4', '5', '6', '7', '8'}
        
        if not expected_grades.issubset(grades):
            missing = expected_grades - grades
            logger.warning(f"Missing grades: {missing}")
            return False
        
        # Check strand distribution
        strands = set(s.strand_code for s in standards)
        expected_strands = {'CN', 'CR', 'PR', 'RE'}
        
        if strands != expected_strands:
            logger.warning(f"Unexpected strand distribution: {strands}")
            return False
        
        # Check for objectives
        total_objectives = sum(len(s.objectives) for s in standards)
        if total_objectives < 100:  # Typically 150+ objectives
            logger.warning(f"Only {total_objectives} objectives found, expected more")
            return False
        
        # Specific check for K.CN.1.1
        k_cn_1 = next((s for s in standards if s.standard_id == 'K.CN.1'), None)
        if k_cn_1:
            has_k_cn_1_1 = any('K.CN.1.1' in obj for obj in k_cn_1.objectives)
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
        
        if grade == 'K':
            return (0, 'K')
        elif grade.isdigit():
            return (1, int(grade))
        else:
            # BE, IN, AD, AC
            order = {'BE': 2, 'IN': 3, 'AD': 4, 'AC': 5}
            return (order.get(grade, 99), grade)
    
    def _standard_number(self, standard_id: str) -> int:
        """Extract standard number for sorting"""
        
        parts = standard_id.split('.')
        if len(parts) >= 3:
            try:
                return int(parts[2])
            except ValueError:
                return 0
        return 0
    
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
            
            # Create objectives
            for obj_text in parsed.objectives:
                # Extract objective ID
                obj_match = re.match(self.objective_pattern, obj_text)
                if obj_match:
                    objective_id = obj_match.group(0)
                else:
                    # Fallback
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
        
        grade_dist = {}
        strand_dist = {}
        
        for std in self.parsed_standards:
            grade_dist[std.grade_level] = grade_dist.get(std.grade_level, 0) + 1
            strand_dist[std.strand_code] = strand_dist.get(std.strand_code, 0) + 1
        
        return {
            "total_standards": len(self.parsed_standards),
            "total_objectives": sum(len(s.objectives) for s in self.parsed_standards),
            "average_objectives_per_standard": (
                sum(len(s.objectives) for s in self.parsed_standards) / len(self.parsed_standards)
                if self.parsed_standards else 0
            ),
            "grade_distribution": grade_dist,
            "strand_distribution": strand_dist,
            "extraction_method": "vision" if self.vision_available else "hybrid_fallback"
        }