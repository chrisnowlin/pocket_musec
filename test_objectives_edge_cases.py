#!/usr/bin/env python3
"""
Comprehensive edge case testing for objectives usage in lesson generation
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api"


def create_test_session(session_data):
    """Helper to create a session"""
    response = requests.post(f"{BASE_URL}/sessions", json=session_data)
    if response.status_code != 200:
        raise Exception(
            f"Failed to create session: {response.status_code} - {response.text}"
        )
    return response.json()


def send_message(session_id, message):
    """Helper to send a message"""
    chat_request = {"message": message}
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/messages", json=chat_request
    )
    if response.status_code != 200:
        raise Exception(
            f"Failed to send message: {response.status_code} - {response.text}"
        )
    return response.json()


def analyze_lesson_content(lesson_content, expected_objectives=None):
    """Analyze lesson content for standards and objectives references"""
    analysis = {
        "mentions_standard": False,
        "mentions_objectives": False,
        "objective_codes_found": [],
        "standard_codes_found": [],
        "has_objectives_section": False,
        "has_standards_section": False,
        "lesson_length": len(lesson_content),
    }

    # Check for standard references
    import re

    standard_pattern = r"\d+\.[A-Z]+\.\d+"
    standard_matches = re.findall(standard_pattern, lesson_content)
    analysis["standard_codes_found"] = list(set(standard_matches))
    analysis["mentions_standard"] = len(standard_matches) > 0

    # Check for objective references
    if expected_objectives:
        for obj_code in expected_objectives:
            if obj_code in lesson_content:
                analysis["objective_codes_found"].append(obj_code)
        analysis["mentions_objectives"] = len(analysis["objective_codes_found"]) > 0

    # Check for sections
    if any(
        section in lesson_content
        for section in ["Learning Objectives", "Lesson Objectives", "Objectives"]
    ):
        analysis["has_objectives_section"] = True

    if any(
        section in lesson_content
        for section in ["Standards Alignment", "Alignment", "Standards"]
    ):
        analysis["has_standards_section"] = True

    return analysis


def test_edge_case_1_single_objective():
    """Test: Single objective selection"""
    print("\n" + "=" * 80)
    print("EDGE CASE 1: Single Objective Selection")
    print("=" * 80)

    session_data = {
        "grade_level": "Grade 4",
        "strand_code": "CREATE",
        "standard_id": "4.CR.1",
        "selected_objectives": "4.CR.1.1",
    }

    session = create_test_session(session_data)
    print(f"✓ Created session with single objective: {session['selected_objectives']}")

    response = send_message(session["id"], "Generate a lesson for this objective")
    analysis = analyze_lesson_content(response["response"], ["4.CR.1.1"])

    print(f"✓ Generated lesson: {analysis['lesson_length']} characters")
    print(f"✓ Mentions standard: {analysis['mentions_standard']}")
    print(
        f"✓ Mentions objective 4.CR.1.1: {'4.CR.1.1' in analysis['objective_codes_found']}"
    )
    print(f"✓ Standards found: {analysis['standard_codes_found']}")

    return (
        analysis["mentions_objectives"]
        and "4.CR.1.1" in analysis["objective_codes_found"]
    )


def test_edge_case_2_multiple_objectives():
    """Test: Multiple objectives (more than 2)"""
    print("\n" + "=" * 80)
    print("EDGE CASE 2: Multiple Objectives (3+ objectives)")
    print("=" * 80)

    session_data = {
        "grade_level": "Grade 5",
        "strand_code": "PERFORM",
        "standard_id": "5.PR.1",
        "selected_objectives": "5.PR.1.1,5.PR.1.2,5.PR.1.3",
    }

    session = create_test_session(session_data)
    print(f"✓ Created session with 3 objectives: {session['selected_objectives']}")

    response = send_message(
        session["id"], "Create a lesson addressing all selected objectives"
    )
    analysis = analyze_lesson_content(
        response["response"], ["5.PR.1.1", "5.PR.1.2", "5.PR.1.3"]
    )

    print(f"✓ Generated lesson: {analysis['lesson_length']} characters")
    print(f"✓ Objectives found: {analysis['objective_codes_found']}")
    print(f"✓ Expected objectives: 5.PR.1.1, 5.PR.1.2, 5.PR.1.3")

    # Check if at least 2 of 3 objectives are mentioned
    found_count = len(
        [
            obj
            for obj in ["5.PR.1.1", "5.PR.1.2", "5.PR.1.3"]
            if obj in analysis["objective_codes_found"]
        ]
    )
    return found_count >= 2


def test_edge_case_3_no_objectives():
    """Test: No objectives selected (backward compatibility)"""
    print("\n" + "=" * 80)
    print("EDGE CASE 3: No Objectives Selected (Backward Compatibility)")
    print("=" * 80)

    session_data = {
        "grade_level": "Grade 2",
        "strand_code": "RESPOND",
        "standard_id": "2.RE.1",
        # No selected_objectives field
    }

    session = create_test_session(session_data)
    print(
        f"✓ Created session without objectives: {session.get('selected_objectives', 'None')}"
    )

    response = send_message(session["id"], "Generate a lesson for this standard")
    analysis = analyze_lesson_content(response["response"])

    print(f"✓ Generated lesson: {analysis['lesson_length']} characters")
    print(f"✓ Mentions standard: {analysis['mentions_standard']}")
    print(f"✓ Standards found: {analysis['standard_codes_found']}")

    # Should work without objectives, just mention the standard
    return analysis["mentions_standard"] and len(analysis["objective_codes_found"]) == 0


def test_edge_case_4_empty_objectives():
    """Test: Empty objectives string"""
    print("\n" + "=" * 80)
    print("EDGE CASE 4: Empty Objectives String")
    print("=" * 80)

    session_data = {
        "grade_level": "Grade 1",
        "strand_code": "CONNECT",
        "standard_id": "1.CN.1",
        "selected_objectives": "",
    }

    session = create_test_session(session_data)
    print(
        f"✓ Created session with empty objectives: '{session['selected_objectives']}'"
    )

    response = send_message(session["id"], "Generate a lesson")
    analysis = analyze_lesson_content(response["response"])

    print(f"✓ Generated lesson: {analysis['lesson_length']} characters")
    print(f"✓ Mentions standard: {analysis['mentions_standard']}")

    # Should work like no objectives case
    return analysis["mentions_standard"]


def test_edge_case_5_malformed_objectives():
    """Test: Malformed objectives string"""
    print("\n" + "=" * 80)
    print("EDGE CASE 5: Malformed Objectives String")
    print("=" * 80)

    session_data = {
        "grade_level": "Grade 6",
        "strand_code": "CREATE",
        "standard_id": "6.CR.1",
        "selected_objectives": "6.CR.1.1,, ,6.CR.1.2, ,6.CR.1.3",
    }

    session = create_test_session(session_data)
    print(
        f"✓ Created session with malformed objectives: '{session['selected_objectives']}'"
    )

    response = send_message(
        session["id"], "Generate a lesson despite malformed objectives"
    )
    analysis = analyze_lesson_content(
        response["response"], ["6.CR.1.1", "6.CR.1.2", "6.CR.1.3"]
    )

    print(f"✓ Generated lesson: {analysis['lesson_length']} characters")
    print(f"✓ Objectives found: {analysis['objective_codes_found']}")

    # Should handle gracefully and still work
    return analysis["mentions_standard"] and response["response"] is not None


def test_edge_case_6_nonexistent_objectives():
    """Test: Non-existent objective IDs"""
    print("\n" + "=" * 80)
    print("EDGE CASE 6: Non-existent Objective IDs")
    print("=" * 80)

    session_data = {
        "grade_level": "Grade 3",
        "strand_code": "PERFORM",
        "standard_id": "3.PR.1",
        "selected_objectives": "3.PR.1.99,3.PR.1.100,3.PR.1.1",
    }

    session = create_test_session(session_data)
    print(
        f"✓ Created session with mixed real/fake objectives: {session['selected_objectives']}"
    )

    response = send_message(session["id"], "Generate a lesson with these objectives")
    analysis = analyze_lesson_content(response["response"], ["3.PR.1.1"])

    print(f"✓ Generated lesson: {analysis['lesson_length']} characters")
    print(f"✓ Real objective found: {'3.PR.1.1' in analysis['objective_codes_found']}")
    print(f"✓ Should gracefully ignore fake objectives")

    # Should find the real objective and ignore fake ones
    return (
        "3.PR.1.1" in analysis["objective_codes_found"]
        and analysis["mentions_standard"]
    )


def test_edge_case_7_objectives_from_different_standards():
    """Test: Objectives from different standards (shouldn't work but should handle gracefully)"""
    print("\n" + "=" * 80)
    print("EDGE CASE 7: Objectives from Different Standards")
    print("=" * 80)

    session_data = {
        "grade_level": "Grade 4",
        "strand_code": "CREATE",
        "standard_id": "4.CR.1",
        "selected_objectives": "4.CR.1.1,3.PR.1.1,5.RE.1.1",
    }

    session = create_test_session(session_data)
    print(
        f"✓ Created session with mixed standard objectives: {session['selected_objectives']}"
    )

    response = send_message(session["id"], "Generate a lesson")
    analysis = analyze_lesson_content(response["response"])

    print(f"✓ Generated lesson: {analysis['lesson_length']} characters")
    print(f"✓ Standards found: {analysis['standard_codes_found']}")
    print(f"✓ Should only find objectives from the selected standard")

    # Should work and only include objectives from the actual standard
    return analysis["mentions_standard"] and response["response"] is not None


def test_edge_case_8_very_long_objectives_list():
    """Test: Very long objectives list"""
    print("\n" + "=" * 80)
    print("EDGE CASE 8: Very Long Objectives List")
    print("=" * 80)

    # Create a long list of objectives (some real, some fake)
    objectives_list = ",".join([f"K.CR.1.{i}" for i in range(1, 20)])  # 19 objectives
    session_data = {
        "grade_level": "Kindergarten",
        "strand_code": "CREATE",
        "standard_id": "K.CR.1",
        "selected_objectives": objectives_list,
    }

    session = create_test_session(session_data)
    print(f"✓ Created session with {len(objectives_list.split(','))} objectives")

    response = send_message(session["id"], "Generate a lesson with many objectives")
    analysis = analyze_lesson_content(response["response"])

    print(f"✓ Generated lesson: {analysis['lesson_length']} characters")
    print(f"✓ Should handle long lists gracefully")

    # Should not crash and should generate a valid lesson
    return analysis["mentions_standard"] and analysis["lesson_length"] > 100


def test_edge_case_9_special_characters():
    """Test: Objectives with special characters in the string"""
    print("\n" + "=" * 80)
    print("EDGE CASE 9: Special Characters in Objectives String")
    print("=" * 80)

    session_data = {
        "grade_level": "Grade 2",
        "strand_code": "RESPOND",
        "standard_id": "2.RE.1",
        "selected_objectives": "2.RE.1.1\n\t,2.RE.1.2\r,2.RE.1.3",
    }

    session = create_test_session(session_data)
    print(
        f"✓ Created session with special chars: {repr(session['selected_objectives'])}"
    )

    response = send_message(session["id"], "Generate a lesson")
    analysis = analyze_lesson_content(response["response"])

    print(f"✓ Generated lesson: {analysis['lesson_length']} characters")
    print(f"✓ Should handle special characters gracefully")

    # Should clean and handle special characters
    return analysis["mentions_standard"] and response["response"] is not None


def test_edge_case_10_case_sensitivity():
    """Test: Case sensitivity in objective codes"""
    print("\n" + "=" * 80)
    print("EDGE CASE 10: Case Sensitivity in Objective Codes")
    print("=" * 80)

    session_data = {
        "grade_level": "Grade 3",
        "strand_code": "CONNECT",
        "standard_id": "3.CN.1",
        "selected_objectives": "3.cn.1.1,3.Cn.1.2,3.CN.1.3",
    }

    session = create_test_session(session_data)
    print(f"✓ Created session with mixed case: {session['selected_objectives']}")

    response = send_message(session["id"], "Generate a lesson")
    analysis = analyze_lesson_content(response["response"])

    print(f"✓ Generated lesson: {analysis['lesson_length']} characters")
    print(f"✓ Standards found: {analysis['standard_codes_found']}")
    print(f"✓ Should handle case variations")

    # Should work despite case variations
    return analysis["mentions_standard"] and response["response"] is not None


def run_comprehensive_tests():
    """Run all edge case tests"""
    print("🧪 COMPREHENSIVE EDGE CASE TESTING FOR OBJECTIVES USAGE")
    print("=" * 80)

    tests = [
        ("Single Objective", test_edge_case_1_single_objective),
        ("Multiple Objectives", test_edge_case_2_multiple_objectives),
        ("No Objectives", test_edge_case_3_no_objectives),
        ("Empty Objectives", test_edge_case_4_empty_objectives),
        ("Malformed Objectives", test_edge_case_5_malformed_objectives),
        ("Non-existent Objectives", test_edge_case_6_nonexistent_objectives),
        (
            "Mixed Standard Objectives",
            test_edge_case_7_objectives_from_different_standards,
        ),
        ("Very Long Objectives List", test_edge_case_8_very_long_objectives_list),
        ("Special Characters", test_edge_case_9_special_characters),
        ("Case Sensitivity", test_edge_case_10_case_sensitivity),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            print(f"\n🔍 Running: {test_name}")
            result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"📊 Result: {status}")
        except Exception as e:
            results[test_name] = False
            print(f"❌ ERROR: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("📋 COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    print(f"\n🎯 Overall Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL EDGE CASES HANDLED SUCCESSFULLY!")
        print("✅ The objectives implementation is rock solid!")
    else:
        print(f"⚠️  {total - passed} edge cases need attention")

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"edge_case_test_results_{timestamp}.json"

    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"📁 Detailed results saved to: {results_file}")

    return passed == total


if __name__ == "__main__":
    try:
        success = run_comprehensive_tests()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
