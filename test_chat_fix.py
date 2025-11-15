#!/usr/bin/env python3
"""Test the chat fix for Standard serialization"""

import requests
import json
import sqlite3

BASE_URL = "http://localhost:8000"
DB_PATH = "data/pocket_musec.db"


def get_test_user_id():
    """Get the test user ID from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = 'test@example.com'")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def test_chat_with_standard():
    """Test sending a chat message after selecting a standard"""

    user_id = get_test_user_id()
    if not user_id:
        print("✗ Test user not found. Run create_test_user.py first.")
        return False

    print(f"Using test user ID: {user_id}")

    # 1. Create a session with a standard directly in the database
    print("1. Creating session with standard in database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    session_id = "test-session-" + str(hash("test"))[:8]
    cursor.execute(
        """
        DELETE FROM sessions WHERE id = ?
    """,
        (session_id,),
    )

    cursor.execute(
        """
        INSERT INTO sessions 
        (id, user_id, grade_level, strand_code, selected_standards, additional_context, lesson_duration, class_size, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """,
        (
            session_id,
            user_id,
            "Grade 3",
            "ML",
            "3.ML.1",
            "Test session",
            "45 minutes",
            "25",
        ),
    )

    conn.commit()
    conn.close()
    print(f"   ✓ Session created: {session_id}")

    # 2. Send a chat message using requests (simulating frontend)
    print("2. Sending chat message...")

    # We need to create a token for the user
    # For now, let's test the endpoint directly without auth

    # Create a mock token (this is a simplified approach for testing)
    import jwt
    from datetime import datetime, timedelta

    token = jwt.encode(
        {
            "sub": user_id,
            "email": "test@example.com",
            "exp": datetime.utcnow() + timedelta(hours=1),
        },
        "your-secret-key-here",  # This should match the key in the backend
        algorithm="HS256",
    )

    headers = {"Authorization": f"Bearer {token}"}

    chat_response = requests.post(
        f"{BASE_URL}/api/sessions/{session_id}/messages",
        headers=headers,
        json={"message": "Create a lesson plan for this standard"},
    )

    if chat_response.status_code != 200:
        print(f"   ✗ Chat failed with status {chat_response.status_code}")
        print(f"   Response: {chat_response.text}")

        # Check logs for the error
        print("\n   Checking logs for errors...")
        with open("logs/backend_server.log", "r") as f:
            lines = f.readlines()
            for line in lines[-20:]:
                if "ERROR" in line or "500" in line:
                    print(f"   {line.strip()}")

        return False

    print("   ✓ Chat message successful!")
    response_data = chat_response.json()
    print(f"   Response preview: {response_data['response'][:100]}...")

    # 3. Clean up
    print("3. Cleaning up...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    print("   ✓ Session deleted")

    return True


if __name__ == "__main__":
    try:
        success = test_chat_with_standard()
        if success:
            print("\n✓ TEST PASSED: Chat with standard works correctly!")
            exit(0)
        else:
            print("\n✗ TEST FAILED")
            exit(1)
    except Exception as e:
        print(f"\n✗ TEST FAILED with exception: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
