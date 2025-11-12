#!/usr/bin/env python3
"""Multi-page vision extraction to get complete standards"""

import sys
sys.path.insert(0, '/Users/cnowlin/Developer/pocket_musec')

from backend.llm.chutes_client import ChutesClient, Message
from pdf2image import convert_from_path
import base64
import io
import re

pdf_path = "/Users/cnowlin/Developer/pocket_musec/NC Music Standards and Resources/1 PAGE QUICK GUIDES GENERAL MUSIC - Google Docs.pdf"

def extract_from_page(image, page_num):
    """Extract standards from a single page"""
    # Encode
    buffered = io.BytesIO()
    image.save(buffered, format="PNG", optimize=True)
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    prompt = f"""Extract ALL music education standards and objectives from this page.

Look for standard IDs like: K.CN.1, K.CN.2, K.CR.1, K.CR.2, K.PR.1, K.PR.2, K.RE.1, K.RE.2
Or other grades: 1.CN.1, 2.PR.2, 3.RE.1, etc.

For EACH standard found, provide:
- Standard ID
- Full standard text
- ALL objectives with full text

Format as JSON:
{{
  "standards": [
    {{
      "id": "K.CN.1",
      "text": "Relate musical ideas...",
      "objectives": [
        {{"id": "K.CN.1.1", "text": "Identify the similarities..."}},
        {{"id": "K.CN.1.2", "text": "Identify how music..."}}
      ]
    }}
  ]
}}

If content is cut off, note it in the text field."""
    
    message = Message(
        role="user",
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
        ]
    )
    
    client = ChutesClient()
    response = client.chat_completion(
        messages=[message],
        model="Qwen/Qwen3-VL-235B-A22B-Instruct",
        temperature=0.0,
        max_tokens=4000
    )
    
    return response.content

print("="*70)
print("MULTI-PAGE EXTRACTION TEST - Kindergarten Standards")
print("="*70)

# Process first 2 pages to capture K.RE standards
images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=2)

all_standards = {}

for page_num, image in enumerate(images, 1):
    print(f"\nProcessing page {page_num}...")
    result = extract_from_page(image, page_num)
    
    print(f"\n{'─'*70}")
    print(f"PAGE {page_num} RESULTS:")
    print(f"{'─'*70}")
    
    # Extract standard IDs from result
    std_ids = re.findall(r'[K123456789]\.(?:CN|CR|PR|RE)\.\d+', result)
    std_ids_unique = list(dict.fromkeys(std_ids))  # Remove duplicates, preserve order
    
    print(f"Standards found: {', '.join(std_ids_unique) if std_ids_unique else 'None'}")
    print(f"\nRaw output:\n{result[:800]}...")
    
    # Store for merging
    for std_id in std_ids_unique:
        if std_id not in all_standards:
            all_standards[std_id] = {
                'pages': [page_num],
                'content': result
            }
        else:
            all_standards[std_id]['pages'].append(page_num)

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"Total unique standards found: {len(all_standards)}")
print(f"Standard IDs: {', '.join(sorted(all_standards.keys()))}")

# Check for Kindergarten completeness
k_standards = [s for s in all_standards.keys() if s.startswith('K.')]
expected_k = ['K.CN.1', 'K.CN.2', 'K.CR.1', 'K.CR.2', 'K.PR.1', 'K.PR.2', 'K.RE.1', 'K.RE.2']
missing_k = [s for s in expected_k if s not in k_standards]

print(f"\nKindergarten standards found: {len(k_standards)}/8")
if missing_k:
    print(f"⚠️  Missing: {', '.join(missing_k)}")
else:
    print(f"✓ All 8 Kindergarten standards captured!")

# Specifically check K.PR.2 and K.RE standards
if 'K.PR.2' in k_standards:
    print(f"\n✓ K.PR.2 found on page(s): {all_standards['K.PR.2']['pages']}")
if 'K.RE.1' in k_standards:
    print(f"✓ K.RE.1 found on page(s): {all_standards['K.RE.1']['pages']}")
if 'K.RE.2' in k_standards:
    print(f"✓ K.RE.2 found on page(s): {all_standards['K.RE.2']['pages']}")
