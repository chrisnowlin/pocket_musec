#!/usr/bin/env python3
"""
Test script to verify that LessonAgent uses objectives explicitly in lesson generation.
Currently it seems to only reference standards, not specific learning objectives.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api"


def create_test_session_with_objectives():
    """Create a new test session with specific objectives"""
    session_data = {
        "grade_level": "Grade 3",
        "strand_code": "CONNECT",
        "selected_standard": {
            "id": "3.CN.1",
            "code": "3.CN.1",
            "grade": "Grade 3",
            "strand_code": "CONNECT",
            "strand_name": "Connect",
            "title": "Relate musical ideas and works with personal, societal, cultural, historical, and daily life contexts",
            "description": "Explore and relate artistic ideas and works to past, present, and future societies and cultures.",
            "objectives": 3,
            "learning_objectives": [
                "3.CN.1.1 - Describe music found in the local community or region.",
                "3.CN.1.2 - Compare elements of music with elements of other disciplines.",
                "3.CN.1.3 - Describe personal emotions evoked by a variety of music.",
            ],
        },
        "selected_objectives": "3.CN.1.1,3.CN.1.2",
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
        desc_keywords = obj_desc.split()[:3]  # First 3 words
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

    return analysis


def test_objectives_usage():
    """Test if LessonAgent uses objectives in lesson generation"""
    print("=" * 80)
    print("TESTING OBJECTIVES USAGE IN LESSON GENERATION")
    print("=" * 80)

    # Test 1: Create session with specific objectives
    print("\n[TEST 1] Creating session with explicit objectives...")
    print("-" * 80)

    session = create_test_session_with_objectives()
    session_id = session["id"]
    print(f"✓ Created session: {session_id}")

    # Show what objectives we're testing
    selected_objectives_str = session.get("selected_objectives", "")
    print(f"✓ Session returned selected_objectives: {selected_objectives_str}")

    # Convert string format to expected object format for analysis
    objectives = []
    if selected_objectives_str:
        obj_codes = [
            code.strip() for code in selected_objectives_str.split(",") if code.strip()
        ]
        objectives = [
            {
                "code": code,
                "description": f"Description for {code}",  # Placeholder for test
                "id": code,
            }
            for code in obj_codes
        ]

    print(f"✓ Testing {len(objectives)} objectives:")
    for obj in objectives:
        print(f"  - {obj['code']}: {obj['description']}")

    # Test 2: Generate lesson with explicit objective request
    print("\n[TEST 2] Generating lesson with objective focus...")
    print("-" * 80)

    generation_message = "Generate a lesson plan that specifically addresses the selected learning objectives: 3.CN.1.1 and 3.CN.1.2"
    print(f"Sending: {generation_message}")

    response = send_message(session_id, generation_message)
    lesson_content = response.get("response", "")

    print(f"✓ Generated lesson: {len(lesson_content)} characters")

    # Analyze content
    analysis = analyze_lesson_content(lesson_content, objectives)

    print(f"\n[CONTENT ANALYSIS]")
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
        f"  Has Standards Alignment section: {'✓' if analysis['alignment_section'] else '❌'}"
    )

    # Test 3: Try refinement with objective focus
    print("\n[TEST 3] Refining with explicit objective alignment...")
    print("-" * 80)

    refinement_message = "Please make sure this lesson explicitly addresses objective 3.CN.1.1 - 'Describe music found in the local community or region' and objective 3.CN.1.2 - 'Compare elements of music with elements of other disciplines'"

    print(f"Sending refinement: {refinement_message}")
    time.sleep(1)

    response_2 = send_message(session_id, refinement_message)
    refined_content = response_2.get("response", "")

    print(f"✓ Received refinement: {len(refined_content)} characters")

    # Analyze refined content
    analysis_2 = analyze_lesson_content(refined_content, objectives)

    print(f"\n[REFINED CONTENT ANALYSIS]")
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

    # Test 4: Try direct objective-focused generation
    print("\n[TEST 4] Testing direct objective-focused generation...")
    print("-" * 80)

    # Create new session
    session_2 = create_test_session_with_objectives()
    session_id_2 = session_2["id"]

    direct_message = "Create a lesson specifically for objective 3.CN.1.1: Describe music found in the local community or region. Focus on having students identify and describe music they hear in their neighborhood."

    print(f"Sending direct objective message: {direct_message}")

    response_3 = send_message(session_id_2, direct_message)
    direct_content = response_3.get("response", "")

    print(f"✓ Received direct objective lesson: {len(direct_content)} characters")

    # Analyze direct content
    analysis_3 = analyze_lesson_content(direct_content, objectives)

    print(f"\n[DIRECT OBJECTIVE ANALYSIS]")
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

    # Summary
    print("\n" + "=" * 80)
    print("OBJECTIVES USAGE TEST SUMMARY")
    print("=" * 80)

    objectives_mentioned = any(
        [
            analysis["mentions_objectives"],
            analysis_2["mentions_objectives"],
            analysis_3["mentions_objectives"],
        ]
    )

    codes_found = set()
    codes_found.update(analysis["objective_codes_found"])
    codes_found.update(analysis_2["objective_codes_found"])
    codes_found.update(analysis_3["objective_codes_found"])

    print(
        f"✓ Objectives explicitly mentioned in any response: {'✓' if objectives_mentioned else '❌'}"
    )
    print(f"✓ Objective codes found across all tests: {list(codes_found)}")
    print(
        f"✓ Standard references working: {'✓' if analysis['mentions_standard'] else '❌'}"
    )

    # Save results for inspection
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_objectives_usage_{timestamp}.txt"

    with open(output_file, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("TEST 1: Standard lesson generation with objectives\n")
        f.write("=" * 80 + "\n\n")
        f.write(lesson_content)
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("TEST 2: Refined with explicit objective alignment\n")
        f.write("=" * 80 + "\n\n")
        f.write(refined_content)
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("TEST 3: Direct objective-focused generation\n")
        f.write("=" * 80 + "\n\n")
        f.write(direct_content)
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("ANALYSIS SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Objectives mentioned: {objectives_mentioned}\n")
        f.write(f"Objective codes found: {list(codes_found)}\n")
        f.write(f"Standard references: {analysis['mentions_standard']}\n")

    print(f"\n✓ Full test results saved to: {output_file}")

    # Final assessment
    print("\n" + "=" * 80)
    if objectives_mentioned and len(codes_found) > 0:
        print("RESULT: ✅ Objectives ARE being used in lesson generation")
    else:
        print("RESULT: ❌ Objectives are NOT being explicitly used")
        print(
            "         The agent may only be referencing standards, not specific objectives"
        )
    print("=" * 80)

    return objectives_mentioned and len(codes_found) > 0


if __name__ == "__main__":
    try:
        result = test_objectives_usage()
        exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
