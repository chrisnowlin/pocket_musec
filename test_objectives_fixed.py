#!/usr/bin/env python3
"""
Test script to verify that LessonAgent uses objectives explicitly in lesson generation.
Fixed version using correct API format (selected_objective: string, not list)
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api"


def create_test_session_with_objective():
    """Create a new test session with specific objective (using correct API format)"""
    session_data = {
        "grade_level": "Grade 3",
        "strand_code": "CONNECT",
        "standard_id": "3.CN.1",
        "selected_objective": "3.CN.1.1",  # Single objective as string
        "additional_context": "Focus on describing local community music",
    }

    response = requests.post(f"{BASE_URL}/sessions", json=session_data)
    if response.status_code != 200:
        raise Exception(
            f"Failed to create session: {response.status_code} - {response.text}"
        )

    return response.json()


def create_test_session_with_multiple_objectives():
    """Create session with multiple objectives mentioned in context"""
    session_data = {
        "grade_level": "Grade 3",
        "strand_code": "CONNECT",
        "standard_id": "3.CN.1",
        "selected_objective": "3.CN.1.1, 3.CN.1.2",  # Multiple objectives as comma-separated string
        "additional_context": "Focus on describing local community music and comparing with other disciplines",
    }

    response = requests.post(f"{BASE_URL}/sessions", json=session_data)
    if response.status_code != 200:
        raise Exception(
            f"Failed to create session: {response.status_code} - {response.text}"
        )

    return response.json()


def send_message(session_id, message):
    """Send a message to the session and return response"""
    chat_request = {"message": message}

    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/messages", json=chat_request
    )

    if response.status_code != 200:
        raise Exception(
            f"Failed to send message: {response.status_code} - {response.text}"
        )

    return response.json()


def analyze_lesson_content(lesson_content, expected_objectives):
    """Analyze if lesson content explicitly references objectives"""
    analysis = {
        "mentions_standard": False,
        "mentions_objectives": False,
        "objective_codes_found": [],
        "objective_descriptions_found": [],
        "standard_code_found": False,
        "lesson_objectives_section": False,
        "alignment_section": False,
        "objective_in_activities": False,
        "objective_in_assessment": False,
    }

    # Check for standard reference
    if "3.CN.1" in lesson_content:
        analysis["mentions_standard"] = True
        analysis["standard_code_found"] = True

    # Check for objective references
    for obj in expected_objectives:
        obj_code = obj.get("code", "")
        obj_desc = obj.get("description", "")

        if obj_code in lesson_content:
            analysis["mentions_objectives"] = True
            analysis["objective_codes_found"].append(obj_code)

        # Check for key phrases from objective descriptions
        desc_keywords = [
            "local community",
            "region",
            "compare",
            "elements",
            "disciplines",
        ]
        for keyword in desc_keywords:
            if keyword.lower() in lesson_content.lower():
                analysis["objective_descriptions_found"].append(obj_code)
                analysis["mentions_objectives"] = True
                break

    # Check for lesson objectives section
    if any(
        section in lesson_content
        for section in ["Learning Objectives", "Lesson Objectives", "Objectives"]
    ):
        analysis["lesson_objectives_section"] = True

    # Check for standards alignment section
    if any(
        section in lesson_content
        for section in ["Standards Alignment", "Alignment", "Standards"]
    ):
        analysis["alignment_section"] = True

    # Check if objectives appear in activities
    if (
        "local community" in lesson_content.lower()
        and "music" in lesson_content.lower()
    ):
        analysis["objective_in_activities"] = True

    # Check if objectives appear in assessment
    if "assessment" in lesson_content.lower() and (
        "describe" in lesson_content.lower() or "compare" in lesson_content.lower()
    ):
        analysis["objective_in_assessment"] = True

    return analysis


def test_objectives_usage_fixed():
    """Test if LessonAgent uses objectives when properly formatted"""
    print("=" * 80)
    print("TESTING OBJECTIVES USAGE - FIXED API FORMAT")
    print("=" * 80)

    # Test 1: Single objective
    print("\n[TEST 1] Single objective (3.CN.1.1)...")
    print("-" * 80)

    session = create_test_session_with_objective()
    session_id = session["id"]
    print(f"✓ Created session: {session_id}")

    # Show what objective we're testing
    objective = session.get("selected_standard", {}).get("learning_objectives", [])
    print(f"✓ Selected objective: {session.get('selected_objective', 'None')}")

    # Generate lesson
    generation_message = "generate lesson plan"
    print(f"Sending: {generation_message}")

    response = send_message(session_id, generation_message)
    lesson_content = response.get("response", "")

    print(f"✓ Generated lesson: {len(lesson_content)} characters")

    # Analyze content
    expected_objectives = [
        {
            "code": "3.CN.1.1",
            "description": "Describe music found in the local community or region",
        }
    ]
    analysis = analyze_lesson_content(lesson_content, expected_objectives)

    print(f"\n[CONTENT ANALYSIS - SINGLE OBJECTIVE]")
    print(
        f"  Mentions standard (3.CN.1): {'✓' if analysis['mentions_standard'] else '❌'}"
    )
    print(f"  Mentions objectives: {'✓' if analysis['mentions_objectives'] else '❌'}")
    print(f"  Objective codes found: {analysis['objective_codes_found']}")
    print(
        f"  Objective descriptions referenced: {analysis['objective_descriptions_found']}"
    )
    print(
        f"  Has Learning Objectives section: {'✓' if analysis['lesson_objectives_section'] else '❌'}"
    )
    print(
        f"  Objectives in activities: {'✓' if analysis['objective_in_activities'] else '❌'}"
    )

    # Test 2: Multiple objectives
    print("\n[TEST 2] Multiple objectives (3.CN.1.1, 3.CN.1.2)...")
    print("-" * 80)

    session_2 = create_test_session_with_multiple_objectives()
    session_id_2 = session_2["id"]
    print(f"✓ Created session: {session_id_2}")
    print(f"✓ Selected objectives: {session_2.get('selected_objective', 'None')}")

    # Generate lesson
    response_2 = send_message(session_id_2, generation_message)
    lesson_content_2 = response_2.get("response", "")

    print(f"✓ Generated lesson: {len(lesson_content_2)} characters")

    # Analyze content
    expected_objectives_2 = [
        {
            "code": "3.CN.1.1",
            "description": "Describe music found in the local community or region",
        },
        {
            "code": "3.CN.1.2",
            "description": "Compare elements of music with elements of other disciplines",
        },
    ]
    analysis_2 = analyze_lesson_content(lesson_content_2, expected_objectives_2)

    print(f"\n[CONTENT ANALYSIS - MULTIPLE OBJECTIVES]")
    print(
        f"  Mentions standard (3.CN.1): {'✓' if analysis_2['mentions_standard'] else '❌'}"
    )
    print(
        f"  Mentions objectives: {'✓' if analysis_2['mentions_objectives'] else '❌'}"
    )
    print(f"  Objective codes found: {analysis_2['objective_codes_found']}")
    print(
        f"  Objective descriptions referenced: {analysis_2['objective_descriptions_found']}"
    )
    print(
        f"  Has Learning Objectives section: {'✓' if analysis_2['lesson_objectives_section'] else '❌'}"
    )
    print(
        f"  Objectives in activities: {'✓' if analysis_2['objective_in_activities'] else '❌'}"
    )

    # Test 3: Explicit objective request in message
    print("\n[TEST 3] Explicit objective request in message...")
    print("-" * 80)

    session_3 = create_test_session_with_objective()
    session_id_3 = session_3["id"]

    explicit_message = "Generate a lesson plan that specifically addresses objective 3.CN.1.1: Describe music found in the local community or region. Make sure students actually describe local music they hear."

    print(f"Sending explicit message: {explicit_message}")

    response_3 = send_message(session_id_3, explicit_message)
    lesson_content_3 = response_3.get("response", "")

    print(f"✓ Generated lesson: {len(lesson_content_3)} characters")

    # Analyze content
    analysis_3 = analyze_lesson_content(lesson_content_3, expected_objectives)

    print(f"\n[CONTENT ANALYSIS - EXPLICIT REQUEST]")
    print(
        f"  Mentions standard (3.CN.1): {'✓' if analysis_3['mentions_standard'] else '❌'}"
    )
    print(
        f"  Mentions objectives: {'✓' if analysis_3['mentions_objectives'] else '❌'}"
    )
    print(f"  Objective codes found: {analysis_3['objective_codes_found']}")
    print(
        f"  Objective descriptions referenced: {analysis_3['objective_descriptions_found']}"
    )
    print(
        f"  Has Learning Objectives section: {'✓' if analysis_3['lesson_objectives_section'] else '❌'}"
    )
    print(
        f"  Objectives in activities: {'✓' if analysis_3['objective_in_activities'] else '❌'}"
    )

    # Summary
    print("\n" + "=" * 80)
    print("OBJECTIVES USAGE TEST SUMMARY - FIXED")
    print("=" * 80)

    all_objectives_mentioned = any(
        [
            analysis["mentions_objectives"],
            analysis_2["mentions_objectives"],
            analysis_3["mentions_objectives"],
        ]
    )

    all_codes_found = set()
    all_codes_found.update(analysis["objective_codes_found"])
    all_codes_found.update(analysis_2["objective_codes_found"])
    all_codes_found.update(analysis_3["objective_codes_found"])

    activities_with_objectives = any(
        [
            analysis["objective_in_activities"],
            analysis_2["objective_in_activities"],
            analysis_3["objective_in_activities"],
        ]
    )

    print(
        f"✓ Objectives explicitly mentioned in any response: {'✓' if all_objectives_mentioned else '❌'}"
    )
    print(f"✓ Objective codes found across all tests: {list(all_codes_found)}")
    print(
        f"✓ Objectives integrated into activities: {'✓' if activities_with_objectives else '❌'}"
    )
    print(
        f"✓ Standard references working: {'✓' if analysis['mentions_standard'] else '❌'}"
    )

    # Save results for inspection
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_objectives_fixed_{timestamp}.txt"

    with open(output_file, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("TEST 1: Single objective (3.CN.1.1)\n")
        f.write("=" * 80 + "\n\n")
        f.write(lesson_content)
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("TEST 2: Multiple objectives (3.CN.1.1, 3.CN.1.2)\n")
        f.write("=" * 80 + "\n\n")
        f.write(lesson_content_2)
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("TEST 3: Explicit objective request\n")
        f.write("=" * 80 + "\n\n")
        f.write(lesson_content_3)
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("ANALYSIS SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Objectives mentioned: {all_objectives_mentioned}\n")
        f.write(f"Objective codes found: {list(all_codes_found)}\n")
        f.write(f"Objectives in activities: {activities_with_objectives}\n")

    print(f"\n✓ Full test results saved to: {output_file}")

    # Final assessment
    print("\n" + "=" * 80)
    if all_objectives_mentioned and len(all_codes_found) > 0:
        print("RESULT: ✅ Objectives ARE being used in lesson generation")
        if activities_with_objectives:
            print("         Objectives are properly integrated into lesson activities")
        else:
            print("         Objectives mentioned but not fully integrated")
    else:
        print("RESULT: ❌ Objectives are NOT being explicitly used")
        print(
            "         The agent may only be referencing standards, not specific objectives"
        )
        print("         RECOMMENDATION: Enhance prompt templates to include objectives")
    print("=" * 80)

    return all_objectives_mentioned and len(all_codes_found) > 0


if __name__ == "__main__":
    try:
        result = test_objectives_usage_fixed()
        exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
