#!/usr/bin/env python3
"""
Simple test to verify that the API layer now returns selected_objectives
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_api_objectives():
    """Test if API returns selected_objectives in session response"""
    print("=" * 80)
    print("TESTING API OBJECTIVES RESPONSE")
    print("=" * 80)

    # Create session with objective
    session_data = {
        "grade_level": "Grade 3",
        "strand_code": "CONNECT",
        "standard_id": "3.CN.1",
        "selected_objective": "3.CN.1.1",
        "additional_context": "Focus on describing local community music",
    }

    response = requests.post(f"{BASE_URL}/sessions", json=session_data)
    if response.status_code != 200:
        print(f"❌ Failed to create session: {response.status_code}")
        print(response.text)
        return False

    session = response.json()
    print(f"✓ Created session: {session['id']}")
    print(
        f"✓ Selected objectives in response: {session.get('selected_objectives', 'None')}"
    )

    # Check if selected_objectives is returned
    if session.get("selected_objectives") == "3.CN.1.1":
        print("✅ SUCCESS: API layer correctly returns selected_objectives")
        return True
    else:
        print("❌ FAILED: API layer not returning selected_objectives correctly")
        return False


if __name__ == "__main__":
    try:
        result = test_api_objectives()
        exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
