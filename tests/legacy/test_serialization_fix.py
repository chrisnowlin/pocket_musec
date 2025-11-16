#!/usr/bin/env python3
"""Test the Standard serialization fix by directly testing the agent"""

import sys
import sqlite3

sys.path.insert(0, ".")

from backend.repositories.session_repository import SessionRepository
from backend.repositories.standards_repository import StandardsRepository
from backend.pocketflow.lesson_agent import LessonAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.api.routes.sessions import _create_lesson_agent, _standard_to_response
import json

DB_PATH = "data/pocket_musec.db"


def test_standard_serialization():
    """Test that Standard objects are properly serialized"""

    print("Testing Standard serialization fix...")

    # 1. Create a test session with a standard
    print("\n1. Creating test session...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get a test user
    cursor.execute("SELECT id FROM users LIMIT 1")
    user_result = cursor.fetchone()
    if not user_result:
        print("   ✗ No users found in database")
        return False
    user_id = user_result[0]

    session_id = "test-serial-" + str(hash("serial-test"))[:8]
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    cursor.execute(
        """
        INSERT INTO sessions 
        (id, user_id, grade_level, strand_code, selected_standards, agent_state, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """,
        (session_id, user_id, "Grade 1", "CN", "1.CN.1", "{}"),
    )

    conn.commit()
    conn.close()
    print(f"   ✓ Session created: {session_id}")

    # 2. Load the session and create an agent
    print("\n2. Creating lesson agent...")
    session_repo = SessionRepository()
    session = session_repo.get_session(session_id)

    if not session:
        print("   ✗ Failed to load session")
        return False

    print(f"   Session selected_standards: {session.selected_standards}")

    # Check if the standard exists
    standards_repo = StandardsRepository()
    standard = standards_repo.get_standard_by_id("1.CN.1")
    if not standard:
        print("   ✗ Standard '1.CN.1' not found in database")
        return False
    print(f"   ✓ Standard found: {standard.standard_id}")

    agent = _create_lesson_agent(session)
    print("   ✓ Agent created successfully")

    # 3. Check that the standard is serialized
    print("\n3. Checking standard serialization...")
    standard = agent.lesson_requirements.get("standard")

    if standard is None:
        print("   ✗ No standard in lesson_requirements")
        return False

    if isinstance(standard, dict):
        print(f"   ✓ Standard is a dict (serialized)")
        print(f"     Keys: {list(standard.keys())}")
    else:
        print(f"   ✗ Standard is not a dict: {type(standard)}")
        return False

    # 4. Try to serialize the agent state (this is where the bug occurred)
    print("\n4. Testing agent state serialization...")
    try:
        agent_state_json = agent.serialize_state()
        state_dict = json.loads(agent_state_json)
        print("   ✓ Agent state serialized successfully")

        # Check if the standard is in the serialized state
        if "lesson_requirements" in state_dict:
            if "standard" in state_dict["lesson_requirements"]:
                std = state_dict["lesson_requirements"]["standard"]
                if isinstance(std, dict):
                    print(f"   ✓ Standard in serialized state is a dict")
                else:
                    print(
                        f"   ✗ Standard in serialized state is not a dict: {type(std)}"
                    )
                    return False
    except TypeError as e:
        print(f"   ✗ Serialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 5. Clean up
    print("\n5. Cleaning up...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    print("   ✓ Test session deleted")

    return True


if __name__ == "__main__":
    try:
        success = test_standard_serialization()
        if success:
            print("\n✓ TEST PASSED: Standard serialization works correctly!")
            exit(0)
        else:
            print("\n✗ TEST FAILED")
            exit(1)
    except Exception as e:
        print(f"\n✗ TEST FAILED with exception: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
