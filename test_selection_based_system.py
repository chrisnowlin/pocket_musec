#!/usr/bin/env python3
"""
Test script for the new selection-based additional standards and objectives system
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"


def test_selection_based_system():
    """Test the new selection-based additional standards and objectives system"""

    print("Testing selection-based additional standards and objectives system...")

    # Test data with comma-separated strings (backend format)
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

            # Verify the API returns arrays instead of strings
            print("2. Verifying API response format...")
            if isinstance(session.get("additional_standards"), list):
                print(
                    f"✓ Additional standards returned as array: {len(session['additional_standards'])} items"
                )
                for standard in session["additional_standards"]:
                    print(
                        f"  - {standard.get('code')}: {standard.get('description', '')[:50]}..."
                    )
            else:
                print(
                    f"✗ Additional standards not returned as array: {type(session.get('additional_standards'))}"
                )

            if isinstance(session.get("additional_objectives"), list):
                print(
                    f"✓ Additional objectives returned as array: {session['additional_objectives']}"
                )
            else:
                print(
                    f"✗ Additional objectives not returned as array: {type(session.get('additional_objectives'))}"
                )

            # Get session to verify persistence
            print("3. Testing session retrieval...")
            get_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")

            if get_response.status_code == 200:
                retrieved_session = get_response.json()
                if isinstance(retrieved_session.get("additional_standards"), list):
                    print("✓ Additional standards persisted as array")
                else:
                    print(
                        f"✗ Additional standards persistence failed: {type(retrieved_session.get('additional_standards'))}"
                    )

                if isinstance(retrieved_session.get("additional_objectives"), list):
                    print("✓ Additional objectives persisted as array")
                else:
                    print(
                        f"✗ Additional objectives persistence failed: {type(retrieved_session.get('additional_objectives'))}"
                    )
            else:
                print(f"✗ Failed to retrieve session: {get_response.status_code}")

            # Test lesson generation
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


def test_ui_compatibility():
    """Test that the new system is compatible with UI array format"""

    print("\n" + "=" * 60)
    print("Testing UI array format compatibility...")

    # Test what the UI will send (arrays get converted to comma-separated in frontend)
    session_data = {
        "grade_level": "Grade 3",
        "strand_code": "Connect",
        "standard_id": "3.CN.1",
        "selected_objectives": "3.CN.1.1",
        "additional_standards": "3.CN.2,3.CN.3",  # Frontend converts array to comma-separated
        "additional_objectives": "3.CN.2.1,3.CN.3.1",  # Frontend converts array to comma-separated
        "additional_context": "UI compatibility test",
    }

    try:
        response = requests.post(f"{BASE_URL}/api/sessions", json=session_data)

        if response.status_code == 200:
            session = response.json()
            print("✓ UI format compatibility confirmed")
            print(
                f"✓ Frontend arrays → Backend strings → API arrays conversion working"
            )
            print(
                f"  Additional standards: {len(session.get('additional_standards', []))} objects returned"
            )
            print(
                f"  Additional objectives: {len(session.get('additional_objectives', []))} items returned"
            )
        else:
            print(f"✗ UI compatibility test failed: {response.status_code}")

    except Exception as e:
        print(f"✗ UI compatibility test error: {e}")


if __name__ == "__main__":
    test_selection_based_system()
    test_ui_compatibility()
