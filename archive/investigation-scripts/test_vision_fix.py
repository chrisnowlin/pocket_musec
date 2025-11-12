#!/usr/bin/env python3
"""Test script to verify Chutes Vision API PDF processing fix"""

import sys
import os
import base64
import io
from pathlib import Path

# Add project to path
sys.path.insert(0, '/Users/cnowlin/Developer/pocket_musec')

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("⚠️  pdf2image not available. Install with: pip install pdf2image")
    sys.exit(1)

from backend.llm.chutes_client import ChutesClient, Message
from backend.config import config

def test_vision_with_pdf(pdf_path: str, page_limit: int = 1):
    """
    Test vision API with a real PDF file
    
    Args:
        pdf_path: Path to PDF file
        page_limit: Number of pages to process (default 1 for quick test)
    """
    print(f"\n{'='*70}")
    print(f"Testing Chutes Vision API with PDF")
    print(f"{'='*70}\n")
    
    # Check API key
    if not config.chutes.api_key:
        print("❌ CHUTES_API_KEY not set. Please set it in .env file.")
        return False
    
    print(f"✓ API Key configured: {config.chutes.api_key[:20]}...")
    print(f"✓ API Base URL: {config.chutes.base_url}")
    
    # Check PDF exists
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    print(f"✓ PDF file found: {pdf_file.name} ({pdf_file.stat().st_size / 1024:.1f} KB)")
    
    # Convert PDF to images
    print(f"\n{'─'*70}")
    print(f"Step 1: Converting PDF to images (first {page_limit} page(s))...")
    print(f"{'─'*70}")
    
    try:
        images = convert_from_path(
            pdf_path,
            dpi=150,
            first_page=1,
            last_page=page_limit
        )
        print(f"✓ Converted {len(images)} page(s) to images")
    except Exception as e:
        print(f"❌ PDF conversion failed: {e}")
        return False
    
    # Process first page with vision model
    print(f"\n{'─'*70}")
    print(f"Step 2: Encoding image as base64...")
    print(f"{'─'*70}")
    
    image = images[0]
    try:
        # Convert to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG", optimize=True)
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        img_size_kb = len(img_base64) / 1024
        
        print(f"✓ Image encoded: {img_size_kb:.1f} KB base64")
        print(f"  Image size: {image.size[0]}x{image.size[1]} pixels")
    except Exception as e:
        print(f"❌ Image encoding failed: {e}")
        return False
    
    # Create multimodal message
    print(f"\n{'─'*70}")
    print(f"Step 3: Creating multimodal message...")
    print(f"{'─'*70}")
    
    vision_prompt = """Analyze this page from a music education standards document.

Please identify:
1. Any standard IDs (format: K.CN.1, 1.PR.2, etc.)
2. Any objective IDs (format: K.CN.1.1, 1.PR.2.3, etc.)
3. Brief description of what you see on the page

Be specific and extract exact text where possible."""

    try:
        message = Message(
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
        print(f"✓ Multimodal message created")
        print(f"  Content parts: {len(message.content)}")
        print(f"  - Part 1: text ({len(vision_prompt)} chars)")
        print(f"  - Part 2: image_url (base64)")
    except Exception as e:
        print(f"❌ Message creation failed: {e}")
        return False
    
    # Call vision API
    print(f"\n{'─'*70}")
    print(f"Step 4: Calling Chutes Vision API...")
    print(f"{'─'*70}")
    
    try:
        client = ChutesClient()
        print(f"  Model: Qwen/Qwen2-VL-7B-Instruct")
        print(f"  Sending request...")
        
        response = client.chat_completion(
            messages=[message],
            model="Qwen/Qwen2-VL-7B-Instruct",
            temperature=0.1,
            max_tokens=1000
        )
        
        print(f"✓ API call successful!")
        print(f"  Response length: {len(response.content)} chars")
        print(f"  Tokens used: {response.usage.get('total_tokens', 'N/A')}")
        
        print(f"\n{'─'*70}")
        print(f"Vision Model Response:")
        print(f"{'─'*70}")
        print(response.content)
        print(f"{'─'*70}")
        
        return True
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Use a small PDF for testing
    test_pdf = "/Users/cnowlin/Developer/pocket_musec/NC Music Standards and Resources/1 PAGE QUICK GUIDES GENERAL MUSIC - Google Docs.pdf"
    
    success = test_vision_with_pdf(test_pdf, page_limit=1)
    
    print(f"\n{'='*70}")
    if success:
        print("✅ TEST PASSED: Vision API is working correctly!")
    else:
        print("❌ TEST FAILED: Vision API encountered errors")
    print(f"{'='*70}\n")
    
    sys.exit(0 if success else 1)
