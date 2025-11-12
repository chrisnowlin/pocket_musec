#!/usr/bin/env python3
"""Test the malformed standards filter"""

from backend.ingestion.vision_extraction_helper import clean_malformed_standards


def test_filter():
    """Test that the filter removes malformed entries"""

    # Sample data mimicking what we found in Grade 8
    test_standards = [
        {"id": "8.CN.1", "text": "Standard text", "objectives": []},
        {"id": "8.CN.2", "text": "Standard text", "objectives": []},
        {"id": "8.PR.2", "text": "Standard text", "objectives": []},
        {
            "id": "8.PR.2.2",
            "text": "Should be filtered",
            "objectives": [],
        },  # Malformed!
        {"id": "8.RE.1", "text": "Standard text", "objectives": []},
        {"id": "RE.1", "text": "Missing grade prefix", "objectives": []},  # Malformed!
    ]

    print("Before filtering:")
    print(f"  Total: {len(test_standards)} standards")
    for s in test_standards:
        dots = s["id"].count(".")
        status = "✅ Valid" if dots == 2 else "❌ Malformed"
        print(f"  - {s['id']:12s} ({dots} dots) {status}")

    # Apply filter
    filtered = clean_malformed_standards(test_standards)

    print(f"\nAfter filtering:")
    print(f"  Total: {len(filtered)} standards")
    for s in filtered:
        print(f"  - {s['id']:12s} ✅")

    # Verify results
    filtered_ids = [s["id"] for s in filtered]

    assert "8.CN.1" in filtered_ids, "Should keep valid standard"
    assert "8.PR.2" in filtered_ids, "Should keep valid standard"
    assert "8.PR.2.2" not in filtered_ids, "Should remove objective (3 dots)"
    assert "RE.1" not in filtered_ids, "Should remove standard with 1 dot"

    print(f"\n✅ All tests passed!")
    print(f"   Removed: {len(test_standards) - len(filtered)} malformed entries")
    print(f"   Kept: {len(filtered)} valid standards")


if __name__ == "__main__":
    test_filter()
