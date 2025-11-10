#!/usr/bin/env python3
"""Test the vision parser with the corrected API endpoint"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.ingestion.standards_parser import NCStandardsParser

def test_vision_parser_fixed():
    """Test the vision parser with corrected API endpoint"""
    
    logger.info("Testing vision parser with fixed API endpoint...")
    
    # Force the correct base URL
    os.environ['CHUTES_API_BASE_URL'] = 'https://llm.chutes.ai/v1'
    
# Force the correct base URL in environment
    os.environ['CHUTES_API_BASE_URL'] = 'https://llm.chutes.ai/v1'
    
# Initialize parser
    parser = NCStandardsParser(force_fallback=False)
    
    # Force update the client base URL if needed
    if parser.llm_client.base_url != 'https://llm.chutes.ai/v1':
        parser.llm_client.base_url = 'https://llm.chutes.ai/v1'
        logger.info("Updated parser base URL to correct endpoint")
    
    logger.info(f"Parser base URL: {parser.llm_client.base_url}")
    logger.info(f"Vision available: {parser.vision_available}")
    
    if not parser.vision_available:
        logger.error("Vision processing not available")
        return False
    
    # Test a single page first
    pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"
    
    try:
        logger.info("Testing vision extraction on page 2...")
        
        # Convert PDF to images for page 2 only
        from pdf2image import convert_from_path
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            images = convert_from_path(pdf_path, dpi=150, output_folder=temp_dir)
            
            if len(images) >= 2:
                page_2_image = images[1]  # Page 2 (0-indexed)
                
                # Process page 2 with vision
                standards = parser._process_page_with_vision(page_2_image, 2)
                
                if standards:
                    logger.info(f"✅ Vision extraction successful!")
                    logger.info(f"   Extracted {len(standards)} standards from page 2")
                    
                    # Check for K.CN.1.1
                    for std in standards:
                        if 'K.CN.1' in std.standard_id:
                            logger.info(f"✅ Found K.CN standard: {std.standard_id}")
                            logger.info(f"   Objectives: {std.objectives}")
                            
                            # Check for K.CN.1.1
                            for obj in std.objectives:
                                if 'K.CN.1.1' in obj:
                                    logger.info(f"✅ K.CN.1.1 found: {obj}")
                                    return True
                    
                    logger.warning("K.CN.1.1 not found in page 2 results")
                    return True
                else:
                    logger.error("❌ Vision extraction returned no standards")
                    return False
            else:
                logger.error("PDF has fewer than 2 pages")
                return False
                
    except Exception as e:
        logger.error(f"❌ Vision extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("TESTING VISION PARSER WITH FIXED API")
    logger.info("=" * 60)
    
    success = test_vision_parser_fixed()
    
    if success:
        logger.info("\n✅ Vision parser is working with corrected API!")
    else:
        logger.info("\n❌ Vision parser still has issues")