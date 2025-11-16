"""Unified database migrations for pocket_musec

Manages schema versioning and migrations for both core and extended functionality
"""

import sqlite3
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database schema migrations for all PocketMusec functionality"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection"""
        return sqlite3.connect(self.db_path)

    def get_schema_version(self) -> int:
        """Get current schema version"""
        conn = self.get_connection()
        try:
            # Create schema_version table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor = conn.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0
        finally:
            conn.close()

    def set_schema_version(self, version: int) -> None:
        """Set schema version after migration"""
        conn = self.get_connection()
        try:
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
            conn.commit()
            logger.info(f"Schema upgraded to version {version}")
        finally:
            conn.close()

    def migrate(self) -> None:
        """Run all necessary migrations"""
        current_version = self.get_schema_version()

        # Run migrations in order
        if current_version < 9:
            self.migrate_to_v9_model_selection()

        if current_version < 10:
            self.migrate_to_v10_lessons_and_presentations()

        logger.info(
            f"All migrations completed. Current version: {self.get_schema_version()}"
        )

    def migrate_to_v9_model_selection(self) -> None:
        """
        Migrate to version 9: Add model selection support

        Adds:
        - selected_model: Store selected AI model for cloud mode sessions
        """
        current_version = self.get_schema_version()

        if current_version >= 9:
            logger.info(
                f"Database already at version {current_version}, skipping v9 migration"
            )
            return

        logger.info("Starting migration to version 9: Add model selection support")

        conn = self.get_connection()
        try:
            # Add selected_model column to sessions table
            conn.execute("""
                ALTER TABLE sessions 
                ADD COLUMN selected_model TEXT
            """)

            conn.commit()

            # Update schema version
            self.set_schema_version(9)

            logger.info(
                "Version 9 migration (model selection support) completed successfully"
            )

        except Exception as e:
            conn.rollback()
            logger.error(f"Migration v9 failed: {e}")
            raise
        finally:
            conn.close()

    def migrate_to_v10_lessons_and_presentations(self) -> None:
        """
        Migrate to version 10: Add lessons and presentations tables

        Adds:
        - lessons table for storing lesson documents with m2.0 schema support
        - presentations table for storing generated slide decks
        """
        current_version = self.get_schema_version()

        if current_version >= 10:
            logger.info(
                f"Database already at version {current_version}, skipping v10 migration"
            )
            return

        logger.info(
            "Starting migration to version 10: Add lessons and presentations tables"
        )

        conn = self.get_connection()
        try:
            # Create lessons table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lessons (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    processing_mode TEXT DEFAULT 'cloud',
                    is_draft INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Create presentations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS presentations (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL,
                    lesson_revision INTEGER NOT NULL,
                    version TEXT DEFAULT 'p1.0',
                    status TEXT DEFAULT 'pending',
                    style TEXT DEFAULT 'default',
                    slides TEXT NOT NULL,  -- JSON serialized slide data
                    export_assets TEXT,   -- JSON serialized export metadata
                    error_code TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
                )
            """)

            # Create indexes for presentations table
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_presentations_lesson_revision 
                ON presentations(lesson_id, lesson_revision)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_presentations_status 
                ON presentations(status)
            """)

            # Create unique constraint to ensure only one active presentation per lesson revision
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_presentations_unique_active 
                ON presentations(lesson_id, lesson_revision) 
                WHERE status IN ('complete', 'pending')
            """)

            conn.commit()

            # Update schema version
            self.set_schema_version(10)

            logger.info(
                "Version 10 migration (lessons and presentations tables) completed successfully"
            )

        except Exception as e:
            conn.rollback()
            logger.error(f"Migration v10 failed: {e}")
            raise
        finally:
            conn.close()


# Convenience functions
def run_migration_v9(db_path: str) -> None:
    """Convenience function to run v9 migration"""
    migrator = MigrationManager(db_path)
    migrator.migrate_to_v9_model_selection()


def run_migration_v10(db_path: str) -> None:
    """Convenience function to run v10 migration"""
    migrator = MigrationManager(db_path)
    migrator.migrate_to_v10_lessons_and_presentations()
