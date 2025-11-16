#!/usr/bin/env python3
"""
Test script to verify recent chats display fix
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def test_recent_chats_data():
    """Test the data that will be displayed in recent chats"""

    db_path = "data/pocket_musec.db"

    print("=== Recent Chats Data Test ===")

    # Check database exists
    if not Path(db_path).exists():
        print("❌ Database not found")
        return

    conn = sqlite3.connect(db_path)

    try:
        # Get recent sessions with all relevant data
        cursor = conn.execute("""
            SELECT id, grade_level, strand_code, selected_standards, 
                   selected_objectives, additional_context, 
                   lesson_duration, class_size, created_at, updated_at,
                   conversation_history IS NOT NULL as has_history
            FROM sessions 
            ORDER BY updated_at DESC 
            LIMIT 10
        """)

        sessions = cursor.fetchall()

        print(f"📊 Found {len(sessions)} recent sessions\n")

        for i, session in enumerate(sessions, 1):
            (
                session_id,
                grade_level,
                strand_code,
                selected_standards,
                selected_objectives,
                additional_context,
                lesson_duration,
                class_size,
                created_at,
                updated_at,
                has_history,
            ) = session

            print(f"{i}. Session: {session_id[:8]}...")
            print(f"   Grade: {grade_level or 'None'}")
            print(f"   Strand: {strand_code or 'None'}")
            print(f"   Standard: {selected_standards or 'None'}")
            print(f"   Objectives: {selected_objectives or 'None'}")
            print(f"   Context: {'Yes' if additional_context else 'None'}")
            print(f"   Duration: {lesson_duration or 'None'}")
            print(f"   Class Size: {class_size or 'None'}")
            print(f"   Has History: {'Yes' if has_history else 'No'}")
            print(f"   Updated: {updated_at}")

            # Generate what the new title should be
            title = "New Conversation"
            if grade_level:
                if strand_code and strand_code != "All Strands":
                    title = f"{grade_level} · {strand_code}"
                else:
                    title = grade_level

            if selected_standards:
                title += f" · {selected_standards}"

            if additional_context and additional_context.strip():
                title += " 📝"

            print(f"   🎯 New Title: {title}")

            # Generate what the new hint should be
            updated_date = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            now = datetime.now()
            diff_minutes = (now - updated_date).total_seconds() / 60

            if diff_minutes < 1:
                time_str = "Just now"
            elif diff_minutes < 60:
                time_str = f"{int(diff_minutes)} minute{'s' if int(diff_minutes) != 1 else ''} ago"
            elif diff_minutes < 1440:  # 24 hours
                hours = int(diff_minutes / 60)
                time_str = f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = int(diff_minutes / 1440)
                if days == 1:
                    time_str = "Yesterday"
                else:
                    time_str = f"{days} days ago"

            # Add indicators
            indicators = []
            if selected_standards:
                indicators.append("📋")
            if additional_context and additional_context.strip():
                indicators.append("📝")
            if lesson_duration:
                indicators.append("⏱️")
            if class_size:
                indicators.append("👥")

            if indicators:
                time_str += f" · {' '.join(indicators)}"

            print(f"   💡 New Hint: {time_str}")
            print()

    finally:
        conn.close()


def test_title_generation():
    """Test various title generation scenarios"""

    print("=== Title Generation Test ===")

    test_cases = [
        {
            "grade_level": "Grade 3",
            "strand_code": "Connect",
            "selected_standards": None,
            "additional_context": None,
        },
        {
            "grade_level": "All Grades",
            "strand_code": "All Strands",
            "selected_standards": None,
            "additional_context": "Class has recorders",
        },
        {
            "grade_level": "Grade 2",
            "strand_code": "Create",
            "selected_standards": "2.CR.1",
            "additional_context": None,
        },
        {
            "grade_level": "Grade 5",
            "strand_code": "Perform",
            "selected_standards": "5.P.1.2",
            "additional_context": "Focus on rhythm patterns",
        },
        {
            "grade_level": None,
            "strand_code": None,
            "selected_standards": None,
            "additional_context": None,
        },
    ]

    for i, case in enumerate(test_cases, 1):
        grade = case["grade_level"]
        strand = case["strand_code"]
        standard = case["selected_standards"]
        context = case["additional_context"]

        # Generate title using new logic
        title = "New Conversation"

        if grade:
            if strand and strand != "All Strands":
                title = f"{grade} · {strand}"
            else:
                title = grade

        if standard:
            title += f" · {standard}"

        if context and context.strip():
            title += " 📝"

        print(f"{i}. {title}")

        # Show what it would have been before
        old_title = (
            grade
            and strand
            and strand != "All Strands"
            and f"{grade} · {strand} Strand"
            or (grade or "Unknown Session")
        )
        print(f"   Before: {old_title}")
        print()


if __name__ == "__main__":
    test_recent_chats_data()
    test_title_generation()
