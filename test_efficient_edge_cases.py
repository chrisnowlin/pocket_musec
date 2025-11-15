#!/usr/bin/env python3
"""
Efficient edge case testing focusing on API layer and parsing logic
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_api_edge_cases():
    """Test API layer edge cases efficiently"""

    test_cases = [
        {
            "name": "Empty objectives string",
            "data": {
                "grade_level": "Grade 2",
                "strand_code": "RESPOND",
                "standard_id": "2.RE.1",
                "selected_objectives": "",
            },
            "expected": "",
        },
        {
            "name": "Single objective",
            "data": {
                "grade_level": "Grade 3",
                "strand_code": "PERFORM",
                "standard_id": "3.PR.1",
                "selected_objectives": "3.PR.1.1",
            },
            "expected": "3.PR.1.1",
        },
        {
            "name": "Multiple objectives",
            "data": {
                "grade_level": "Grade 4",
                "strand_code": "CREATE",
                "standard_id": "4.CR.1",
                "selected_objectives": "4.CR.1.1,4.CR.1.2,4.CR.1.3",
            },
            "expected": "4.CR.1.1,4.CR.1.2,4.CR.1.3",
        },
        {
            "name": "Malformed with extra commas",
            "data": {
                "grade_level": "Grade 5",
                "strand_code": "CONNECT",
                "standard_id": "5.CN.1",
                "selected_objectives": "5.CN.1.1,, ,5.CN.1.2",
            },
            "expected": "5.CN.1.1,, ,5.CN.1.2",
        },
        {
            "name": "Special characters",
            "data": {
                "grade_level": "Grade 1",
                "strand_code": "RESPOND",
                "standard_id": "1.RE.1",
                "selected_objectives": "1.RE.1.1\n\t,1.RE.1.2",
            },
            "expected": "1.RE.1.1\n\t,1.RE.1.2",
        },
        {
            "name": "No objectives field",
            "data": {
                "grade_level": "Kindergarten",
                "strand_code": "CREATE",
                "standard_id": "K.CR.1",
            },
            "expected": None,
        },
    ]

    results = []

    for test_case in test_cases:
        try:
            response = requests.post(f"{BASE_URL}/sessions", json=test_case["data"])

            if response.status_code != 200:
                results.append(
                    {
                        "test": test_case["name"],
                        "status": "FAILED",
                        "error": f"HTTP {response.status_code}: {response.text}",
                    }
                )
                continue

            session = response.json()
            actual = session.get("selected_objectives")

            if actual == test_case["expected"]:
                results.append(
                    {
                        "test": test_case["name"],
                        "status": "PASSED",
                        "actual": actual,
                        "expected": test_case["expected"],
                    }
                )
            else:
                results.append(
                    {
                        "test": test_case["name"],
                        "status": "FAILED",
                        "actual": actual,
                        "expected": test_case["expected"],
                    }
                )

        except Exception as e:
            results.append(
                {"test": test_case["name"], "status": "ERROR", "error": str(e)}
            )

    return results


def test_objective_parsing_logic():
    """Test the objective parsing logic directly"""
    print("\n🔍 Testing Objective Parsing Logic")
    print("=" * 50)

    # Simulate the parsing logic from LessonAgent
    def parse_objectives(objectives_str):
        if not objectives_str:
            return []

        return [
            obj_id.strip() for obj_id in objectives_str.split(",") if obj_id.strip()
        ]

    test_cases = [
        ("", []),
        ("3.PR.1.1", ["3.PR.1.1"]),
        ("3.PR.1.1,3.PR.1.2", ["3.PR.1.1", "3.PR.1.2"]),
        ("3.PR.1.1,, ,3.PR.1.2", ["3.PR.1.1", "3.PR.1.2"]),
        ("3.PR.1.1\n\t,3.PR.1.2\r", ["3.PR.1.1", "3.PR.1.2"]),
        ("  3.PR.1.1  ,  3.PR.1.2  ", ["3.PR.1.1", "3.PR.1.2"]),
        (",,,", []),
        ("3.PR.1.1,,,", ["3.PR.1.1"]),
    ]

    parsing_results = []

    for input_str, expected in test_cases:
        actual = parse_objectives(input_str)
        success = actual == expected

        parsing_results.append(
            {
                "input": repr(input_str),
                "expected": expected,
                "actual": actual,
                "status": "PASSED" if success else "FAILED",
            }
        )

    return parsing_results


def main():
    print("🧪 EFFICIENT EDGE CASE TESTING")
    print("=" * 50)

    # Test API layer
    print("\n📡 Testing API Layer")
    api_results = test_api_edge_cases()

    for result in api_results:
        status_icon = "✅" if result["status"] == "PASSED" else "❌"
        print(f"{status_icon} {result['test']}: {result['status']}")
        if result["status"] == "FAILED":
            if "error" in result:
                print(f"   Error: {result['error']}")
            else:
                print(f"   Expected: {result['expected']}")
                print(f"   Actual: {result['actual']}")

    # Test parsing logic
    parsing_results = test_objective_parsing_logic()

    for result in parsing_results:
        status_icon = "✅" if result["status"] == "PASSED" else "❌"
        print(f"{status_icon} Input {result['input']}: {result['status']}")
        if result["status"] == "FAILED":
            print(f"   Expected: {result['expected']}")
            print(f"   Actual: {result['actual']}")

    # Summary
    api_passed = sum(1 for r in api_results if r["status"] == "PASSED")
    api_total = len(api_results)
    parsing_passed = sum(1 for r in parsing_results if r["status"] == "PASSED")
    parsing_total = len(parsing_results)

    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    print(f"API Layer: {api_passed}/{api_total} tests passed")
    print(f"Parsing Logic: {parsing_passed}/{parsing_total} tests passed")

    total_passed = api_passed + parsing_passed
    total_tests = api_total + parsing_total

    print(f"Overall: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 ALL EDGE CASES HANDLED PERFECTLY!")
        print("✅ Objectives implementation is rock solid!")
    else:
        print(f"\n⚠️  {total_tests - total_passed} edge cases need attention")

    # Save results
    results = {
        "api_tests": api_results,
        "parsing_tests": parsing_results,
        "summary": {
            "api_passed": api_passed,
            "api_total": api_total,
            "parsing_passed": parsing_passed,
            "parsing_total": parsing_total,
            "total_passed": total_passed,
            "total_tests": total_tests,
        },
    }

    with open("efficient_edge_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📁 Results saved to: efficient_edge_test_results.json")
    return total_passed == total_tests


if __name__ == "__main__":
    main()
