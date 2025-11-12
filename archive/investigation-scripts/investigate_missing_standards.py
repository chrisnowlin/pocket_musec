#!/usr/bin/env python3
"""
Quick investigation script to identify which specific standards are missing from Grade 2 and 8.
"""

import os
from pathlib import Path
from backend.ingestion.vision_extraction_helper import (
    extract_standards_from_pdf_multipage,
)
from backend.llm.chutes_client import ChutesClient


def investigate_missing():
    pdf_path = Path(
        "NC Music Standards and Resources/1 PAGE QUICK GUIDES GENERAL MUSIC - Google Docs.pdf"
    )

    # Initialize LLM client
    api_key = os.getenv("CHUTES_API_KEY")
    if not api_key:
        print("ERROR: CHUTES_API_KEY not set")
        return

    llm_client = ChutesClient(api_key=api_key)

    # Expected standards for each grade (8 per grade)
    expected_standards = {
        "2": [
            "2.CN.1",
            "2.CN.2",
            "2.CR.1",
            "2.CR.2",
            "2.PR.1",
            "2.PR.2",
            "2.RE.1",
            "2.RE.2",
        ],
        "8": [
            "8.CN.1",
            "8.CN.2",
            "8.CR.1",
            "8.CR.2",
            "8.PR.1",
            "8.PR.2",
            "8.RE.1",
            "8.RE.2",
        ],
    }

    print("=" * 70)
    print("INVESTIGATING MISSING STANDARDS")
    print("=" * 70)

    for grade, expected in expected_standards.items():
        print(f"\n{'=' * 70}")
        print(f"GRADE {grade} ANALYSIS")
        print(f"{'=' * 70}\n")

        # Determine page range based on grade
        if grade == "2":
            # Grade 2 is on pages 5-6 (1-indexed in PDF)
            start_page = 4  # 0-indexed
            end_page = 6
        else:  # grade == '8'
            # Grade 8 is approximately pages 15-16
            start_page = 14
            end_page = 16

        print(f"Extracting pages {start_page + 1}-{end_page} (1-indexed)...")

        # Extract with page range (note: page_range is a tuple)
        extracted = extract_standards_from_pdf_multipage(
            pdf_path=str(pdf_path),
            llm_client=llm_client,
            page_range=(start_page, end_page),
            grade_filter=grade,
            dpi=300,
        )

        # Analyze what we got
        found_standards = set()
        for standard in extracted:
            std_id = standard.get("standard_id", "")
            if std_id.startswith(f"{grade}."):
                found_standards.add(std_id)

        # Compare
        expected_set = set(expected)
        missing = expected_set - found_standards
        extra = found_standards - expected_set

        print(f"\nExpected: {len(expected_set)} standards")
        print(f"Found:    {len(found_standards)} standards")
        print(f"Missing:  {len(missing)} standards")

        if missing:
            print(f"\n⚠️  MISSING STANDARDS:")
            for std in sorted(missing):
                print(f"   - {std}")

        if extra:
            print(f"\n➕ EXTRA STANDARDS (shouldn't be here):")
            for std in sorted(extra):
                print(f"   - {std}")

        print(f"\n✅ FOUND STANDARDS:")
        for std in sorted(found_standards):
            # Find the standard details
            for s in extracted:
                if s.get("standard_id") == std:
                    obj_count = len(s.get("objectives", []))
                    print(f"   - {std}: {obj_count} objectives")
                    break

        # Try expanding the range if missing standards
        if missing:
            print(
                f"\n🔍 Trying expanded range (pages {start_page + 1}-{end_page + 2})..."
            )
            expanded = extract_standards_from_pdf_multipage(
                pdf_path=str(pdf_path),
                llm_client=llm_client,
                page_range=(start_page, end_page + 1),
                grade_filter=grade,
                dpi=300,
            )

            expanded_found = set()
            for standard in expanded:
                std_id = standard.get("standard_id", "")
                if std_id.startswith(f"{grade}."):
                    expanded_found.add(std_id)

            newly_found = expanded_found - found_standards
            if newly_found:
                print(f"   ✨ Found {len(newly_found)} additional standards:")
                for std in sorted(newly_found):
                    print(f"      - {std}")
            else:
                print(f"   ❌ No additional standards found")


if __name__ == "__main__":
    investigate_missing()
