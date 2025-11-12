#!/usr/bin/env python3
"""Test the existing VisionAnalyzer to see if it works"""

import sys
sys.path.insert(0, '/Users/cnowlin/Developer/pocket_musec')

from backend.image_processing.vision_analyzer import VisionAnalyzer
from pdf2image import convert_from_path
import tempfile

# Convert first page of PDF to image
pdf_path = "/Users/cnowlin/Developer/pocket_musec/NC Music Standards and Resources/1 PAGE QUICK GUIDES GENERAL MUSIC - Google Docs.pdf"
images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)

# Save as temp file
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
    images[0].save(f, format="PNG")
    temp_image = f.name
    print(f"Saved temp image: {temp_image}")

# Test VisionAnalyzer
analyzer = VisionAnalyzer()
print(f"API Key: {analyzer.api_key[:20]}...")
print(f"API Base URL: {analyzer.api_base_url}")

result = analyzer.analyze_image(
    temp_image,
    prompt="What educational content do you see on this page? List any standard IDs if visible."
)

if result:
    print(f"\n✓ VisionAnalyzer works!")
    print(f"Response: {result[:500]}...")
else:
    print(f"\n❌ VisionAnalyzer failed")

import os
os.unlink(temp_image)
