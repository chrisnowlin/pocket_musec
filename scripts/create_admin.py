#!/usr/bin/env python3
"""
Create an admin user for PocketMusec.

Usage:
    python scripts/create_admin.py

Interactive script to create a new admin user account.
"""

import getpass
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.auth.user_repository import UserRepository
from backend.auth.models import UserRole, ProcessingMode


def main():
    print("=" * 60)
    print("PocketMusec - Create Admin User")
    print("=" * 60)
    print()

    # Get database path
    db_path = input("Database path [./data/pocket_musec.db]: ").strip()
    if not db_path:
        db_path = "./data/pocket_musec.db"

    # Create repository
    try:
        repo = UserRepository(db_path)
    except Exception as e:
        print(f"\n❌ Error: Failed to connect to database: {e}")
        print("\nMake sure the database exists and migrations have been run:")
        print("  python -c \"from backend.repositories.migrations import DatabaseMigrator; m = DatabaseMigrator('./data/pocket_musec.db'); m.migrate()\"")
        sys.exit(1)

    print()
    print("Enter details for the new admin user:")
    print()

    # Get user details
    email = input("Email address: ").strip()
    if not email or '@' not in email:
        print("\n❌ Error: Invalid email address")
        sys.exit(1)

    # Check if user already exists
    existing_user = repo.get_user_by_email(email)
    if existing_user:
        print(f"\n❌ Error: User with email '{email}' already exists")
        sys.exit(1)

    full_name = input("Full name: ").strip()
    if not full_name:
        full_name = email.split('@')[0]

    # Get password securely
    while True:
        password = getpass.getpass("Password (min 8 chars): ")
        if len(password) < 8:
            print("❌ Password must be at least 8 characters. Try again.")
            continue

        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("❌ Passwords do not match. Try again.")
            continue

        break

    # Processing mode
    print()
    print("Processing mode:")
    print("  1. Cloud (default - uses Chutes API)")
    print("  2. Local (uses Ollama)")
    mode_choice = input("Select mode [1]: ").strip()

    if mode_choice == "2":
        processing_mode = ProcessingMode.LOCAL
    else:
        processing_mode = ProcessingMode.CLOUD

    # Create user
    print()
    print("Creating admin user...")

    try:
        user = repo.create_user(
            email=email,
            password=password,
            role=UserRole.ADMIN,
            full_name=full_name,
            processing_mode=processing_mode
        )

        print()
        print("=" * 60)
        print("✅ Admin user created successfully!")
        print("=" * 60)
        print()
        print(f"Email:          {user.email}")
        print(f"Name:           {user.full_name}")
        print(f"Role:           {user.role.value}")
        print(f"Processing:     {user.processing_mode.value}")
        print(f"Created:        {user.created_at}")
        print()
        print("You can now log in to PocketMusec with these credentials.")
        print()

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: Failed to create user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
