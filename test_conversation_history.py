#!/usr/bin/env python3
"""
Test script to diagnose conversation history persistence issues
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def test_conversation_history_persistence():
    """Test conversation history loading and saving"""

    db_path = "data/pocket_musec.db"

    print("=== Conversation History Persistence Test ===")
    print(f"Database: {db_path}")

    # Check database exists
    if not Path(db_path).exists():
        print("❌ Database not found")
        return

    conn = sqlite3.connect(db_path)

    try:
        # Check sessions table structure
        cursor = conn.execute("PRAGMA table_info(sessions)")
        columns = cursor.fetchall()
        print("\n📋 Sessions table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        # Check conversation_history column specifically
        cursor = conn.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = cursor.fetchone()[0]

        cursor = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE conversation_history IS NOT NULL"
        )
        sessions_with_history = cursor.fetchone()[0]

        cursor = conn.execute(
            "SELECT AVG(LENGTH(conversation_history)) FROM sessions WHERE conversation_history IS NOT NULL"
        )
        avg_length = cursor.fetchone()[0]

        print(f"\n📊 Statistics:")
        print(f"  Total sessions: {total_sessions}")
        print(f"  Sessions with history: {sessions_with_history}")
        print(f"  Average history length: {avg_length or 0:.0f} characters")

        # Show sample conversation history
        cursor = conn.execute("""
            SELECT id, grade_level, length(conversation_history) as history_len, conversation_history
            FROM sessions 
            WHERE conversation_history IS NOT NULL 
            ORDER BY updated_at DESC 
            LIMIT 3
        """)

        print(f"\n📝 Sample conversation history:")
        for row in cursor.fetchall():
            session_id, grade_level, history_len, history_json = row
            print(f"\n  Session: {session_id[:8]}...")
            print(f"  Grade: {grade_level}")
            print(f"  History length: {history_len} chars")

            try:
                history = json.loads(history_json)
                print(f"  Messages: {len(history)}")
                if history:
                    last_msg = history[-1]
                    print(
                        f"  Last message: {last_msg.get('role', 'unknown')}: {last_msg.get('content', '')[:100]}..."
                    )
            except json.JSONDecodeError as e:
                print(f"  ❌ Invalid JSON: {e}")

        # Test conversation history loading mechanism
        print(f"\n🔧 Testing loading mechanism...")

        # Test conversation history loading mechanism
        print(f"  🔧 Testing conversation history loading...")

        # Import the session repository to test
        try:
            import sys

            sys.path.append("backend")
            from backend.repositories.session_repository import SessionRepository

            session_repo = SessionRepository()

            # Get a session with history
            cursor = conn.execute("""
                SELECT id FROM sessions 
                WHERE conversation_history IS NOT NULL 
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()

            if row:
                session_id = row[0]
                print(f"  Testing session: {session_id[:8]}...")

                # Test loading conversation history
                session = session_repo.get_session(session_id)
                if session and session.conversation_history:
                    try:
                        history = json.loads(session.conversation_history)
                        print(f"  ✅ Loaded {len(history)} messages from session")
                        print(f"  ✅ JSON parsing successful")

                        # Show message structure
                        if history:
                            last_msg = history[-1]
                            print(
                                f"  ✅ Last message structure: {list(last_msg.keys())}"
                            )

                    except json.JSONDecodeError as e:
                        print(f"  ❌ Failed to parse conversation history: {e}")
                else:
                    print(f"  ❌ No conversation history found in session")
            else:
                print(f"  ❌ No sessions with conversation history found")

        except ImportError as e:
            print(f"  ❌ Failed to import required modules: {e}")

    finally:
        conn.close()


def test_recent_activity():
    """Check if conversation history is being saved recently"""

    db_path = "data/pocket_musec.db"

    print(f"\n=== Recent Activity Test ===")

    conn = sqlite3.connect(db_path)

    try:
        # Check recent sessions
        cursor = conn.execute("""
            SELECT id, grade_level, created_at, updated_at, 
                   conversation_history IS NOT NULL as has_history,
                   length(conversation_history) as history_len
            FROM sessions 
            ORDER BY updated_at DESC 
            LIMIT 10
        """)

        print("Recent sessions:")
        for row in cursor.fetchall():
            (
                session_id,
                grade_level,
                created_at,
                updated_at,
                has_history,
                history_len,
            ) = row
            print(
                f"  {session_id[:8]}... | {grade_level} | {updated_at} | History: {'✅' if has_history else '❌'} ({history_len or 0} chars)"
            )

        # Check if there are any very recent updates (last hour)
        cursor = conn.execute("""
            SELECT COUNT(*) FROM sessions 
            WHERE updated_at > datetime('now', '-1 hour')
        """)
        recent_count = cursor.fetchone()[0]

        print(f"\nSessions updated in last hour: {recent_count}")

    finally:
        conn.close()


if __name__ == "__main__":
    test_conversation_history_persistence()
    test_recent_activity()
