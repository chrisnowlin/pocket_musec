#!/usr/bin/env python3
"""
Test the sessions API endpoint directly
"""

import requests
import json


def test_sessions_api():
    """Test the sessions API endpoint"""

    print("=== Testing Sessions API ===")

    # Test the API endpoint
    try:
        response = requests.get(
            "http://localhost:8001/api/sessions",
            headers={"Authorization": "Bearer demo-token"},
            timeout=5,
        )

        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response type: {type(data)}")
            print(
                f"Number of sessions: {len(data) if isinstance(data, list) else 'Not a list'}"
            )

            if isinstance(data, list) and len(data) > 0:
                print("\nFirst session:")
                first_session = data[0]
                print(f"  ID: {first_session.get('id', 'N/A')}")
                print(f"  Grade: {first_session.get('grade_level', 'N/A')}")
                print(f"  Strand: {first_session.get('strand_code', 'N/A')}")
                print(f"  Created: {first_session.get('created_at', 'N/A')}")
                print(f"  Updated: {first_session.get('updated_at', 'N/A')}")
                print(
                    f"  Has History: {'Yes' if first_session.get('conversation_history') else 'No'}"
                )
            else:
                print("❌ No sessions returned or invalid response format")
        else:
            print(f"❌ API Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Error text: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection error - backend may not be running")
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    test_sessions_api()
