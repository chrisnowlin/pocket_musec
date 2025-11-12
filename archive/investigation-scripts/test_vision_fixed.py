#!/usr/bin/env python3
"""Test Chutes Vision API with the correct model name"""

import sys
sys.path.insert(0, '/Users/cnowlin/Developer/pocket_musec')

from backend.llm.chutes_client import ChutesClient, Message
from pdf2image import convert_from_path
import base64
import io

pdf_path = "/Users/cnowlin/Developer/pocket_musec/NC Music Standards and Resources/1 PAGE QUICK GUIDES GENERAL MUSIC - Google Docs.pdf"

print("Converting PDF to image...")
images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)

print("Encoding image...")
buffered = io.BytesIO()
images[0].save(buffered, format="PNG", optimize=True)
img_base64 = base64.b64encode(buffered.getvalue()).decode()

print(f"Image encoded: {len(img_base64) / 1024:.1f} KB")

# Create multimodal message
message = Message(
    role="user",
    content=[
        {
            "type": "text",
            "text": "What do you see on this page? List any standard IDs."
        },
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_base64}"}
        }
    ]
)

print("Calling Chutes API...")
client = ChutesClient()

# Use the same model that works in VisionAnalyzer
response = client.chat_completion(
    messages=[message],
    model="Qwen/Qwen3-VL-235B-A22B-Instruct",  # Same as VisionAnalyzer
    temperature=0.3,
    max_tokens=1000
)

print(f"\n✓ Success!")
print(f"Response: {response.content[:500]}...")
print(f"Tokens: {response.usage.get('total_tokens', 'N/A')}")
