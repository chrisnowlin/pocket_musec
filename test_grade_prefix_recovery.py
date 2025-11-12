#!/usr/bin/env python3
"""Test the intelligent grade prefix recovery"""

from backend.ingestion.vision_extraction_helper import recover_missing_grade_prefixes


def test_recovery():
    """Test that grade prefixes are recovered from context"""

    # Mock data simulating what we get from Grade 8
    test_standards = [
        {"id": "8.CN.1", "page": 17, "text": "Standard text", "objectives": []},
        {"id": "8.CN.2", "page": 17, "text": "Standard text", "objectives": []},
        {"id": "8.PR.2", "page": 17, "text": "Standard text", "objectives": []},
        {
            "id": "RE.1",
            "page": 18,
            "text": "Missing grade",
            "objectives": [],
        },  # Should become 8.RE.1
        {
            "id": "RE.2",
            "page": 18,
            "text": "Missing grade",
            "objectives": [],
        },  # Should become 8.RE.2
        {
            "id": "8.PR.1",
            "page": 18,
            "text": "Has context",
            "objectives": [],
        },  # Context for page 18
    ]

    print("Before recovery:")
    for s in test_standards:
        dots = s["id"].count(".")
        status = "✅ Valid" if dots == 2 else "❌ Missing prefix"
        print(f"  {s['id']:12s} (page {s.get('page', '?')}) {status}")

    # Apply recovery
    recovered = recover_missing_grade_prefixes(test_standards)

    print(f"\nAfter recovery:")
    for s in recovered:
        dots = s["id"].count(".")
        status = "✅" if dots == 2 else "❌"
        print(f"  {s['id']:12s} (page {s.get('page', '?')}) {status}")

    # Verify
    ids = [s["id"] for s in recovered]
    assert "8.RE.1" in ids, "Should have recovered 8.RE.1"
    assert "8.RE.2" in ids, "Should have recovered 8.RE.2"
    assert "RE.1" not in ids, "Should not have bare RE.1 anymore"
    assert "RE.2" not in ids, "Should not have bare RE.2 anymore"

    print(f"\n✅ All tests passed!")
    print(f"   Successfully recovered grade prefixes from context")


if __name__ == "__main__":
    test_recovery()
