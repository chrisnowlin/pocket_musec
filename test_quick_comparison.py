#!/usr/bin/env python3
"""Quick parser comparison on first 5 pages"""

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
from backend.ingestion.standards_parser_hybrid import NCStandardsParser as HybridParser

def quick_comparison():
    """Quick comparison on first 5 pages"""
    
    logger.info("=" * 60)
    logger.info("QUICK PARSER COMPARISON (First 5 Pages)")
    logger.info("=" * 60)
    
    # Force correct API endpoint
    os.environ['CHUTES_API_BASE_URL'] = 'https://llm.chutes.ai/v1'
    
    pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"
    
    # Test hybrid parser first
    logger.info("\n🔄 Testing HYBRID parser...")
    hybrid_parser = HybridParser()
    hybrid_standards = hybrid_parser.parse_standards_document(pdf_path)
    
    # Filter to first 5 pages worth
    hybrid_first_5 = [std for std in hybrid_standards if std.page_number <= 5]
    logger.info(f"✅ Hybrid: {len(hybrid_first_5)} standards from pages 1-5")
    
    hybrid_objectives = sum(len(std.objectives) for std in hybrid_first_5)
    logger.info(f"   Objectives: {hybrid_objectives}")
    
    # Check for K.CN.1.1
    kcn_found_hybrid = any('K.CN.1.1' in obj for std in hybrid_first_5 for obj in std.objectives)
    logger.info(f"   K.CN.1.1: {'✅' if kcn_found_hybrid else '❌'}")
    
    # Test vision parser (limited to first 5 pages)
    logger.info("\n👁️ Testing VISION parser...")
    vision_parser = NCStandardsParser(force_fallback=False)
    
    # Force correct URL
    if vision_parser.llm_client.base_url != 'https://llm.chutes.ai/v1':
        vision_parser.llm_client.base_url = 'https://llm.chutes.ai/v1'
    
    # Modify parser to only process first 5 pages
    original_process = vision_parser._process_page_with_vision
    
    def limited_process(*args, **kwargs):
        page_num = args[1] if len(args) > 1 else kwargs.get('page_number', 1)
        if page_num > 5:
            return []  # Skip pages beyond 5
        return original_process(*args, **kwargs)
    
    vision_parser._process_page_with_vision = limited_process
    
    vision_standards = vision_parser.parse_standards_document(pdf_path)
    vision_first_5 = [std for std in vision_standards if std.page_number <= 5]
    
    logger.info(f"✅ Vision: {len(vision_first_5)} standards from pages 1-5")
    
    vision_objectives = sum(len(std.objectives) for std in vision_first_5)
    logger.info(f"   Objectives: {vision_objectives}")
    
    # Check for K.CN.1.1
    kcn_found_vision = any('K.CN.1.1' in obj for std in vision_first_5 for obj in std.objectives)
    logger.info(f"   K.CN.1.1: {'✅' if kcn_found_vision else '❌'}")
    
    # Comparison
    logger.info("\n" + "=" * 60)
    logger.info("RESULTS (First 5 Pages)")
    logger.info("=" * 60)
    
    logger.info(f"Hybrid:  {len(hybrid_first_5):3d} standards, {hybrid_objectives:3d} objectives, K.CN.1.1: {'✅' if kcn_found_hybrid else '❌'}")
    logger.info(f"Vision:  {len(vision_first_5):3d} standards, {vision_objectives:3d} objectives, K.CN.1.1: {'✅' if kcn_found_vision else '❌'}")
    
    # Quality assessment
    if kcn_found_vision and len(vision_first_5) >= len(hybrid_first_5):
        logger.info(f"\n🎯 VISION PARSER READY FOR PRODUCTION!")
        logger.info(f"   ✅ Equal or better coverage")
        logger.info(f"   ✅ Successfully extracts K.CN.1.1")
        logger.info(f"   ✅ Vision-first architecture working")
    else:
        logger.info(f"\n⚠️ Use HYBRID parser for now")
        logger.info(f"   Vision needs optimization")
    
    return True

if __name__ == "__main__":
    success = quick_comparison()
    
    if success:
        logger.info("\n🎉 Quick comparison completed!")
    else:
        logger.info("\n❌ Quick comparison failed")