#!/usr/bin/env python3
"""Create a test user directly in the database"""

import sqlite3
import hashlib
import secrets
from datetime import datetime

DB_PATH = "data/pocket_musec.db"


def hash_password(password: str) -> str:
    """Hash password"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_test_user():
    """Create a test user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = "test@example.com"
    password = "password123"
    hashed_pw = hash_password(password)

    try:
        # Delete existing user if present
        cursor.execute("DELETE FROM users WHERE email = ?", (email,))

        # Insert new user
        cursor.execute(
            """
            INSERT INTO users (id, email, password_hash, full_name, role, processing_mode, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                secrets.token_urlsafe(16),
                email,
                hashed_pw,
                "Test User",
                "teacher",
                "cloud",
                1,
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()
        print(f"✓ Created test user: {email} / {password}")
        return True
    except Exception as e:
        print(f"✗ Error creating user: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    create_test_user()
