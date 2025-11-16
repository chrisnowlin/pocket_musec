#!/usr/bin/env python3
"""
Debug script to check time formatting issues
"""

import requests
import json
from datetime import datetime


def debug_time_formatting():
    """Debug the time formatting issues"""

    print("🔍 DEBUG: Time Formatting Issues")
    print("=" * 40)

    # Get sessions from API
    try:
        response = requests.get("http://localhost:8000/api/sessions")
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return

        sessions = response.json()
        print(f"📊 Analyzing {len(sessions)} sessions\n")

        # Check first 5 sessions in detail
        for i, session in enumerate(sessions[:5], 1):
            print(f"Session {i}: {session['id']}")

            # Check created_at
            created_at = session.get("created_at")
            updated_at = session.get("updated_at")

            print(f"  created_at: {created_at}")
            print(f"  updated_at: {updated_at}")

            # Test if these dates are valid
            try:
                if created_at:
                    created_dt = datetime.fromisoformat(
                        created_at.replace("Z", "+00:00")
                    )
                    print(f"  ✅ created_at valid: {created_dt}")
                else:
                    print(f"  ❌ created_at is None/empty")

                if updated_at:
                    updated_dt = datetime.fromisoformat(
                        updated_at.replace("Z", "+00:00")
                    )
                    print(f"  ✅ updated_at valid: {updated_dt}")
                else:
                    print(f"  ❌ updated_at is None/empty")

            except Exception as e:
                print(f"  ❌ Date parsing error: {e}")

            # Check conversation history
            history = session.get("conversation_history")
            if history:
                try:
                    parsed = (
                        json.loads(history) if isinstance(history, str) else history
                    )
                    print(f"  📝 History has {len(parsed)} messages")
                except:
                    print(f"  ❌ History parsing failed")
            else:
                print(f"  📝 No history")

            print()

        # Test JavaScript Date parsing simulation
        print("🧪 Testing JavaScript Date parsing simulation:")

        test_dates = [
            "2025-11-13T20:53:03.887904",
            "2025-11-13T20:53:03.887904Z",
            None,
            "",
            "invalid-date",
        ]

        for test_date in test_dates:
            print(f"  Testing: {test_date}")
            if test_date:
                try:
                    # Simulate JavaScript new Date() behavior
                    dt = datetime.fromisoformat(test_date.replace("Z", "+00:00"))
                    print(f"    ✅ Valid: {dt}")
                except Exception as e:
                    print(f"    ❌ Invalid: {e}")
            else:
                print(f"    ❌ None/empty")

    except Exception as e:
        print(f"❌ Request failed: {e}")


if __name__ == "__main__":
    debug_time_formatting()
