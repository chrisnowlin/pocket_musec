#!/usr/bin/env python3
"""
Quick edge case test to verify basic functionality
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def quick_test():
    """Quick test of key edge cases"""

    # Test 1: Single objective
    print("Test 1: Single objective")
    session_data = {
        "grade_level": "Grade 4",
        "strand_code": "CREATE",
        "standard_id": "4.CR.1",
        "selected_objectives": "4.CR.1.1",
    }

    response = requests.post(f"{BASE_URL}/sessions", json=session_data)
    if response.status_code != 200:
        print(f"❌ Failed: {response.text}")
        return False

    session = response.json()
    print(f"✓ Session created: {session['selected_objectives']}")

    # Test 2: Empty objectives
    print("\nTest 2: Empty objectives")
    session_data2 = {
        "grade_level": "Grade 2",
        "strand_code": "RESPOND",
        "standard_id": "2.RE.1",
        "selected_objectives": "",
    }

    response2 = requests.post(f"{BASE_URL}/sessions", json=session_data2)
    if response2.status_code != 200:
        print(f"❌ Failed: {response2.text}")
        return False

    session2 = response2.json()
    print(f"✓ Session created with empty: '{session2['selected_objectives']}'")

    # Test 3: No objectives
    print("\nTest 3: No objectives")
    session_data3 = {
        "grade_level": "Grade 1",
        "strand_code": "CONNECT",
        "standard_id": "1.CN.1",
    }

    response3 = requests.post(f"{BASE_URL}/sessions", json=session_data3)
    if response3.status_code != 200:
        print(f"❌ Failed: {response3.text}")
        return False

    session3 = response3.json()
    print(
        f"✓ Session created without objectives: {session3.get('selected_objectives', 'None')}"
    )

    print("\n✅ All basic edge cases handled correctly!")
    return True


if __name__ == "__main__":
    quick_test()
