#!/usr/bin/env python3
"""Simple investigation: extract without filter and see everything"""

import os
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
    print("INVESTIGATING - EXTRACTING WITHOUT FILTER")
    print("=" * 70)

    # Grade 2: Pages 5-6
    print("\nGRADE 2: Pages 5-6")
    print("-" * 70)
    extracted_2 = extract_standards_from_pdf_multipage(
        pdf_path=str(pdf_path),
        llm_client=llm_client,
        page_range=(4, 6),  # 0-indexed
        grade_filter=None,  # No filter
        dpi=300,
    )

    print(f"Total standards extracted: {len(extracted_2)}")
    for std in extracted_2:
        std_id = std.get("standard_id", "NO_ID")
        obj_count = len(std.get("objectives", []))
        print(f"  - {std_id}: {obj_count} objectives")

    # Grade 8: Pages 15-16
    print("\n" + "=" * 70)
    print("GRADE 8: Pages 15-16")
    print("-" * 70)
    extracted_8 = extract_standards_from_pdf_multipage(
        pdf_path=str(pdf_path),
        llm_client=llm_client,
        page_range=(14, 16),  # 0-indexed
        grade_filter=None,  # No filter
        dpi=300,
    )

    print(f"Total standards extracted: {len(extracted_8)}")
    for std in extracted_8:
        std_id = std.get("standard_id", "NO_ID")
        obj_count = len(std.get("objectives", []))
        print(f"  - {std_id}: {obj_count} objectives")


if __name__ == "__main__":
    main()
