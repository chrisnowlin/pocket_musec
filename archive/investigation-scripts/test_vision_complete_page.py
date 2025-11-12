#!/usr/bin/env python3
"""Test complete extraction from a single page - checking for K.RE standards"""

import sys
sys.path.insert(0, '/Users/cnowlin/Developer/pocket_musec')

from backend.llm.chutes_client import ChutesClient, Message
from pdf2image import convert_from_path
import base64
import io

pdf_path = "/Users/cnowlin/Developer/pocket_musec/NC Music Standards and Resources/1 PAGE QUICK GUIDES GENERAL MUSIC - Google Docs.pdf"

print("="*70)
print("COMPLETE PAGE EXTRACTION - Looking for Missing K.RE Standards")
print("="*70)

# Convert with very high DPI for best quality
images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=1)
image = images[0]

# Encode
buffered = io.BytesIO()
image.save(buffered, format="PNG")
img_base64 = base64.b64encode(buffered.getvalue()).decode()

# Specific prompt focusing on K.RE
prompt = """This is page 1 of a Kindergarten music standards document.

I need you to extract EVERYTHING visible on this page, especially focusing on the RESPOND (RE) strand at the bottom.

Please list:
1. ALL standard IDs you can see (K.CN.1, K.CN.2, K.CR.1, K.CR.2, K.PR.1, K.PR.2, K.RE.1, K.RE.2)
2. For EACH standard, list ALL objectives visible (even if partially visible)

Pay special attention to:
- K.RE.1 - Is this standard visible? What objectives?
- K.RE.2 - Is this standard visible? What objectives?

If any text is cut off at the bottom, mention that explicitly.

Format:
**K.XX.#** - [Standard text if visible, or "NOT VISIBLE" or "PARTIALLY VISIBLE"]
  - K.XX.#.1: [objective text or "CUT OFF"]
  - K.XX.#.2: [objective text or "CUT OFF"]
"""

message = Message(
    role="user",
    content=[
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
    ]
)

print("\nCalling vision API...")
client = ChutesClient()
response = client.chat_completion(
    messages=[message],
    model="Qwen/Qwen3-VL-235B-A22B-Instruct",
    temperature=0.0,
    max_tokens=4000
)

print("\n" + "="*70)
print("COMPLETE EXTRACTION")
print("="*70)
print(response.content)

# Summary
print("\n" + "="*70)
print("ANALYSIS")
print("="*70)

found_standards = []
missing_objectives = []

for line in response.content.split('\n'):
    if line.strip().startswith('**K.'):
        std_id = line.split('**')[1].split()[0]
        found_standards.append(std_id)
        if 'NOT VISIBLE' in line or 'PARTIALLY VISIBLE' in line or 'CUT OFF' in line:
            missing_objectives.append(std_id)

print(f"Standards found: {', '.join(found_standards)}")
print(f"Standards with missing/cut off content: {', '.join(missing_objectives) if missing_objectives else 'None'}")

# Check specifically for K.RE
if 'K.RE.1' not in found_standards:
    print("\n⚠️  K.RE.1 NOT FOUND on page")
if 'K.RE.2' not in found_standards:
    print("⚠️  K.RE.2 NOT FOUND on page")

if any('K.RE' in s for s in found_standards):
    print("\n✓ K.RE standards are present on the page")
    if any('K.RE' in s for s in missing_objectives):
        print("⚠️  But some K.RE content is cut off or not fully visible")
