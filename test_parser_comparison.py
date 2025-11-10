#!/usr/bin/env python3
"""Comprehensive test: Vision vs Hybrid parser comparison"""

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

def compare_parsers():
    """Compare vision vs hybrid parser results"""
    
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE PARSER COMPARISON")
    logger.info("=" * 80)
    
    # Force correct API endpoint
    os.environ['CHUTES_API_BASE_URL'] = 'https://llm.chutes.ai/v1'
    
    pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"
    
    if not Path(pdf_path).exists():
        logger.error(f"PDF not found: {pdf_path}")
        return False
    
    # Test hybrid parser first
    logger.info("\n🔄 Testing HYBRID parser...")
    hybrid_parser = HybridParser()
    hybrid_start = time.time()
    hybrid_standards = hybrid_parser.parse_standards_document(pdf_path)
    hybrid_time = time.time() - hybrid_start
    
    logger.info(f"✅ Hybrid parser completed in {hybrid_time:.1f}s")
    logger.info(f"   Standards: {len(hybrid_standards)}")
    
    hybrid_objectives = sum(len(std.objectives) for std in hybrid_standards)
    logger.info(f"   Objectives: {hybrid_objectives}")
    
    # Check for K.CN.1.1
    kcn_found_hybrid = False
    for std in hybrid_standards:
        if 'K.CN.1' in std.standard_id:
            for obj in std.objectives:
                if 'K.CN.1.1' in obj:
                    kcn_found_hybrid = True
                    logger.info(f"✅ K.CN.1.1 found in hybrid: {obj}")
                    break
    
    # Test vision parser
    logger.info("\n👁️ Testing VISION parser...")
    vision_parser = NCStandardsParser(force_fallback=False)
    
    # Force correct URL
    if vision_parser.llm_client.base_url != 'https://llm.chutes.ai/v1':
        vision_parser.llm_client.base_url = 'https://llm.chutes.ai/v1'
    
    vision_start = time.time()
    vision_standards = vision_parser.parse_standards_document(pdf_path)
    vision_time = time.time() - vision_start
    
    logger.info(f"✅ Vision parser completed in {vision_time:.1f}s")
    logger.info(f"   Standards: {len(vision_standards)}")
    
    vision_objectives = sum(len(std.objectives) for std in vision_standards)
    logger.info(f"   Objectives: {vision_objectives}")
    
    # Check for K.CN.1.1
    kcn_found_vision = False
    for std in vision_standards:
        if 'K.CN.1' in std.standard_id:
            for obj in std.objectives:
                if 'K.CN.1.1' in obj:
                    kcn_found_vision = True
                    logger.info(f"✅ K.CN.1.1 found in vision: {obj}")
                    break
    
    # Comparison
    logger.info("\n" + "=" * 80)
    logger.info("COMPARISON RESULTS")
    logger.info("=" * 80)
    
    logger.info(f"Hybrid Parser:")
    logger.info(f"  Standards: {len(hybrid_standards)}")
    logger.info(f"  Objectives: {hybrid_objectives}")
    logger.info(f"  Time: {hybrid_time:.1f}s")
    logger.info(f"  K.CN.1.1: {'✅' if kcn_found_hybrid else '❌'}")
    
    logger.info(f"\nVision Parser:")
    logger.info(f"  Standards: {len(vision_standards)}")
    logger.info(f"  Objectives: {vision_objectives}")
    logger.info(f"  Time: {vision_time:.1f}s")
    logger.info(f"  K.CN.1.1: {'✅' if kcn_found_vision else '❌'}")
    
    # Quality check
    logger.info(f"\nQuality Analysis:")
    if len(vision_standards) >= len(hybrid_standards):
        logger.info(f"✅ Vision extracted >= standards than hybrid")
    else:
        logger.info(f"⚠️ Vision extracted fewer standards than hybrid")
    
    if vision_objectives >= hybrid_objectives:
        logger.info(f"✅ Vision extracted >= objectives than hybrid")
    else:
        logger.info(f"⚠️ Vision extracted fewer objectives than hybrid")
    
    if kcn_found_vision and kcn_found_hybrid:
        logger.info(f"✅ Both parsers found K.CN.1.1")
    elif kcn_found_vision:
        logger.info(f"✅ Only vision parser found K.CN.1.1")
    elif kcn_found_hybrid:
        logger.info(f"⚠️ Only hybrid parser found K.CN.1.1")
    else:
        logger.info(f"❌ Neither parser found K.CN.1.1")
    
    # Recommendation
    logger.info(f"\n🎯 RECOMMENDATION:")
    if kcn_found_vision and len(vision_standards) >= 85:
        logger.info(f"✅ Use VISION-FIRST parser - excellent quality and coverage")
    else:
        logger.info(f"⚠️ Use HYBRID parser - more reliable for production")
    
    return True

if __name__ == "__main__":
    import time
    success = compare_parsers()
    
    if success:
        logger.info("\n🎉 Parser comparison completed successfully!")
    else:
        logger.info("\n❌ Parser comparison failed")