#!/usr/bin/env python3
"""Test the vision-first parser with Chutes Qwen VL"""

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

def test_vision_parser():
    """Test the vision-first parser on NC Music Standards"""
    
    # Initialize parser
    logger.info("Initializing vision-first parser...")
    parser = NCStandardsParser(force_fallback=False)
    
    # Parse the PDF
    pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"
    logger.info(f"Parsing PDF: {pdf_path}")
    
    try:
        standards = parser.parse_standards_document(pdf_path)
        
        logger.info(f"Successfully parsed {len(standards)} standards")
        
        # Count objectives
        total_objectives = sum(len(s.objectives) for s in standards)
        logger.info(f"Total objectives extracted: {total_objectives}")
        
        # Check grade distribution
        grades = set(s.grade_level for s in standards)
        logger.info(f"Grade levels found: {sorted(grades)}")
        
        # Check for K.CN.1.1
        k_standards = [s for s in standards if s.grade_level == "K"]
        logger.info(f"Kindergarten standards: {len(k_standards)}")
        
        for std in k_standards:
            if "CN" in std.standard_id:
                logger.info(f"Found K.CN standard: {std.standard_id}")
                logger.info(f"  Text: {std.standard_text[:100]}...")
                logger.info(f"  Objectives: {std.objectives}")
                break
        
        # Sample first few standards
        logger.info("\nFirst 3 standards:")
        for i, std in enumerate(standards[:3]):
            logger.info(f"\n{i+1}. {std.standard_id} ({std.grade_level})")
            logger.info(f"   Text: {std.standard_text[:100]}...")
            logger.info(f"   Objectives: {len(std.objectives)}")
            if std.objectives:
                logger.info(f"   First objective: {std.objectives[0]}")
        
        return standards
        
    except Exception as e:
        logger.error(f"Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_vision_availability():
    """Test if vision processing is available"""
    logger.info("Testing vision processing availability...")
    
    parser = NCStandardsParser(force_fallback=False)
    
    if parser.vision_available:
        logger.info("✓ Vision processing is available")
        logger.info(f"✓ Chutes client available: {parser.llm_client is not None}")
    else:
        logger.warning("✗ Vision processing is NOT available")
        logger.warning(f"  Force fallback: {parser.force_fallback}")
        logger.warning(f"  Chutes client available: {parser.llm_client is not None}")

if __name__ == "__main__":
    # First test vision availability
    logger.info("=" * 60)
    logger.info("Testing Vision Processing Availability")
    logger.info("=" * 60)
    test_vision_availability()
    
    logger.info("\n" + "=" * 60)
    logger.info("Testing Full Vision-First Parser")
    logger.info("=" * 60)
    
    # Then test full parser
    standards = test_vision_parser()
    
    if standards:
        logger.info("\n" + "=" * 60)
        logger.info("Vision-first parser test completed successfully!")
        logger.info(f"Final count: {len(standards)} standards")
    else:
        logger.info("\nVision-first parser test failed - check logs above")