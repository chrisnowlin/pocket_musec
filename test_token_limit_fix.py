#!/usr/bin/env python3
"""Test script to verify token limit increase for lesson generation"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"


def test_lesson_generation():
    """Test lesson generation with increased token limit"""

    # Create a new session
    print("Creating new session...")
    session_data = {
        "grade_level": "Grade 3",
        "strand_code": "CONNECT",
        "selected_standard": {
            "id": "3.CN.1",
            "code": "3.CN.1",
            "grade": "Grade 3",
            "strand_code": "CONNECT",
            "strand_name": "Connect",
            "title": "Relate musical ideas and works with personal, societal, cultural, historical, and daily life contexts, including diverse and marginalized groups.",
            "description": "Explore and relate artistic ideas and works to past, present, and future societies and cultures.",
            "objectives": 3,
            "learning_objectives": [
                "3.CN.1.1 - Describe music found in the local community or region.",
                "3.CN.1.2 - Compare elements of music with elements of other disciplines.",
                "3.CN.1.3 - Describe personal emotions evoked by a variety of music.",
            ],
        },
    }

    response = requests.post(f"{BASE_URL}/sessions", json=session_data)
    if response.status_code != 200:
        print(f"Failed to create session: {response.status_code}")
        print(response.text)
        return

    session = response.json()
    session_id = session["id"]
    print(f"Created session: {session_id}")

    # Send initial message to trigger lesson generation
    print("\nSending lesson generation request...")
    chat_request = {"message": "generate lesson plan"}

    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/messages", json=chat_request
    )
    if response.status_code != 200:
        print(f"Failed to send message: {response.status_code}")
        print(response.text)
        return

    chat_response = response.json()
    lesson_content = chat_response.get("response", "")

    # Check lesson length and completeness
    print(f"\n{'=' * 80}")
    print("LESSON GENERATION TEST RESULTS")
    print(f"{'=' * 80}")
    print(f"Response length: {len(lesson_content)} characters")
    print(f"Response word count: ~{len(lesson_content.split())} words")

    # Check for key sections
    sections_to_check = [
        (
            "Learning Objectives",
            "Learning Objectives" in lesson_content
            or "## Learning Objectives" in lesson_content,
        ),
        (
            "Materials",
            "Materials" in lesson_content or "## Materials" in lesson_content,
        ),
        (
            "Lesson Procedure",
            "Lesson Procedure" in lesson_content
            or "## Lesson Procedure" in lesson_content
            or "Procedure" in lesson_content,
        ),
        (
            "Assessment",
            "Assessment" in lesson_content or "## Assessment" in lesson_content,
        ),
        (
            "Differentiation",
            "Differentiation" in lesson_content
            or "## Differentiation" in lesson_content,
        ),
        (
            "Closure/Reflection",
            "Closure" in lesson_content or "Reflection" in lesson_content,
        ),
        (
            "RAG Citations",
            "## Educational Resources" in lesson_content
            or "Bibliography" in lesson_content
            or "Sources" in lesson_content
            or "[1]" in lesson_content,
        ),
    ]

    print(f"\n{'=' * 80}")
    print("SECTION COMPLETENESS CHECK")
    print(f"{'=' * 80}")
    all_present = True
    for section_name, present in sections_to_check:
        status = "✅" if present else "❌"
        print(f"{status} {section_name}")
        if not present:
            all_present = False

    # Check if lesson was cut off
    last_100 = lesson_content[-100:] if len(lesson_content) > 100 else lesson_content
    looks_complete = lesson_content.endswith(
        (".", "!", "?", "\n")
    ) and not last_100.endswith((",", "-", "ding-dong", "the"))

    print(f"\n{'=' * 80}")
    print("COMPLETENESS CHECK")
    print(f"{'=' * 80}")
    print(f"Last 100 characters: ...{last_100}")
    print(
        f"Looks complete: {'✅ Yes' if looks_complete else '❌ No (appears cut off)'}"
    )

    # Overall result
    print(f"\n{'=' * 80}")
    print("OVERALL RESULT")
    print(f"{'=' * 80}")
    if all_present and looks_complete:
        print(
            "✅ SUCCESS: Lesson plan is complete with all sections including RAG citations!"
        )
    elif all_present and not looks_complete:
        print("⚠️  PARTIAL: All sections present but lesson may be cut off")
    elif not all_present and looks_complete:
        print("⚠️  PARTIAL: Lesson appears complete but missing some sections")
    else:
        print("❌ FAILED: Lesson incomplete and/or cut off")

    # Save full lesson to file for inspection
    output_file = f"test_lesson_output_{int(time.time())}.txt"
    with open(output_file, "w") as f:
        f.write(lesson_content)
    print(f"\nFull lesson saved to: {output_file}")

    return session_id, lesson_content


if __name__ == "__main__":
    test_lesson_generation()
