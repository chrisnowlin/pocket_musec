#!/usr/bin/env python3
"""
Debug session creation to see why selected_objectives isn't being stored
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_session_creation():
    """Test session creation step by step"""

    # Create session with selected_objectives
    session_data = {
        "grade_level": "Grade 3",
        "strand_code": "CONNECT",
        "standard_id": "3.CN.1",
        "selected_objectives": "3.CN.1.1,3.CN.1.2",
    }

    print("Creating session with data:")
    print(json.dumps(session_data, indent=2))

    response = requests.post(f"{BASE_URL}/sessions", json=session_data)
    print(f"\nResponse status: {response.status_code}")

    if response.status_code != 200:
        print(f"Error response: {response.text}")
        return None

    session = response.json()
    print(f"\nSession response:")
    print(json.dumps(session, indent=2))

    # Try to get the session again
    session_id = session["id"]
    print(f"\nFetching session {session_id} again...")

    response2 = requests.get(f"{BASE_URL}/sessions/{session_id}")
    if response2.status_code == 200:
        session2 = response2.json()
        print(f"Fetched session:")
        print(json.dumps(session2, indent=2))
    else:
        print(f"Failed to fetch session: {response2.text}")


if __name__ == "__main__":
    test_session_creation()
