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

        if current_version < 11:
            self.migrate_to_v11_presentation_jobs()

        if current_version < 12:
            self.migrate_to_v12_styles_table()

        logger.info(
            f"All migrations completed. Current version: {self.get_schema_version()}"
        )

    def _ensure_table(self, conn: sqlite3.Connection, table_name: str, create_sql: str) -> None:
        """Create a table if it does not exist."""
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if cursor.fetchone() is None:
            conn.execute(create_sql)
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
            # Ensure sessions table exists before altering. Minimal schema for legacy tests.
            self._ensure_table(
                conn,
                "sessions",
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    grade_level TEXT,
                    strand_code TEXT,
                    selected_standards TEXT,
                    selected_objectives TEXT,
                    additional_context TEXT,
                    lesson_duration TEXT,
                    class_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

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

    def migrate_to_v11_presentation_jobs(self) -> None:
        """
        Migrate to version 11: Add presentation_jobs table for persistent job tracking

        Adds:
        - presentation_jobs table for database-backed job persistence
        - Enhanced job tracking with retries, errors, and priorities
        - Job recovery and monitoring capabilities
        """
        current_version = self.get_schema_version()

        if current_version >= 11:
            logger.info(
                f"Database already at version {current_version}, skipping v11 migration"
            )
            return

        logger.info("Starting migration to version 11: Add presentation_jobs table")

        conn = self.get_connection()
        try:
            # Create presentation_jobs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS presentation_jobs (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority TEXT NOT NULL DEFAULT 'normal',
                    progress INTEGER DEFAULT 0,
                    message TEXT DEFAULT '',
                    created_at TIMESTAMP NOT NULL,
                    started_at TIMESTAMP NULL,
                    completed_at TIMESTAMP NULL,
                    timeout_seconds INTEGER DEFAULT 30,
                    presentation_id TEXT NULL,
                    slide_count INTEGER NULL,
                    result_data TEXT NULL,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 2,
                    error_code TEXT NULL,
                    error_message TEXT NULL,
                    error_details TEXT NULL,
                    style TEXT DEFAULT 'default',
                    use_llm_polish INTEGER DEFAULT 1,
                    worker_id TEXT NULL,
                    queue_position INTEGER NULL,
                    processing_time_seconds REAL NULL,

                    -- Foreign keys
                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
                );
            """)

            # Create indexes for efficient job querying
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_status ON presentation_jobs(status)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_user_status ON presentation_jobs(user_id, status)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_created ON presentation_jobs(created_at)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_priority_status ON presentation_jobs(priority, status)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_lesson ON presentation_jobs(lesson_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_worker ON presentation_jobs(worker_id)
            """)

            # Create index for queue ordering
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_queue_order ON presentation_jobs(
                    priority, created_at
                ) WHERE status = 'pending'
            """)

            conn.commit()

            # Update schema version
            self.set_schema_version(11)

            logger.info(
                "Version 11 migration (presentation_jobs table) completed successfully"
            )

        except Exception as e:
            conn.rollback()
            logger.error(f"Migration v11 failed: {e}")
            raise
        finally:
            conn.close()

    def migrate_to_v12_styles_table(self) -> None:
        """
        Migrate to version 12: Add styles table for style configurations

        Adds:
        - styles table for storing custom and preset style configurations
        - Support for user-specific and public styles
        - JSON storage for colors, fonts, layout, and transition settings
        """
        current_version = self.get_schema_version()

        if current_version >= 12:
            logger.info(
                f"Database already at version {current_version}, skipping v12 migration"
            )
            return

        logger.info("Starting migration to version 12: Add styles table")

        conn = self.get_connection()
        try:
            # Create styles table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS styles (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    type TEXT NOT NULL,
                    user_id TEXT,
                    is_public INTEGER DEFAULT FALSE,
                    is_active INTEGER DEFAULT TRUE,
                    color_scheme TEXT DEFAULT 'default',
                    colors TEXT,
                    fonts TEXT,
                    layout TEXT,
                    transitions TEXT,
                    show_progress_indicator INTEGER DEFAULT TRUE,
                    show_slide_numbers INTEGER DEFAULT TRUE,
                    show_section_headers INTEGER DEFAULT TRUE,
                    use_animations INTEGER DEFAULT FALSE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Create indexes for styles table
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_styles_user_id ON styles(user_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_styles_type ON styles(type)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_styles_public ON styles(is_public, is_active)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_styles_name ON styles(name)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_styles_active ON styles(is_active)
            """)

            conn.commit()

            # Update schema version
            self.set_schema_version(12)

            logger.info(
                "Version 12 migration (styles table) completed successfully"
            )

        except Exception as e:
            conn.rollback()
            logger.error(f"Migration v12 failed: {e}")
            raise
        finally:
            conn.close()


class DatabaseMigrator(MigrationManager):
    """Backwards-compatible alias for legacy code/tests."""

    pass


# Convenience functions
def run_migration_v9(db_path: str) -> None:
    """Convenience function to run v9 migration"""
    migrator = MigrationManager(db_path)
    migrator.migrate_to_v9_model_selection()


def run_migration_v10(db_path: str) -> None:
    """Convenience function to run v10 migration"""
    migrator = MigrationManager(db_path)
    migrator.migrate_to_v10_lessons_and_presentations()


def run_migration_v11(db_path: str) -> None:
    """Convenience function to run v11 migration"""
    migrator = MigrationManager(db_path)
    migrator.migrate_to_v11_presentation_jobs()


def run_migration_v12(db_path: str) -> None:
    """Convenience function to run v12 migration"""
    migrator = MigrationManager(db_path)
    migrator.migrate_to_v12_styles_table()
