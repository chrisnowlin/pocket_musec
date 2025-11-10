#!/usr/bin/env python3
"""Final production test of the NC Music Standards parser"""

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

def test_production_parser():
    """Test the production parser with vision-first + hybrid fallback"""
    
    logger.info("=" * 60)
    logger.info("PRODUCTION PARSER FINAL TEST")
    logger.info("=" * 60)
    
    # Initialize parser (will try vision first, fall back to hybrid)
    logger.info("Initializing production parser...")
    parser = NCStandardsParser(force_fallback=False)
    
    logger.info(f"Vision available: {parser.vision_available}")
    logger.info(f"Force fallback: {parser.force_fallback}")
    
    # Parse the PDF
    pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"
    logger.info(f"Parsing PDF: {pdf_path}")
    
    try:
        start_time = time.time()
        standards = parser.parse_standards_document(pdf_path)
        elapsed_time = time.time() - start_time
        
        logger.info(f"✓ Parsing completed in {elapsed_time:.2f} seconds")
        logger.info(f"✓ Extracted {len(standards)} standards")
        
        # Validate extraction
        total_objectives = sum(len(s.objectives) for s in standards)
        logger.info(f"✓ Extracted {total_objectives} objectives")
        
        grades = set(s.grade_level for s in standards)
        expected_grades = {'K', '1', '2', '3', '4', '5', '6', '7', '8', 'AC', 'AD'}
        
        if grades == expected_grades:
            logger.info(f"✓ All grade levels present: {sorted(grades)}")
        else:
            logger.warning(f"Grade mismatch. Expected: {expected_grades}, Got: {grades}")
        
        # Check for K.CN.1.1 specifically
        k_standards = [s for s in standards if s.grade_level == "K"]
        k_cn_standards = [s for s in k_standards if "CN" in s.standard_id]
        
        if k_cn_standards:
            k_cn = k_cn_standards[0]
            logger.info(f"✓ Found K.CN standard: {k_cn.standard_id}")
            logger.info(f"  Text: {k_cn.standard_text[:100]}...")
            
            # Check for K.CN.1.1 objective
            kcn11_objectives = [obj for obj in k_cn.objectives if "K.CN.1.1" in obj]
            if kcn11_objectives:
                logger.info(f"✓ K.CN.1.1 found: {kcn11_objectives[0]}")
            else:
                logger.warning("K.CN.1.1 objective not found")
        else:
            logger.error("K.CN standard not found")
        
        # Validate strand distribution
        strands = set(s.strand_code for s in standards)
        expected_strands = {'CN', 'CR', 'PR', 'RE'}
        
        if strands == expected_strands:
            logger.info(f"✓ All strands present: {sorted(strands)}")
        else:
            logger.warning(f"Strand mismatch. Expected: {expected_strands}, Got: {strands}")
        
        # Sample validation
        logger.info("\nSample standards:")
        for i, std in enumerate(standards[:3]):
            logger.info(f"  {i+1}. {std.standard_id} ({std.grade_level}.{std.strand_code}) - {len(std.objectives)} objectives")
        
        # Final validation
        success = (
            len(standards) == 88 and
            total_objectives == 193 and
            grades == expected_grades and
            strands == expected_strands and
            len(k_cn_standards) > 0
        )
        
        if success:
            logger.info("\n" + "=" * 60)
            logger.info("🎉 PRODUCTION PARSER TEST: PASSED")
            logger.info("✅ Ready for production deployment")
            logger.info("=" * 60)
        else:
            logger.error("\n" + "=" * 60)
            logger.info("❌ PRODUCTION PARSER TEST: FAILED")
            logger.info("⚠️  Review validation results above")
            logger.info("=" * 60)
        
        return success, standards
        
    except Exception as e:
        logger.error(f"Error during production test: {e}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    import time
    
    success, standards = test_production_parser()
    
    if success and standards:
        # Save results for verification
        results = {
            "timestamp": time.time(),
            "total_standards": len(standards),
            "total_objectives": sum(len(s.objectives) for s in standards),
            "grades": sorted(set(s.grade_level for s in standards)),
            "strands": sorted(set(s.strand_code for s in standards)),
            "parsing_successful": True
        }
        
        with open("production_test_results.json", "w") as f:
            import json
            json.dump(results, f, indent=2)
        
        logger.info("Results saved to production_test_results.json")