#!/usr/bin/env python3
"""Detailed vision test to see what's being missed"""

import sys
sys.path.insert(0, '/Users/cnowlin/Developer/pocket_musec')

from backend.llm.chutes_client import ChutesClient, Message
from pdf2image import convert_from_path
import base64
import io

pdf_path = "/Users/cnowlin/Developer/pocket_musec/NC Music Standards and Resources/1 PAGE QUICK GUIDES GENERAL MUSIC - Google Docs.pdf"

print("="*70)
print("DETAILED VISION EXTRACTION TEST")
print("="*70)

# Convert PDF
print("\nConverting PDF to image...")
images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=1)  # Higher DPI
image = images[0]
print(f"Image size: {image.size[0]}x{image.size[1]} pixels")

# Encode
buffered = io.BytesIO()
image.save(buffered, format="PNG", optimize=False)  # No optimization for quality
img_base64 = base64.b64encode(buffered.getvalue()).decode()
print(f"Base64 size: {len(img_base64) / 1024:.1f} KB")

# More detailed prompt
detailed_prompt = """Analyze this North Carolina Music Standards document page for KINDERGARTEN.

CRITICAL: Extract EVERY standard and objective visible on this page. Do not miss any!

Look for:
1. STANDARD IDs in format: K.CN.1, K.CN.2, K.CR.1, K.CR.2, K.PR.1, K.PR.2, K.RE.1, K.RE.2
2. OBJECTIVE IDs in format: K.CN.1.1, K.CN.1.2, K.PR.2.1, K.PR.2.2, etc.

For EACH standard you find, list:
- The standard ID (e.g., K.PR.2)
- The full standard text
- ALL objectives under that standard

Format your response like this:

**STANDARD: K.XX.#**
Text: [full standard text]
Objectives:
- K.XX.#.1: [objective text]
- K.XX.#.2: [objective text]

Be thorough - check all four strands: CONNECT (CN), CREATE (CR), PRESENT (PR), RESPOND (RE).
Each strand should have 2 standards, and each standard should have 2-4 objectives."""

message = Message(
    role="user",
    content=[
        {"type": "text", "text": detailed_prompt},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_base64}"}
        }
    ]
)

print("\nCalling vision API with detailed extraction prompt...")
client = ChutesClient()
response = client.chat_completion(
    messages=[message],
    model="Qwen/Qwen3-VL-235B-A22B-Instruct",
    temperature=0.0,  # Zero temperature for maximum accuracy
    max_tokens=4000   # More tokens for complete response
)

print("\n" + "="*70)
print("DETAILED EXTRACTION RESULTS")
print("="*70)
print(response.content)
print("\n" + "="*70)
print(f"Tokens used: {response.usage.get('total_tokens', 'N/A')}")
print("="*70)

# Parse and count what was found
lines = response.content.split('\n')
standard_count = len([l for l in lines if 'STANDARD:' in l or (l.startswith('K.') and any(x in l for x in ['.CN.', '.CR.', '.PR.', '.RE.']) and ':' in l)])
objective_count = len([l for l in lines if l.strip().startswith('- K.') or (l.strip().startswith('K.') and '.' in l.count('.') >= 3)])

print(f"\nExtraction Summary:")
print(f"  Standards found: ~{standard_count}")
print(f"  Objectives found: ~{objective_count}")
print(f"  Expected: 8 standards (2 per strand × 4 strands)")
print(f"  Expected: ~20-28 objectives (2-4 per standard)")
