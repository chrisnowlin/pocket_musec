#!/usr/bin/env python3
"""Detailed investigation: see what's actually in the extracted standards"""

import os
import json
from pathlib import Path
from backend.ingestion.vision_extraction_helper import (
    extract_standards_from_pdf_multipage,
)
from backend.llm.chutes_client import ChutesClient


def main():
    pdf_path = Path(
        "NC Music Standards and Resources/1 PAGE QUICK GUIDES GENERAL MUSIC - Google Docs.pdf"
    )

    # Initialize LLM client
    api_key = os.getenv("CHUTES_API_KEY")
    if not api_key:
        print("ERROR: CHUTES_API_KEY not set")
        return

    llm_client = ChutesClient(api_key=api_key)

    print("=" * 70)
    print("DETAILED INVESTIGATION - Grade 2 Pages 5-6")
    print("=" * 70)

    extracted = extract_standards_from_pdf_multipage(
        pdf_path=str(pdf_path),
        llm_client=llm_client,
        page_range=(4, 6),  # Pages 5-6 (0-indexed)
        grade_filter=None,
        dpi=300,
    )

    print(f"\nTotal standards extracted: {len(extracted)}\n")

    for i, std in enumerate(extracted[:5], 1):  # Show first 5
        print(f"\n{'=' * 70}")
        print(f"STANDARD #{i}")
        print(f"{'=' * 70}")
        print(json.dumps(std, indent=2))


if __name__ == "__main__":
    main()
