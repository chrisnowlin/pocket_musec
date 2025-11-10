#!/usr/bin/env python3

import pdfplumber
from pathlib import Path

# Test PDF reading
pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"

if not Path(pdf_path).exists():
    print(f"PDF not found: {pdf_path}")
    exit(1)

try:
    with pdfplumber.open(pdf_path) as pdf:
        print(f"PDF has {len(pdf.pages)} pages")
        
        # Check first few pages
        for i, page in enumerate(pdf.pages[:3]):
            text = page.extract_text()
            print(f"\n--- Page {i+1} ---")
            print(f"Text length: {len(text) if text else 0}")
            if text:
                print(text[:500] + "..." if len(text) > 500 else text)
            else:
                print("No text extracted")
                
except Exception as e:
    print(f"Error reading PDF: {e}")