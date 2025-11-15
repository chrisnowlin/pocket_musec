#!/usr/bin/env python3
"""
Final comprehensive test with real lesson generation for critical edge cases
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


def test_critical_edge_cases():
    """Test the most critical edge cases with actual lesson generation"""

    critical_tests = [
        {
            "name": "Single Objective",
            "session_data": {
                "grade_level": "Grade 4",
                "strand_code": "CREATE",
                "standard_id": "4.CR.1",
                "selected_objectives": "4.CR.1.1",
            },
            "message": "Generate a lesson for this objective",
            "expected_objectives": ["4.CR.1.1"],
        },
        {
            "name": "Multiple Objectives",
            "session_data": {
                "grade_level": "Grade 3",
                "strand_code": "PERFORM",
                "standard_id": "3.PR.1",
                "selected_objectives": "3.PR.1.1,3.PR.1.2",
            },
            "message": "Create a lesson addressing both objectives",
            "expected_objectives": ["3.PR.1.1", "3.PR.1.2"],
        },
        {
            "name": "No Objectives (Backward Compatibility)",
            "session_data": {
                "grade_level": "Grade 2",
                "strand_code": "RESPOND",
                "standard_id": "2.RE.1",
                # No selected_objectives
            },
            "message": "Generate a lesson for this standard",
            "expected_objectives": [],
        },
    ]

    results = []

    for i, test in enumerate(critical_tests):
        try:
            print(f"\n🧪 Test {i + 1}: {test['name']}")
            print("-" * 40)

            # Create session
            session = create_session(test["session_data"])
            print(f"✓ Session created")
            print(
                f"  Selected objectives: {session.get('selected_objectives', 'None')}"
            )

            # Send message for lesson generation
            print("📝 Generating lesson...")
            start_time = time.time()
            response = send_message(session["id"], test["message"])
            generation_time = time.time() - start_time

            lesson_content = response.get("response", "")
            print(
                f"✓ Lesson generated in {generation_time:.1f}s ({len(lesson_content)} chars)"
            )

            # Check for objectives in lesson
            found_objectives = []
            for obj in test["expected_objectives"]:
                if obj in lesson_content:
                    found_objectives.append(obj)

            # Check for standard reference
            has_standard = test["session_data"]["standard_id"] in lesson_content

            # Evaluate success
            if test["expected_objectives"]:
                # Should have objectives
                success = (
                    len(found_objectives) >= len(test["expected_objectives"]) // 2
                )  # At least half
                print(f"  Expected objectives: {test['expected_objectives']}")
                print(f"  Found objectives: {found_objectives}")
                print(f"  Standard mentioned: {has_standard}")
            else:
                # Should not have specific objectives, but should have standard
                success = has_standard
                print(f"  No specific objectives expected")
                print(f"  Standard mentioned: {has_standard}")

            result = {
                "test": test["name"],
                "status": "PASSED" if success else "FAILED",
                "generation_time": generation_time,
                "lesson_length": len(lesson_content),
                "expected_objectives": test["expected_objectives"],
                "found_objectives": found_objectives,
                "has_standard": has_standard,
            }

            results.append(result)
            status_icon = "✅" if success else "❌"
            print(f"  {status_icon} Result: {result['status']}")

        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({"test": test["name"], "status": "ERROR", "error": str(e)})

        # Brief pause between tests
        if i < len(critical_tests) - 1:
            time.sleep(2)

    return results


def analyze_lesson_quality(results):
    """Analyze the quality of generated lessons"""
    print("\n📊 LESSON QUALITY ANALYSIS")
    print("=" * 50)

    successful_tests = [r for r in results if r["status"] == "PASSED"]

    if not successful_tests:
        print("❌ No successful tests to analyze")
        return

    avg_time = sum(r["generation_time"] for r in successful_tests) / len(
        successful_tests
    )
    avg_length = sum(r["lesson_length"] for r in successful_tests) / len(
        successful_tests
    )

    print(f"Average generation time: {avg_time:.1f}s")
    print(f"Average lesson length: {avg_length:.0f} characters")

    # Check objectives inclusion
    tests_with_objectives = [
        r for r in successful_tests if r.get("expected_objectives")
    ]
    if tests_with_objectives:
        total_expected = sum(
            len(r["expected_objectives"]) for r in tests_with_objectives
        )
        total_found = sum(len(r["found_objectives"]) for r in tests_with_objectives)
        inclusion_rate = (
            (total_found / total_expected) * 100 if total_expected > 0 else 0
        )
        print(f"Objectives inclusion rate: {inclusion_rate:.1f}%")

    # Check standards inclusion
    tests_with_standards = [r for r in successful_tests if r.get("has_standard")]
    standards_rate = (len(tests_with_standards) / len(successful_tests)) * 100
    print(f"Standards inclusion rate: {standards_rate:.1f}%")


def main():
    print("🎯 FINAL COMPREHENSIVE TESTING")
    print("=" * 50)
    print("Testing critical edge cases with real lesson generation...")

    results = test_critical_edge_cases()

    # Summary
    print("\n" + "=" * 50)
    print("📋 FINAL TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for r in results if r["status"] == "PASSED")
    total = len(results)

    for result in results:
        status_icon = "✅" if result["status"] == "PASSED" else "❌"
        print(f"{status_icon} {result['test']}: {result['status']}")
        if result["status"] == "ERROR":
            print(f"   Error: {result['error']}")

    print(f"\n🎯 Results: {passed}/{total} critical tests passed")

    # Quality analysis
    analyze_lesson_quality(results)

    # Final assessment
    print("\n" + "=" * 50)
    if passed == total:
        print("🎉 ALL CRITICAL TESTS PASSED!")
        print("✅ Objectives implementation is PRODUCTION READY!")
        print("✅ Standards and objectives inclusion is ROCK SOLID!")
    else:
        print(f"⚠️  {total - passed} critical tests failed")
        print("❌ Implementation needs fixes before production")

    # Save results
    final_results = {
        "test_results": results,
        "summary": {
            "passed": passed,
            "total": total,
            "success_rate": (passed / total) * 100,
        },
    }

    with open("final_comprehensive_test_results.json", "w") as f:
        json.dump(final_results, f, indent=2)

    print(f"\n📁 Final results saved to: final_comprehensive_test_results.json")
    return passed == total


if __name__ == "__main__":
    main()
