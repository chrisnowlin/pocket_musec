#!/usr/bin/env python3
"""
Test script to verify lesson refinement quality and structure.
Tests:
1. Initial lesson generation
2. First refinement request
3. Multiple rounds of refinement
4. Structure validation
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api"


def create_test_session():
    """Create a new test session for lesson generation"""
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
        },
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


def check_lesson_structure(lesson_content):
    """Check if lesson has all required sections"""
    required_sections = {
        "Overview": "Overview" in lesson_content or "## Overview" in lesson_content,
        "Objectives": "Objectives" in lesson_content
        or "Learning Objectives" in lesson_content,
        "Materials": "Materials" in lesson_content or "## Materials" in lesson_content,
        "Procedure": "Procedure" in lesson_content or "Activities" in lesson_content,
        "Assessment": "Assessment" in lesson_content
        or "## Assessment" in lesson_content,
        "Differentiation": "Differentiation" in lesson_content
        or "## Differentiation" in lesson_content,
    }

    results = {}
    for section, present in required_sections.items():
        results[section] = present

    return results


def check_citations(lesson_content):
    """Check if lesson has RAG and web citations"""
    has_rag = any(f"[{i}]" in lesson_content for i in range(1, 10))
    has_web = "http" in lesson_content or "www" in lesson_content
    return has_rag, has_web


def test_refinement_workflow():
    """Test complete refinement workflow"""
    print("=" * 80)
    print("LESSON REFINEMENT QUALITY TEST")
    print("=" * 80)

    # Test 1: Create session and generate initial lesson
    print("\n[TEST 1] Generating initial lesson...")
    print("-" * 80)

    session = create_test_session()
    session_id = session["id"]
    print(f"✓ Created session: {session_id}")

    # Generate lesson
    response = send_message(session_id, "generate lesson plan")
    lesson_content = response.get("response", "")

    print(f"✓ Generated lesson: {len(lesson_content)} characters")

    # Check structure
    structure = check_lesson_structure(lesson_content)
    rag_cites, web_cites = check_citations(lesson_content)

    print("\n[STRUCTURE CHECK] Initial lesson:")
    for section, present in structure.items():
        status = "✓" if present else "❌"
        print(f"  {status} {section}")
    print(f"  {'✓' if rag_cites else '❌'} RAG Citations")
    print(f"  {'✓' if web_cites else '❌'} Web Citations")

    initial_structure_valid = all(structure.values()) and rag_cites

    # Test 2: First refinement - Shorten and focus on recorders
    print("\n[TEST 2] Testing first refinement...")
    print("-" * 80)

    refinement_1 = "Can you shorten this lesson to fit a 30-minute class period and focus more on using recorders?"

    print(f"Sending refinement: {refinement_1}")
    time.sleep(1)  # Brief pause

    response_1 = send_message(session_id, refinement_1)
    refined_content_1 = response_1.get("response", "")

    print(f"✓ Received refinement: {len(refined_content_1)} characters")
    print(
        f"  Length change: {len(refined_content_1) - len(lesson_content):+d} characters"
    )

    # Check structure maintained
    structure_1 = check_lesson_structure(refined_content_1)

    print("\n[STRUCTURE CHECK] Refined lesson (round 1):")
    for section, present in structure_1.items():
        status = "✓" if present else "❌"
        print(f"  {status} {section}")

    # Check if recorder content increased
    recorder_original = lesson_content.lower().count("recorder")
    recorder_refined = refined_content_1.lower().count("recorder")

    print(f"\n[CONTENT CHECK]")
    print(f"  Original recorder mentions: {recorder_original}")
    print(f"  Refined recorder mentions: {recorder_refined}")
    print(
        f"  {'✓' if recorder_refined > recorder_original else '❌'} Recorder focus increased"
    )

    refinement_1_valid = (
        all(structure_1.values()) and recorder_refined >= recorder_original
    )

    # Test 3: Second refinement - Add assessment strategies
    print("\n[TEST 3] Testing second refinement...")
    print("-" * 80)

    refinement_2 = "Add more specific assessment strategies for evaluating student performance on the recorders"

    print(f"Sending refinement: {refinement_2}")
    time.sleep(1)

    response_2 = send_message(session_id, refinement_2)
    refined_content_2 = response_2.get("response", "")

    print(f"✓ Received refinement: {len(refined_content_2)} characters")

    # Check structure maintained
    structure_2 = check_lesson_structure(refined_content_2)

    print("\n[STRUCTURE CHECK] Refined lesson (round 2):")
    for section, present in structure_2.items():
        status = "✓" if present else "❌"
        print(f"  {status} {section}")

    # Check if assessment content increased
    assessment_1 = refined_content_1.lower().count("assessment")
    assessment_2 = refined_content_2.lower().count("assessment")

    print(f"\n[CONTENT CHECK]")
    print(f"  Round 1 assessment mentions: {assessment_1}")
    print(f"  Round 2 assessment mentions: {assessment_2}")
    print(
        f"  {'✓' if assessment_2 >= assessment_1 else '❌'} Assessment focus maintained/increased"
    )

    refinement_2_valid = all(structure_2.values())

    # Test 4: Third refinement - Simplify language
    print("\n[TEST 4] Testing third refinement (stress test)...")
    print("-" * 80)

    refinement_3 = "Make the language more appropriate for struggling readers and add visual aids suggestions"

    print(f"Sending refinement: {refinement_3}")
    time.sleep(1)

    response_3 = send_message(session_id, refinement_3)
    refined_content_3 = response_3.get("response", "")

    print(f"✓ Received refinement: {len(refined_content_3)} characters")

    # Final structure check
    structure_3 = check_lesson_structure(refined_content_3)

    print("\n[STRUCTURE CHECK] Refined lesson (round 3):")
    all_sections_present = True
    for section, present in structure_3.items():
        status = "✓" if present else "❌"
        print(f"  {status} {section}")
        if not present:
            all_sections_present = False

    # Check for visual aids additions
    visual_keywords = ["visual", "chart", "diagram", "picture", "image", "graphic"]
    visual_mentions = sum(refined_content_3.lower().count(kw) for kw in visual_keywords)

    print(f"\n[CONTENT CHECK]")
    print(f"  Visual aid mentions: {visual_mentions}")
    print(f"  {'✓' if visual_mentions > 0 else '❌'} Visual aids added")

    refinement_3_valid = all(structure_3.values())

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✓ Initial lesson generated: {len(lesson_content)} chars")
    print(f"✓ Round 1 refinement (30 min + recorders): {len(refined_content_1)} chars")
    print(f"✓ Round 2 refinement (assessment): {len(refined_content_2)} chars")
    print(
        f"✓ Round 3 refinement (simple language + visuals): {len(refined_content_3)} chars"
    )
    print(f"")
    print(f"Initial structure valid: {'✓' if initial_structure_valid else '❌'}")
    print(f"Refinement 1 valid: {'✓' if refinement_1_valid else '❌'}")
    print(f"Refinement 2 valid: {'✓' if refinement_2_valid else '❌'}")
    print(f"Refinement 3 valid: {'✓' if refinement_3_valid else '❌'}")
    print(f"All sections maintained: {'✓' if all_sections_present else '❌'}")

    # Save refinement history
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_refined_lesson_{timestamp}.txt"

    with open(output_file, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("INITIAL LESSON\n")
        f.write("=" * 80 + "\n\n")
        f.write(lesson_content)
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("REFINEMENT 1: Shorten to 30 min, focus on recorders\n")
        f.write("=" * 80 + "\n\n")
        f.write(refined_content_1)
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("REFINEMENT 2: Add assessment strategies\n")
        f.write("=" * 80 + "\n\n")
        f.write(refined_content_2)
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("REFINEMENT 3: Simplify language, add visual aids\n")
        f.write("=" * 80 + "\n\n")
        f.write(refined_content_3)

    print(f"\n✓ Full refinement history saved to: {output_file}")

    # Final result
    all_tests_passed = (
        initial_structure_valid
        and refinement_1_valid
        and refinement_2_valid
        and refinement_3_valid
        and all_sections_present
    )

    print("\n" + "=" * 80)
    if all_tests_passed:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ❌")
    print("=" * 80)

    return all_tests_passed


if __name__ == "__main__":
    try:
        result = test_refinement_workflow()
        exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
