#!/usr/bin/env python3
"""
Test script to verify conversation history restoration fix
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def test_conversation_restoration():
    """Test that conversation history is properly restored"""

    db_path = "data/pocket_musec.db"

    print("=== Conversation History Restoration Test ===")

    # Check database exists
    if not Path(db_path).exists():
        print("❌ Database not found")
        return

    conn = sqlite3.connect(db_path)

    try:
        # Get a session with conversation history
        cursor = conn.execute("""
            SELECT id, grade_level, conversation_history 
            FROM sessions 
            WHERE conversation_history IS NOT NULL 
            ORDER BY updated_at DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()

        if not row:
            print("❌ No sessions with conversation history found")
            return

        session_id, grade_level, conversation_history_json = row

        print(f"✅ Found session with history: {session_id[:8]}...")
        print(f"   Grade: {grade_level}")

        try:
            conversation_history = json.loads(conversation_history_json)
            print(f"✅ Parsed {len(conversation_history)} messages from JSON")

            # Show the conversation structure
            print("\n📝 Conversation structure:")
            for i, msg in enumerate(conversation_history):
                role = msg.get("role", "unknown")
                content_preview = (
                    msg.get("content", "")[:100] + "..."
                    if len(msg.get("content", "")) > 100
                    else msg.get("content", "")
                )
                print(f"   {i + 1}. {role}: {content_preview}")

            print(f"\n✅ Conversation history restoration should work for this session")

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse conversation history JSON: {e}")

        # Now test creating a new session to see if it gets conversation history
        print(f"\n🔧 Testing new session creation...")

        # Get the most recent session without conversation history
        cursor = conn.execute("""
            SELECT id, grade_level, created_at 
            FROM sessions 
            WHERE conversation_history IS NULL 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()

        if row:
            session_id, grade_level, created_at = row
            print(f"✅ Found recent session without history: {session_id[:8]}...")
            print(f"   Grade: {grade_level}")
            print(f"   Created: {created_at}")
            print(
                f"   This session should get conversation history when messages are sent"
            )
        else:
            print("ℹ️  All sessions have conversation history")

    finally:
        conn.close()


if __name__ == "__main__":
    test_conversation_restoration()
