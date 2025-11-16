#!/usr/bin/env python3
"""
Test script for additional standards and objectives functionality
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"


def test_additional_standards_objectives():
    """Test creating a session with additional standards and objectives"""

    print("Testing additional standards and objectives functionality...")

    # Test data
    session_data = {
        "grade_level": "Grade 3",
        "strand_code": "Connect",
        "standard_id": "3.CN.1",
        "selected_objectives": "3.CN.1.1,3.CN.1.2",
        "additional_standards": "3.CN.2,3.CN.3",
        "additional_objectives": "3.CN.2.1,3.CN.3.1",
        "additional_context": "Test lesson with additional standards and objectives",
    }

    try:
        # Create session
        print("1. Creating session with additional standards and objectives...")
        response = requests.post(f"{BASE_URL}/api/sessions", json=session_data)

        if response.status_code == 200:
            session = response.json()
            session_id = session["id"]
            print(f"✓ Session created successfully: {session_id}")

            # Verify the additional fields are stored
            print("2. Verifying additional fields in session...")
            if session.get("additional_standards") == "3.CN.2,3.CN.3":
                print("✓ Additional standards stored correctly")
            else:
                print(
                    f"✗ Additional standards mismatch: {session.get('additional_standards')}"
                )

            if session.get("additional_objectives") == "3.CN.2.1,3.CN.3.1":
                print("✓ Additional objectives stored correctly")
            else:
                print(
                    f"✗ Additional objectives mismatch: {session.get('additional_objectives')}"
                )

            # Get session to verify persistence
            print("3. Testing session retrieval...")
            get_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")

            if get_response.status_code == 200:
                retrieved_session = get_response.json()
                if retrieved_session.get("additional_standards") == "3.CN.2,3.CN.3":
                    print("✓ Additional standards persisted correctly")
                else:
                    print(
                        f"✗ Additional standards persistence failed: {retrieved_session.get('additional_standards')}"
                    )

                if (
                    retrieved_session.get("additional_objectives")
                    == "3.CN.2.1,3.CN.3.1"
                ):
                    print("✓ Additional objectives persisted correctly")
                else:
                    print(
                        f"✗ Additional objectives persistence failed: {retrieved_session.get('additional_objectives')}"
                    )
            else:
                print(f"✗ Failed to retrieve session: {get_response.status_code}")

            # Test lesson generation to ensure additional fields are used
            print("4. Testing lesson generation with additional fields...")
            chat_data = {
                "message": "Generate a lesson plan that includes the primary and additional standards"
            }

            chat_response = requests.post(
                f"{BASE_URL}/api/sessions/{session_id}/messages", json=chat_data
            )

            if chat_response.status_code == 200:
                chat_result = chat_response.json()
                lesson_content = chat_result.get("lesson", {}).get("content", "")

                # Check if lesson content mentions additional standards
                if "3.CN.2" in lesson_content or "3.CN.3" in lesson_content:
                    print("✓ Lesson generation includes additional standards")
                else:
                    print("✗ Lesson generation may not be using additional standards")

                if "3.CN.2.1" in lesson_content or "3.CN.3.1" in lesson_content:
                    print("✓ Lesson generation includes additional objectives")
                else:
                    print("✗ Lesson generation may not be using additional objectives")

                print(
                    f"✓ Lesson generated successfully ({len(lesson_content)} characters)"
                )
                print(f"Lesson content preview:\n{lesson_content[:300]}...")
            else:
                print(f"✗ Lesson generation failed: {chat_response.status_code}")
                print(f"Response: {chat_response.text}")

        else:
            print(f"✗ Failed to create session: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print(
            "✗ Cannot connect to API server. Make sure it's running on localhost:8000"
        )
    except Exception as e:
        print(f"✗ Test failed with error: {e}")


if __name__ == "__main__":
    test_additional_standards_objectives()
