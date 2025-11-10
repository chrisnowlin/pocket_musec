#!/usr/bin/env python3
"""Test the hybrid fallback parser"""

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

def test_fallback_parser():
    """Test the hybrid fallback parser"""
    
    # Initialize parser with forced fallback
    logger.info("Initializing parser with forced fallback...")
    parser = NCStandardsParser(force_fallback=True)
    
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
        
        found_kcn = False
        for std in k_standards:
            if "CN" in std.standard_id:
                logger.info(f"Found K.CN standard: {std.standard_id}")
                logger.info(f"  Text: {std.standard_text[:100]}...")
                logger.info(f"  Objectives: {std.objectives}")
                found_kcn = True
                break
        
        if not found_kcn:
            logger.warning("K.CN standard not found!")
        
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

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Testing Hybrid Fallback Parser")
    logger.info("=" * 60)
    
    standards = test_fallback_parser()
    
    if standards:
        logger.info("\n" + "=" * 60)
        logger.info("Hybrid fallback parser test completed successfully!")
        logger.info(f"Final count: {len(standards)} standards")
    else:
        logger.info("\nHybrid fallback parser test failed - check logs above")