#!/usr/bin/env python3
"""
Simple test to debug the objective filtering issue
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def create_simple_session():
    """Create a simple session with objectives"""
    session_data = {
        "grade_level": "Grade 3",
        "strand_code": "CONNECT",
        "standard_id": "3.CN.1",
        "selected_objectives": "3.CN.1.1,3.CN.1.2",
    }

    response = requests.post(f"{BASE_URL}/sessions", json=session_data)
    if response.status_code != 200:
        print(f"Failed to create session: {response.status_code} - {response.text}")
        return None

    session = response.json()
    print(f"Created session: {session['id']}")
    print(f"Selected objectives: {session.get('selected_objectives', 'None')}")
    return session


def send_simple_message(session_id, message):
    """Send a simple message"""
    chat_request = {"message": message}

    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/messages", json=chat_request
    )

    if response.status_code != 200:
        print(f"Failed to send message: {response.status_code} - {response.text}")
        return None

    return response.json()


if __name__ == "__main__":
    print("Creating simple session...")
    session = create_simple_session()
    if not session:
        exit(1)

    print("Sending simple message...")
    response = send_simple_message(session["id"], "hello")
    if response:
        print("Success!")
    else:
        print("Failed!")
