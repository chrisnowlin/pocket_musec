"""PDF parsing utilities for standards ingestion"""

import pdfplumber
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """Represents a block of text with position information"""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page_number: int
    font_size: Optional[float] = None
    font_name: Optional[str] = None


@dataclass
class ParsedPage:
    """Represents a parsed page with text blocks"""
    page_number: int
    width: float
    height: float
    text_blocks: List[TextBlock]
    raw_text: str


class PDFReader:
    """PDF reader using pdfplumber for text extraction"""
    
    def __init__(self):
        self.pages: List[ParsedPage] = []
    
    def read_pdf(self, pdf_path: str) -> List[ParsedPage]:
        """Read a PDF file and extract text with position data"""
        pdf_path_obj = Path(pdf_path)
        if not pdf_path_obj.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self.pages.clear()
        
        try:
            with pdfplumber.open(pdf_path_obj) as pdf:
                logger.info(f"Reading PDF with {len(pdf.pages)} pages: {pdf_path}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    parsed_page = self._parse_page(page, page_num)
                    self.pages.append(parsed_page)
                    logger.debug(f"Parsed page {page_num}: {len(parsed_page.text_blocks)} text blocks")
        
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
            raise
        
        logger.info(f"Successfully parsed {len(self.pages)} pages")
        return self.pages
    
    def _parse_page(self, page, page_number: int) -> ParsedPage:
        """Parse a single page and extract text blocks"""
        text_blocks = []
        
        # Extract words and group them into lines
        words = page.extract_words(extra_attrs=["fontname", "size"])
        
        # Group words by line (similar y-coordinate)
        lines = {}
        for word in words:
            y = round(word["top"], 1)  # Round to group nearby words
            if y not in lines:
                lines[y] = []
            lines[y].append(word)
        
        # Sort lines by y-coordinate (top to bottom)
        for y in sorted(lines.keys()):
            line_words = lines[y]
            # Sort words by x-coordinate (left to right)
            line_words.sort(key=lambda w: w["x0"])
            
            # Join words to form line text
            line_text = " ".join(w["text"] for w in line_words)
            
            # Calculate line boundaries
            x0 = min(w["x0"] for w in line_words)
            x1 = max(w["x1"] for w in line_words)
            y0 = min(w["top"] for w in line_words)
            y1 = max(w["bottom"] for w in line_words)
            
            # Use font info from first word
            first_word = line_words[0]
            
            text_block = TextBlock(
                text=line_text,
                x0=x0,
                y0=y0,
                x1=x1,
                y1=y1,
                page_number=page_number,
                font_size=first_word.get("size"),
                font_name=first_word.get("fontname")
            )
            text_blocks.append(text_block)
        
        # Get raw text for fallback
        raw_text = page.extract_text() or ""
        
        return ParsedPage(
            page_number=page_number,
            width=page.width,
            height=page.height,
            text_blocks=text_blocks,
            raw_text=raw_text
        )
    
    def get_text_by_region(self, page_number: int, x0: float, y0: float, 
                          x1: float, y1: float) -> List[TextBlock]:
        """Get text blocks within a specific region"""
        if page_number < 1 or page_number > len(self.pages):
            return []
        
        page = self.pages[page_number - 1]
        region_blocks = []
        
        for block in page.text_blocks:
            # Check if block intersects with region
            if (block.x0 >= x0 and block.y0 >= y0 and 
                block.x1 <= x1 and block.y1 <= y1):
                region_blocks.append(block)
        
        # Sort by reading order (top to bottom, left to right)
        region_blocks.sort(key=lambda b: (b.y0, b.x0))
        return region_blocks
    
    def get_columns(self, page_number: int, num_columns: int = 2) -> List[List[TextBlock]]:
        """Divide page into columns and return text blocks for each"""
        if page_number < 1 or page_number > len(self.pages):
            return []
        
        page = self.pages[page_number - 1]
        column_width = page.width / num_columns
        columns = []
        
        for i in range(num_columns):
            x0 = i * column_width
            x1 = (i + 1) * column_width
            column_blocks = self.get_text_by_region(page_number, x0, 0, x1, page.height)
            columns.append(column_blocks)
        
        return columns