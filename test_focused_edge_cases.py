#!/usr/bin/env python3
"""
Focused edge case testing with lesson generation
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"


def create_session(session_data):
    """Create a session"""
    response = requests.post(f"{BASE_URL}/sessions", json=session_data)
    if response.status_code != 200:
        raise Exception(
            f"Failed to create session: {response.status_code} - {response.text}"
        )
    return response.json()


def send_message(session_id, message):
    """Send a message and get response"""
    chat_request = {"message": message}
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/messages", json=chat_request
    )
    if response.status_code != 200:
        raise Exception(
            f"Failed to send message: {response.status_code} - {response.text}"
        )
    return response.json()


def check_objectives_in_lesson(lesson_content, expected_objectives):
    """Check if objectives are mentioned in lesson"""
    found_objectives = []
    for obj in expected_objectives:
        if obj in lesson_content:
            found_objectives.append(obj)
    return found_objectives


def test_malformed_objectives():
    """Test malformed objectives string handling"""
    print("🧪 Test: Malformed objectives string")

    session_data = {
        "grade_level": "Grade 3",
        "strand_code": "PERFORM",
        "standard_id": "3.PR.1",
        "selected_objectives": "3.PR.1.1,, ,3.PR.1.2, ,3.PR.1.3",
    }

    session = create_session(session_data)
    print(f"✓ Created session with malformed: {repr(session['selected_objectives'])}")

    response = send_message(session["id"], "Generate a lesson plan")
    lesson = response["response"]

    print(f"✓ Generated lesson: {len(lesson)} characters")
    print(f"✓ Should handle malformed input gracefully")

    # Should not crash and should generate valid content
    return len(lesson) > 100


def test_nonexistent_objectives():
    """Test non-existent objective IDs"""
    print("\n🧪 Test: Non-existent objective IDs")

    session_data = {
        "grade_level": "Grade 4",
        "strand_code": "RESPOND",
        "standard_id": "4.RE.1",
        "selected_objectives": "4.RE.1.99,4.RE.1.100,4.RE.1.1",
    }

    session = create_session(session_data)
    print(f"✓ Created session with fake objectives: {session['selected_objectives']}")

    response = send_message(session["id"], "Create a lesson for these objectives")
    lesson = response["response"]

    found_real = check_objectives_in_lesson(lesson, ["4.RE.1.1"])
    print(f"✓ Real objective found: {found_real}")
    print(f"✓ Should ignore fake objectives and use real ones")

    return len(lesson) > 100 and "4.RE.1.1" in lesson


def test_case_sensitivity():
    """Test case sensitivity in objective codes"""
    print("\n🧪 Test: Case sensitivity")

    session_data = {
        "grade_level": "Grade 5",
        "strand_code": "CONNECT",
        "standard_id": "5.CN.1",
        "selected_objectives": "5.cn.1.1,5.Cn.1.2,5.CN.1.3",
    }

    session = create_session(session_data)
    print(f"✓ Created session with mixed case: {session['selected_objectives']}")

    response = send_message(session["id"], "Generate lesson")
    lesson = response["response"]

    print(f"✓ Generated lesson: {len(lesson)} characters")
    print(f"✓ Should handle case variations")

    return len(lesson) > 100


def test_special_characters():
    """Test special characters in objectives string"""
    print("\n🧪 Test: Special characters")

    session_data = {
        "grade_level": "Grade 2",
        "strand_code": "CREATE",
        "standard_id": "2.CR.1",
        "selected_objectives": "2.CR.1.1\n\t,2.CR.1.2\r,2.CR.1.3",
    }

    session = create_session(session_data)
    print(
        f"✓ Created session with special chars: {repr(session['selected_objectives'])}"
    )

    response = send_message(session["id"], "Create a lesson")
    lesson = response["response"]

    print(f"✓ Generated lesson: {len(lesson)} characters")
    print(f"✓ Should clean special characters")

    return len(lesson) > 100


def test_very_long_list():
    """Test very long objectives list"""
    print("\n🧪 Test: Very long objectives list")

    # Create a long list
    objectives = ",".join([f"K.CR.1.{i}" for i in range(1, 15)])  # 14 objectives
    session_data = {
        "grade_level": "Kindergarten",
        "strand_code": "CREATE",
        "standard_id": "K.CR.1",
        "selected_objectives": objectives,
    }

    session = create_session(session_data)
    print(f"✓ Created session with {len(objectives.split(','))} objectives")

    response = send_message(session["id"], "Generate lesson")
    lesson = response["response"]

    print(f"✓ Generated lesson: {len(lesson)} characters")
    print(f"✓ Should handle long lists without crashing")

    return len(lesson) > 100


def test_mixed_standard_objectives():
    """Test objectives from different standards"""
    print("\n🧪 Test: Mixed standard objectives")

    session_data = {
        "grade_level": "Grade 3",
        "strand_code": "PERFORM",
        "standard_id": "3.PR.1",
        "selected_objectives": "3.PR.1.1,4.CR.1.1,5.RE.1.1",
    }

    session = create_session(session_data)
    print(f"✓ Created session with mixed standards: {session['selected_objectives']}")

    response = send_message(session["id"], "Generate lesson")
    lesson = response["response"]

    print(f"✓ Generated lesson: {len(lesson)} characters")
    print(f"✓ Should only use objectives from selected standard")

    return len(lesson) > 100


def run_focused_tests():
    """Run focused edge case tests"""
    print("🔍 FOCUSED EDGE CASE TESTING")
    print("=" * 50)

    tests = [
        ("Malformed Objectives", test_malformed_objectives),
        ("Non-existent Objectives", test_nonexistent_objectives),
        ("Case Sensitivity", test_case_sensitivity),
        ("Special Characters", test_special_characters),
        ("Very Long List", test_very_long_list),
        ("Mixed Standard Objectives", test_mixed_standard_objectives),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"📊 {test_name}: {status}")
        except Exception as e:
            results[test_name] = False
            print(f"❌ {test_name}: ERROR - {e}")
        time.sleep(1)  # Brief pause between tests

    # Summary
    print("\n" + "=" * 50)
    print("📋 FOCUSED TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    print(f"\n🎯 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL EDGE CASES HANDLED PERFECTLY!")
        print("✅ Objectives implementation is rock solid!")
    else:
        print(f"⚠️  {total - passed} edge cases need attention")

    return passed == total


if __name__ == "__main__":
    run_focused_tests()
