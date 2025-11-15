#!/usr/bin/env python3
"""
Debug test to see actual lesson content
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def debug_lesson_content():
    """Debug what's actually in the lesson content"""

    # Simple test case
    session_data = {
        "grade_level": "Grade 3",
        "strand_code": "CONNECT",
        "standard_id": "3.CN.1",
        "selected_objectives": "3.CN.1.1,3.CN.1.2",
    }

    response = requests.post(f"{BASE_URL}/sessions", json=session_data)
    session = response.json()

    print(f"Session created with objectives: {session['selected_objectives']}")

    # Send message
    chat_request = {
        "message": "Generate a lesson plan that specifically addresses objectives 3.CN.1.1 and 3.CN.1.2"
    }
    response = requests.post(
        f"{BASE_URL}/sessions/{session['id']}/messages", json=chat_request
    )
    lesson_data = response.json()
    lesson_content = lesson_data["response"]

    print(f"\nGenerated lesson ({len(lesson_content)} chars):")
    print("=" * 60)
    print(lesson_content[:1000])  # First 1000 chars
    print("=" * 60)
    print(lesson_content[1000:2000])  # Next 1000 chars
    print("=" * 60)

    # Check for specific patterns
    print(f"\n🔍 Content Analysis:")
    print(f"Contains '3.CN.1.1': {'3.CN.1.1' in lesson_content}")
    print(f"Contains '3.CN.1.2': {'3.CN.1.2' in lesson_content}")
    print(f"Contains '3.CN.1': {'3.CN.1' in lesson_content}")
    print(f"Contains 'objective': {'objective' in lesson_content.lower()}")
    print(f"Contains 'standard': {'standard' in lesson_content.lower()}")

    # Look for any standard-like patterns
    import re

    patterns = re.findall(r"\d+\.[A-Z]+\.\d+(\.\d+)?", lesson_content)
    print(f"Standard patterns found: {patterns}")


if __name__ == "__main__":
    debug_lesson_content()
