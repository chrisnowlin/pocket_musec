"""Database migrations for pocket_musec

Manages schema versioning and migrations
"""

import sqlite3
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database schema migrations"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)

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

    def migrate_to_milestone3(self) -> None:
        """
        Migrate database to Milestone 3 schema

        Adds:
        - users table for authentication
        - sessions table for lesson generation sessions
        - lessons table for saved lessons
        - images table for image ingestion
        - citations table for source tracking
        - User foreign keys to existing tables
        """
        current_version = self.get_schema_version()

        if current_version >= 3:
            logger.info(
                f"Database already at version {current_version}, skipping M3 migration"
            )
            return

        logger.info("Starting Milestone 3 database migration...")

        conn = self.get_connection()
        try:
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")

            # Create users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    role TEXT NOT NULL DEFAULT 'teacher',
                    processing_mode TEXT DEFAULT 'cloud',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    CHECK (role IN ('teacher', 'admin')),
                    CHECK (processing_mode IN ('cloud', 'local'))
                )
            """)

            # Create sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    grade_level TEXT,
                    strand_code TEXT,
                    selected_standards TEXT,
                    selected_objectives TEXT,
                    additional_context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Create images table for image ingestion
            conn.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    mime_type TEXT NOT NULL,
                    extracted_text TEXT,
                    vision_summary TEXT,
                    ocr_confidence REAL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Create citations table for source tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS citations (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    source_title TEXT NOT NULL,
                    page_number INTEGER,
                    excerpt TEXT,
                    citation_text TEXT NOT NULL,
                    citation_number INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
                    CHECK (source_type IN ('standard', 'objective', 'document', 'image'))
                )
            """)

            # Create refresh_tokens table for JWT token management
            conn.execute("""
                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    revoked INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_lessons_user ON lessons(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_lessons_session ON lessons(session_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_images_user ON images(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_citations_lesson ON citations(lesson_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_citations_source ON citations(source_type, source_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash)"
            )

            conn.commit()

            # Update schema version
            self.set_schema_version(3)

            logger.info("Milestone 3 migration completed successfully")

        except Exception as e:
            conn.rollback()
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            conn.close()

    def migrate_to_v4_session_persistence(self) -> None:
        """
        Migrate to version 4: Add session persistence columns

        Adds:
        - agent_state: JSON column to store serialized agent state
        - conversation_history: JSON column to store chat history
        - current_state: Current conversation state
        """
        current_version = self.get_schema_version()

        if current_version >= 4:
            logger.info(
                f"Database already at version {current_version}, skipping v4 migration"
            )
            return

        logger.info("Starting version 4 database migration (session persistence)...")

        conn = self.get_connection()
        try:
            # Add new columns to sessions table
            try:
                conn.execute("""
                    ALTER TABLE sessions 
                    ADD COLUMN agent_state TEXT
                """)
                logger.info("Added agent_state column to sessions table")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise
                logger.info("agent_state column already exists")

            try:
                conn.execute("""
                    ALTER TABLE sessions 
                    ADD COLUMN conversation_history TEXT
                """)
                logger.info("Added conversation_history column to sessions table")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise
                logger.info("conversation_history column already exists")

            try:
                conn.execute("""
                    ALTER TABLE sessions 
                    ADD COLUMN current_state TEXT DEFAULT 'welcome'
                """)
                logger.info("Added current_state column to sessions table")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise
                logger.info("current_state column already exists")

            conn.commit()

            # Update schema version
            self.set_schema_version(4)

            logger.info("Version 4 migration completed successfully")

        except Exception as e:
            conn.rollback()
            logger.error(f"Migration v4 failed: {e}")
            raise
        finally:
            conn.close()

    def create_default_admin(
        self, email: str, password_hash: str, full_name: str = "Admin User"
    ) -> str:
        """Create default admin user for initial setup"""
        import uuid

        admin_id = str(uuid.uuid4())
        conn = self.get_connection()
        try:
            conn.execute(
                """
                INSERT INTO users (id, email, password_hash, full_name, role, is_active)
                VALUES (?, ?, ?, ?, 'admin', 1)
            """,
                (admin_id, email, password_hash, full_name),
            )
            conn.commit()
            logger.info(f"Created default admin user: {email}")
            return admin_id
        finally:
            conn.close()

    def check_users_exist(self) -> bool:
        """Check if any users exist in database"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            return count > 0
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return False
        finally:
            conn.close()
