#!/usr/bin/env python3
"""
Debug script to check recent chats logic
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def debug_recent_chats():
    """Debug the recent chats logic"""

    db_path = "data/pocket_musec.db"

    print("=== Recent Chats Debug ===")

    if not Path(db_path).exists():
        print("❌ Database not found")
        return

    conn = sqlite3.connect(db_path)

    try:
        # Get sessions with dates
        cursor = conn.execute("""
            SELECT id, grade_level, strand_code, created_at, updated_at
            FROM sessions 
            ORDER BY updated_at DESC 
            LIMIT 10
        """)

        sessions = cursor.fetchall()

        print(f"📊 Found {len(sessions)} sessions\n")

        # Simulate the frontend logic
        now = datetime.now()
        today = now.date()
        one_week_ago = datetime(now.year, now.month, now.day - 7)

        print(f"Current time: {now}")
        print(f"Today: {today}")
        print(f"One week ago: {one_week_ago}")
        print()

        today_sessions = []
        this_week_sessions = []
        older_sessions = []

        for i, session in enumerate(sessions, 1):
            session_id, grade_level, strand_code, created_at, updated_at = session

            print(f"{i}. Session: {session_id[:8]}...")
            print(f"   Created: {created_at}")
            print(f"   Updated: {updated_at}")

            # Parse dates like frontend does
            try:
                # Handle ISO format with timezone info
                if "T" in created_at:
                    # Remove timezone info for parsing if present
                    clean_created = created_at.split(".")[0].replace("Z", "")
                    created_date = datetime.fromisoformat(clean_created)
                else:
                    created_date = datetime.fromisoformat(created_at)

                if "T" in updated_at:
                    clean_updated = updated_at.split(".")[0].replace("Z", "")
                    updated_date = datetime.fromisoformat(clean_updated)
                else:
                    updated_date = datetime.fromisoformat(updated_at)

            except Exception as e:
                print(f"   ❌ Date parsing error: {e}")
                created_date = now
                updated_date = now

            print(f"   Parsed created: {created_date}")
            print(f"   Parsed updated: {updated_date}")
            print(f"   Created date only: {created_date.date()}")
            print(f"   Today date only: {today}")
            print(
                f"   created_date.toDateString() == today: {created_date.date() == today}"
            )
            print(f"   created_date >= one_week_ago: {created_date >= one_week_ago}")

            # Categorize like frontend does
            if created_date.date() == today:
                today_sessions.append(session)
                print(f"   📅 Category: TODAY")
            elif created_date >= one_week_ago:
                this_week_sessions.append(session)
                print(f"   📅 Category: THIS WEEK")
            else:
                older_sessions.append(session)
                print(f"   📅 Category: OLDER")

            print()

        print("=== Summary ===")
        print(f"Today sessions: {len(today_sessions)}")
        print(f"This week sessions: {len(this_week_sessions)}")
        print(f"Older sessions: {len(older_sessions)}")

        # Combine for recent chats
        all_recent = today_sessions + this_week_sessions
        print(f"All recent sessions: {len(all_recent)}")

        if len(all_recent) > 0:
            print("✅ Should show recent chats")
        else:
            print("❌ No recent chats to show")

    finally:
        conn.close()


if __name__ == "__main__":
    debug_recent_chats()
