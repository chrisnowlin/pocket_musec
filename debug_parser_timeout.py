#!/usr/bin/env python3
"""Debug document processing timeout issues"""

import sys
import time
import signal
from pathlib import Path
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

from backend.ingestion.standards_parser import NCStandardsParser
from backend.ingestion.pdf_parser import PDFReader

def test_pdf_reading():
    """Test basic PDF reading"""
    logger.info("=" * 60)
    logger.info("Test 1: PDF Reading")
    logger.info("=" * 60)
    
    test_doc = 'NC Music Standards and Resources/Kindergarten GM Unpacking - Google Docs.pdf'
    
    try:
        start = time.time()
        reader = PDFReader()
        pages = reader.read_pdf(test_doc)
        elapsed = time.time() - start
        
        logger.info(f"✓ PDF reading successful in {elapsed:.2f}s")
        logger.info(f"  Pages: {len(pages)}")
        logger.info(f"  First page blocks: {len(pages[0].text_blocks)}")
        return True
    except Exception as e:
        logger.error(f"✗ PDF reading failed: {e}")
        return False

def test_parser_initialization():
    """Test parser initialization"""
    logger.info("\n" + "=" * 60)
    logger.info("Test 2: Parser Initialization")
    logger.info("=" * 60)
    
    try:
        start = time.time()
        parser = NCStandardsParser()
        elapsed = time.time() - start
        
        logger.info(f"✓ Parser initialized in {elapsed:.2f}s")
        logger.info(f"  Vision available: {parser.vision_available}")
        logger.info(f"  Has LLM client: {hasattr(parser, 'llm_client')}")
        
        if hasattr(parser, 'llm_client'):
            logger.info(f"  Base URL: {parser.llm_client.base_url}")
            logger.info(f"  Vision model: {parser.vision_model}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Parser initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_to_image_conversion():
    """Test PDF to image conversion (the likely bottleneck)"""
    logger.info("\n" + "=" * 60)
    logger.info("Test 3: PDF to Image Conversion")
    logger.info("=" * 60)
    
    try:
        from pdf2image import convert_from_path
        import tempfile
        
        test_doc = 'NC Music Standards and Resources/Kindergarten GM Unpacking - Google Docs.pdf'
        
        logger.info("Converting first 3 pages only...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            start = time.time()
            
            # Convert only first 3 pages to test
            images = convert_from_path(
                test_doc,
                dpi=150,
                first_page=2,  # Skip cover
                last_page=4,   # Only 3 pages
                output_folder=temp_dir
            )
            
            elapsed = time.time() - start
            
            logger.info(f"✓ Converted {len(images)} pages in {elapsed:.2f}s")
            logger.info(f"  Average: {elapsed/len(images):.2f}s per page")
            logger.info(f"  Image size: {images[0].size}")
            
            # Extrapolate for full document (48 pages)
            estimated_full = (elapsed / len(images)) * 46  # 48 pages minus 2
            logger.info(f"  Estimated full doc: {estimated_full:.1f}s ({estimated_full/60:.1f} minutes)")
            
            return True
            
    except ImportError:
        logger.error("✗ pdf2image not available")
        return False
    except Exception as e:
        logger.error(f"✗ PDF to image conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_single_page_vision():
    """Test vision processing on a single page"""
    logger.info("\n" + "=" * 60)
    logger.info("Test 4: Single Page Vision Processing")
    logger.info("=" * 60)
    
    try:
        from pdf2image import convert_from_path
        import tempfile
        
        test_doc = 'NC Music Standards and Resources/Kindergarten GM Unpacking - Google Docs.pdf'
        
        parser = NCStandardsParser()
        
        if not parser.vision_available:
            logger.warning("Vision not available, skipping")
            return False
        
        logger.info("Processing page 2 with vision...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert single page
            images = convert_from_path(
                test_doc,
                dpi=150,
                first_page=2,
                last_page=2,
                output_folder=temp_dir
            )
            
            start = time.time()
            results = parser._process_page_with_vision(images[0], 2)
            elapsed = time.time() - start
            
            logger.info(f"✓ Vision processing completed in {elapsed:.2f}s")
            logger.info(f"  Standards found: {len(results)}")
            
            if results:
                logger.info(f"  First standard: {results[0].standard_id}")
                logger.info(f"  Objectives: {len(results[0].objectives)}")
            
            # Extrapolate for full document
            estimated_full = elapsed * 46
            logger.info(f"  Estimated full doc: {estimated_full:.1f}s ({estimated_full/60:.1f} minutes)")
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Vision processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hybrid_parser():
    """Test hybrid parser as fallback"""
    logger.info("\n" + "=" * 60)
    logger.info("Test 5: Hybrid Parser (Fallback)")
    logger.info("=" * 60)
    
    try:
        test_doc = 'NC Music Standards and Resources/Kindergarten GM Unpacking - Google Docs.pdf'
        
        # Force fallback mode
        parser = NCStandardsParser(force_fallback=True)
        
        logger.info("Using hybrid parser...")
        start = time.time()
        
        # Set timeout for this test
        def timeout_handler(signum, frame):
            raise TimeoutError("Hybrid parser exceeded 30s timeout")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        standards = parser.parse_standards_document(test_doc)
        
        signal.alarm(0)  # Cancel timeout
        elapsed = time.time() - start
        
        logger.info(f"✓ Hybrid parser completed in {elapsed:.2f}s")
        logger.info(f"  Standards extracted: {len(standards)}")
        
        if standards:
            logger.info(f"  First standard: {standards[0].standard_id}")
            logger.info(f"  Grade level: {standards[0].grade_level}")
        
        return True
        
    except TimeoutError as e:
        signal.alarm(0)
        logger.error(f"✗ {e}")
        return False
    except Exception as e:
        signal.alarm(0)
        logger.error(f"✗ Hybrid parser failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Document Processing Timeout Debugger")
    logger.info("=" * 60)
    
    results = {}
    
    # Run tests in sequence
    results['pdf_reading'] = test_pdf_reading()
    results['parser_init'] = test_parser_initialization()
    results['pdf_to_image'] = test_pdf_to_image_conversion()
    results['single_vision'] = test_single_page_vision()
    results['hybrid_parser'] = test_hybrid_parser()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{test_name:20s}: {status}")
    
    # Recommendations
    logger.info("\n" + "=" * 60)
    logger.info("RECOMMENDATIONS")
    logger.info("=" * 60)
    
    if results.get('pdf_to_image') and results.get('single_vision'):
        logger.info("⚠️  Vision processing is very slow (~46 minutes per document)")
        logger.info("    Consider these optimizations:")
        logger.info("    1. Process fewer pages (skip cover/appendices)")
        logger.info("    2. Lower DPI (100 instead of 150)")
        logger.info("    3. Use hybrid parser by default")
        logger.info("    4. Add caching to avoid reprocessing")
    
    if results.get('hybrid_parser'):
        logger.info("✓  Hybrid parser is fast and should be the default")
        logger.info("    Vision can be optional for enhanced accuracy")
