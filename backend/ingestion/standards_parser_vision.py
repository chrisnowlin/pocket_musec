"""Vision-enhanced NC Music Standards parser using Qwen VL model"""

import re
import base64
import io
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from pathlib import Path
import tempfile

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

from .pdf_parser import PDFReader, TextBlock, ParsedPage
from ..repositories.models import Standard, Objective
from ..llm.chutes_client import ChutesClient, Message

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


@dataclass 
class VisionExtractionResult:
    """Result from vision model extraction"""
    standards: List[Dict[str, Any]]
    objectives: List[Dict[str, Any]]
    layout_info: Dict[str, Any]
    confidence: float


class NCStandardsParser:
    """Vision-enhanced parser for North Carolina Music Standards PDFs"""
    
    def __init__(self, use_vision: bool = True):
        self.pdf_reader = PDFReader()
        self.parsed_standards: List[ParsedStandard] = []
        self.use_vision = use_vision and PDF2IMAGE_AVAILABLE and PIL_AVAILABLE
        
        if self.use_vision:
            self.llm_client = ChutesClient()
            self.vision_model = "Qwen/Qwen2-VL-7B-Instruct"  # Or appropriate vision model
        
        # NC Standards strand mappings
        self.strand_mappings = {
            "CN": ("Connect", "Connect music with other arts, other disciplines, and diverse contexts"),
            "CR": ("Create", "Conceive and develop new artistic ideas and work"),
            "PR": ("Present", "Analyze, interpret, and select artistic work for presentation"),
            "RE": ("Respond", "Interpret and intent and meaning in artistic work")
        }
        
        # Patterns for text-based extraction
        self.standard_id_pattern = r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+"
        self.objective_pattern = r"(K|\d+|BE|IN|AD|AC)\.(CN|CR|PR|RE)\.\d+\.\d+"
        
    def parse_standards_document(self, pdf_path: str) -> List[ParsedStandard]:
        """Parse a NC standards PDF document with optional vision enhancement"""
        logger.info(f"Parsing NC standards document: {pdf_path}")
        logger.info(f"Vision enhancement: {'enabled' if self.use_vision else 'disabled'}")
        
        # First, do text-based extraction for baseline
        pages = self.pdf_reader.read_pdf(pdf_path)
        text_standards = self._extract_standards_text(pages)
        
        # If vision is enabled, enhance with visual understanding
        if self.use_vision:
            try:
                vision_results = self._extract_with_vision(pdf_path)
                self.parsed_standards = self._merge_extraction_results(
                    text_standards, 
                    vision_results
                )
                logger.info(f"Vision enhancement successful - extracted {len(self.parsed_standards)} standards")
            except Exception as e:
                logger.error(f"Vision extraction failed: {e}, falling back to text-only")
                self.parsed_standards = text_standards
        else:
            self.parsed_standards = text_standards
        
        logger.info(f"Total extracted: {len(self.parsed_standards)} standards")
        return self.parsed_standards
    
    def _extract_with_vision(self, pdf_path: str) -> VisionExtractionResult:
        """Extract standards using vision model for better layout understanding"""
        
        logger.info("Converting PDF to images for vision processing...")
        
        # Convert PDF pages to images
        with tempfile.TemporaryDirectory() as temp_dir:
            images = convert_from_path(
                pdf_path, 
                dpi=150,  # Balance between quality and processing time
                output_folder=temp_dir
            )
            
            all_standards = []
            all_objectives = []
            
            # Process each page with vision model
            for page_num, image in enumerate(images[:10], 1):  # Limit to first 10 pages for now
                logger.info(f"Processing page {page_num} with vision model...")
                
                # Convert image to base64
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                
                # Create prompt for vision model
                vision_prompt = self._create_vision_prompt(page_num)
                
                # Call vision model
                messages = [
                    Message(
                        role="user",
                        content=[
                            {
                                "type": "text",
                                "text": vision_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    )
                ]
                
                try:
                    response = self.llm_client.chat_completion(
                        messages=messages,
                        model=self.vision_model,
                        temperature=0.1,  # Low temperature for accuracy
                        max_tokens=2000
                    )
                    
                    # Parse the structured response
                    result = self._parse_vision_response(response.content, page_num)
                    all_standards.extend(result.get('standards', []))
                    all_objectives.extend(result.get('objectives', []))
                    
                except Exception as e:
                    logger.error(f"Vision processing failed for page {page_num}: {e}")
                    continue
            
            return VisionExtractionResult(
                standards=all_standards,
                objectives=all_objectives,
                layout_info={},
                confidence=0.9
            )
    
    def _create_vision_prompt(self, page_num: int) -> str:
        """Create a detailed prompt for the vision model"""
        
        return f"""You are analyzing page {page_num} of a North Carolina Music Standards document.

Please extract ALL standards and objectives from this page with exact text. The document structure is:

1. GRADE LEVELS: Look for headers like "Kindergarten", "1st Grade", "2nd Grade", etc.
2. STRANDS: Four main categories - Connect (CN), Create (CR), Present (PR), Respond (RE)
3. STANDARDS: Format like "K.CN.1", "1.CR.2", etc. followed by descriptive text
4. OBJECTIVES: Format like "K.CN.1.1", "1.CR.2.3", etc. with specific learning objectives

IMPORTANT EXTRACTION RULES:
- Extract the COMPLETE text for each standard and objective, not just fragments
- Preserve the exact formatting and punctuation
- Include ALL objectives, even if they appear before or after their parent standard
- Pay special attention to objectives that might be in different columns or positions

Return your extraction in this JSON format:
{{
    "standards": [
        {{
            "id": "K.CN.1",
            "text": "Complete standard text here",
            "grade": "K",
            "strand": "CN",
            "page": {page_num}
        }}
    ],
    "objectives": [
        {{
            "id": "K.CN.1.1", 
            "standard_id": "K.CN.1",
            "text": "Complete objective text here",
            "page": {page_num}
        }}
    ],
    "layout_notes": "Any important observations about the page layout"
}}

Focus on accuracy and completeness. Extract EVERYTHING, even if text spans multiple lines."""
    
    def _parse_vision_response(self, response: str, page_num: int) -> Dict[str, Any]:
        """Parse the structured response from the vision model"""
        
        try:
            # Try to parse as JSON first
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "{" in response:
                # Find JSON object in response
                start = response.index("{")
                end = response.rindex("}") + 1
                json_str = response[start:end]
            else:
                json_str = response
                
            result = json.loads(json_str)
            
            # Add page numbers if not present
            for standard in result.get('standards', []):
                if 'page' not in standard:
                    standard['page'] = page_num
                    
            for objective in result.get('objectives', []):
                if 'page' not in objective:
                    objective['page'] = page_num
                    
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse vision response as JSON: {e}")
            
            # Fallback: try to extract using regex
            return self._extract_from_text_response(response, page_num)
    
    def _extract_from_text_response(self, response: str, page_num: int) -> Dict[str, Any]:
        """Fallback extraction from non-JSON response"""
        
        standards = []
        objectives = []
        
        # Look for standard patterns in the response
        standard_matches = re.findall(
            r'(' + self.standard_id_pattern + r')\s*[:\-]?\s*([^\n]+)', 
            response
        )
        
        for match in standard_matches:
            std_id = match[0]
            std_text = match[1].strip()
            
            if not re.match(self.objective_pattern, std_id):
                # It's a standard, not an objective
                standards.append({
                    'id': std_id,
                    'text': f"{std_id} {std_text}",
                    'page': page_num
                })
        
        # Look for objectives
        objective_matches = re.findall(
            r'(' + self.objective_pattern + r')\s*[:\-]?\s*([^\n]+)',
            response
        )
        
        for match in objective_matches:
            obj_id = match[0]
            obj_text = match[1].strip()
            
            # Extract parent standard ID
            parts = obj_id.split('.')
            if len(parts) >= 3:
                standard_id = '.'.join(parts[:3])
                
                objectives.append({
                    'id': obj_id,
                    'standard_id': standard_id,
                    'text': f"{obj_id} {obj_text}",
                    'page': page_num
                })
        
        return {
            'standards': standards,
            'objectives': objectives
        }
    
    def _merge_extraction_results(
        self, 
        text_standards: List[ParsedStandard],
        vision_results: VisionExtractionResult
    ) -> List[ParsedStandard]:
        """Merge text-based and vision-based extraction results"""
        
        merged_standards = {}
        
        # Start with text-based extraction
        for std in text_standards:
            merged_standards[std.standard_id] = std
        
        # Enhance with vision results
        for vision_std in vision_results.standards:
            std_id = vision_std['id']
            
            if std_id in merged_standards:
                # Enhance existing standard
                existing = merged_standards[std_id]
                
                # Use vision text if it's longer/more complete
                vision_text = vision_std.get('text', '')
                if len(vision_text) > len(existing.standard_text):
                    existing.standard_text = vision_text
            else:
                # Add new standard from vision
                grade = vision_std.get('grade', std_id.split('.')[0])
                strand_code = vision_std.get('strand', std_id.split('.')[1])
                
                merged_standards[std_id] = ParsedStandard(
                    grade_level=grade,
                    strand_code=strand_code,
                    strand_name=self.strand_mappings.get(strand_code, ("Unknown", ""))[0],
                    strand_description=self.strand_mappings.get(strand_code, ("", "Unknown"))[1],
                    standard_id=std_id,
                    standard_text=vision_std.get('text', ''),
                    objectives=[],
                    source_document="",
                    page_number=vision_std.get('page', 0)
                )
        
        # Add objectives from vision
        for vision_obj in vision_results.objectives:
            std_id = vision_obj.get('standard_id')
            if std_id in merged_standards:
                obj_text = vision_obj.get('text', '')
                
                # Check if objective already exists
                existing_obj_ids = [
                    obj.split()[0] if ' ' in obj else obj 
                    for obj in merged_standards[std_id].objectives
                ]
                
                obj_id = vision_obj.get('id')
                if obj_id not in existing_obj_ids and obj_text:
                    merged_standards[std_id].objectives.append(obj_text)
        
        # Sort objectives for each standard
        for std in merged_standards.values():
            std.objectives.sort()
        
        return list(merged_standards.values())
    
    def _extract_standards_text(self, pages: List[ParsedPage]) -> List[ParsedStandard]:
        """Text-based extraction as fallback/baseline"""
        
        # Use the hybrid approach from before
        standards = []
        all_blocks = []
        
        for page_num, page in enumerate(pages):
            for block in page.text_blocks:
                all_blocks.append({
                    'page': page_num,
                    'block': block,
                    'text': block.text.strip()
                })
        
        # Process blocks to extract standards
        standard_blocks = {}
        processed_ids = set()
        
        for i, block_info in enumerate(all_blocks):
            text = block_info['text']
            
            # Look for standard IDs
            std_match = re.search(self.standard_id_pattern, text)
            if std_match:
                std_id = std_match.group(0)
                
                # Check if it's an objective
                if not re.match(self.objective_pattern, std_id):
                    if std_id not in processed_ids:
                        processed_ids.add(std_id)
                        
                        # Gather related blocks
                        related = self._gather_related_blocks(all_blocks, i, std_id)
                        standard_blocks[std_id] = related
        
        # Build standards from blocks
        for std_id, blocks in standard_blocks.items():
            standard = self._build_standard_from_blocks(std_id, blocks)
            if standard:
                standards.append(standard)
        
        return standards
    
    def _gather_related_blocks(
        self, 
        all_blocks: List[Dict], 
        start_idx: int, 
        std_id: str
    ) -> List[Dict]:
        """Gather blocks related to a standard"""
        
        related = []
        
        # Look backward for objectives
        for j in range(start_idx - 1, max(0, start_idx - 10), -1):
            text = all_blocks[j]['text']
            if text.startswith(std_id + '.'):
                related.insert(0, all_blocks[j])
            elif re.search(self.standard_id_pattern, text):
                break
        
        # Include the standard block
        related.append(all_blocks[start_idx])
        
        # Look forward for text and objectives
        for j in range(start_idx + 1, min(len(all_blocks), start_idx + 20)):
            text = all_blocks[j]['text']
            
            if re.search(self.standard_id_pattern, text) and not text.startswith(std_id):
                break
                
            related.append(all_blocks[j])
        
        return related
    
    def _build_standard_from_blocks(
        self, 
        std_id: str, 
        blocks: List[Dict]
    ) -> Optional[ParsedStandard]:
        """Build a standard from related blocks"""
        
        # Extract grade and strand
        parts = std_id.split('.')
        if len(parts) < 3:
            return None
            
        grade = parts[0]
        strand_code = parts[1]
        
        # Build text and objectives
        text_parts = []
        objectives = []
        
        for block in blocks:
            text = block['text']
            
            if re.match(self.objective_pattern, text):
                objectives.append(text)
            elif std_id in text:
                # Extract text after standard ID
                parts = text.split(std_id, 1)
                if len(parts) > 1:
                    text_parts.append(parts[1].strip())
            else:
                text_parts.append(text)
        
        standard_text = ' '.join(text_parts).strip()
        if not standard_text.startswith(std_id):
            standard_text = f"{std_id} {standard_text}"
        
        return ParsedStandard(
            grade_level=grade,
            strand_code=strand_code,
            strand_name=self.strand_mappings.get(strand_code, ("Unknown", ""))[0],
            strand_description=self.strand_mappings.get(strand_code, ("", "Unknown"))[1],
            standard_id=std_id,
            standard_text=standard_text,
            objectives=objectives,
            source_document="",
            page_number=blocks[0]['page'] if blocks else 0
        )
    
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
            "average_objectives_per_standard": sum(len(s.objectives) for s in self.parsed_standards) / len(self.parsed_standards) if self.parsed_standards else 0,
            "grade_distribution": grade_dist,
            "strand_distribution": strand_dist,
            "vision_enhanced": self.use_vision
        }