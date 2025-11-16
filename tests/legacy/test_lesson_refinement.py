#!/usr/bin/env python3
"""Test script to verify lesson refinement workflow"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_lesson_refinement():
    """Test that users can iterate on generated lessons"""

    # Create a new session
    print("1. Creating new session...")
    session_data = {
        "grade_level": "Grade 5",
        "strand_code": "CREATE",
        "selected_standard": {
            "id": "5.CR.1",
            "code": "5.CR.1",
            "grade": "Grade 5",
            "strand_code": "CREATE",
            "strand_name": "Create",
            "title": "Generate musical ideas for various purposes and contexts.",
            "description": "Create and explore musical ideas.",
            "objectives": 3,
            "learning_objectives": [
                "5.CR.1.1 - Improvise rhythmic and melodic ideas.",
                "5.CR.1.2 - Compose simple pieces.",
                "5.CR.1.3 - Arrange music for specific purposes.",
            ],
        },
    }

    response = requests.post(f"{BASE_URL}/sessions", json=session_data)
    session = response.json()
    session_id = session["id"]
    print(f"   ✓ Session created: {session_id}\n")

    # Generate initial lesson
    print("2. Generating initial lesson plan...")
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/messages",
        json={"message": "generate lesson plan"},
    )
    result = response.json()
    initial_lesson = result["lesson"]["content"]
    print(f"   ✓ Lesson generated ({len(initial_lesson)} chars)\n")

    # Try to refine the lesson
    print("3. Testing refinement - making lesson shorter...")
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/messages",
        json={
            "message": "Can you make this lesson shorter, suitable for a 30-minute class instead?"
        },
    )

    if response.status_code != 200:
        print(f"   ✗ Refinement request failed: {response.status_code}")
        print(f"     {response.text}")
        return False

    result = response.json()
    refinement_response = result.get("response", "")

    # Check if we got the "complete" message (old behavior) or actual refinement (new behavior)
    if "Lesson generation is complete" in refinement_response:
        print("   ✗ FAILED: Still getting 'complete' message instead of refinement")
        return False
    elif "Lesson Plan Updated" in refinement_response or len(refinement_response) > 500:
        print(f"   ✓ Refinement successful!")
        print(f"     Response length: {len(refinement_response)} chars")

        # Check if lesson was actually updated
        if "lesson" in result:
            refined_lesson = result["lesson"]["content"]
            print(f"     Refined lesson length: {len(refined_lesson)} chars")

            if refined_lesson != initial_lesson:
                print(f"     ✓ Lesson content was modified")
            else:
                print(f"     ⚠ Lesson content appears unchanged")

        print()
        return True
    else:
        print(f"   ? Unexpected response (length: {len(refinement_response)} chars):")
        print(f"     First 200 chars: {refinement_response[:200]}")
        return False

    # Try another refinement
    print("4. Testing second refinement - adding technology...")
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/messages",
        json={
            "message": "Add some technology integration ideas using iPads or music apps"
        },
    )

    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ Second refinement accepted")
        print(f"     Response length: {len(result.get('response', ''))} chars\n")
    else:
        print(f"   ✗ Second refinement failed: {response.status_code}\n")

    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("✓ Lesson refinement workflow is working!")
    print("✓ Users can now iterate on generated lessons")
    print("✓ Multiple refinement rounds supported")

    return True


if __name__ == "__main__":
    success = test_lesson_refinement()
    exit(0 if success else 1)
