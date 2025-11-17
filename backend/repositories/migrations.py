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

        if current_version < 13:
            self.migrate_to_v13_add_foreign_keys()

        if current_version < 14:
            self.migrate_to_v14_camelcase_fields()

        logger.info(
            f"All migrations completed. Current version: {self.get_schema_version()}"
        )

    def _ensure_table(
        self, conn: sqlite3.Connection, table_name: str, create_sql: str
    ) -> None:
        """Create a table if it does not exist."""
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
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
                """,
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

            logger.info("Version 12 migration (styles table) completed successfully")

        except Exception as e:
            conn.rollback()
            logger.error(f"Migration v12 failed: {e}")
            raise
        finally:
            conn.close()

    def migrate_to_v13_add_foreign_keys(self) -> None:
        """
        Migrate to version 13: Add foreign key constraints for data integrity

        NOTE: SQLite requires recreating tables to add foreign keys.
        This migration will:
        - Add foreign key from presentations.lesson_id to lessons.id with CASCADE
        - Add foreign key from presentation_jobs.lesson_id to lessons.id
        """
        current_version = self.get_schema_version()

        if current_version >= 13:
            logger.info(
                f"Database already at version {current_version}, skipping v13 migration"
            )
            return

        logger.info("Starting migration to version 13: Add foreign key constraints")

        conn = self.get_connection()
        try:
            # Enable foreign key support
            conn.execute("PRAGMA foreign_keys = ON")

            # For presentations table - recreate with foreign key
            logger.info("Migrating presentations table with foreign key constraint...")

            # Create new presentations table with foreign key
            conn.execute("""
                CREATE TABLE presentations_new (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL,
                    lesson_revision INTEGER NOT NULL,
                    version TEXT NOT NULL,
                    status TEXT NOT NULL,
                    style TEXT NOT NULL,
                    slides TEXT NOT NULL,
                    export_assets TEXT NOT NULL,
                    error_code TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
                )
            """)

            # Copy data from old table
            conn.execute("""
                INSERT INTO presentations_new 
                SELECT * FROM presentations
                WHERE lesson_id IN (SELECT id FROM lessons)
            """)

            # Drop old table and rename new one
            conn.execute("DROP TABLE presentations")
            conn.execute("ALTER TABLE presentations_new RENAME TO presentations")

            # Recreate indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_presentations_lesson 
                ON presentations(lesson_id, lesson_revision)
            """)

            logger.info("Presentations table migrated successfully")

            # For presentation_jobs table - recreate with foreign key
            logger.info(
                "Migrating presentation_jobs table with foreign key constraint..."
            )

            conn.execute("""
                CREATE TABLE presentation_jobs_new (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority TEXT NOT NULL DEFAULT 'normal',
                    progress INTEGER DEFAULT 0,
                    message TEXT DEFAULT '',
                    created_at TIMESTAMP NOT NULL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    timeout_seconds INTEGER DEFAULT 30,
                    presentation_id TEXT,
                    slide_count INTEGER,
                    result_data TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 2,
                    error_code TEXT,
                    error_message TEXT,
                    error_details TEXT,
                    style TEXT DEFAULT 'default',
                    use_llm_polish INTEGER DEFAULT 1,
                    worker_id TEXT,
                    queue_position INTEGER,
                    processing_time_seconds REAL,
                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
                    FOREIGN KEY (presentation_id) REFERENCES presentations(id) ON DELETE SET NULL
                )
            """)

            # Copy data from old table, keeping only jobs with valid lessons
            conn.execute("""
                INSERT INTO presentation_jobs_new
                SELECT * FROM presentation_jobs
                WHERE lesson_id IN (SELECT id FROM lessons)
            """)

            # Drop old table and rename new one
            conn.execute("DROP TABLE presentation_jobs")
            conn.execute(
                "ALTER TABLE presentation_jobs_new RENAME TO presentation_jobs"
            )

            # Recreate indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON presentation_jobs(user_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_lesson_id ON presentation_jobs(lesson_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_status ON presentation_jobs(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON presentation_jobs(created_at DESC)
            """)

            logger.info("Presentation jobs table migrated successfully")

            conn.commit()

            # Update schema version
            self.set_schema_version(13)

            logger.info(
                "Version 13 migration (foreign key constraints) completed successfully"
            )

        except Exception as e:
            conn.rollback()
            logger.error(f"Migration v13 failed: {e}")
            raise
        finally:
            conn.close()

    def migrate_to_v14_camelcase_fields(self) -> None:
        """
        Migrate to version 14: Convert snake_case field names to camelCase

        This migration adds camelCase columns alongside existing snake_case columns
        to enable gradual transition. Data is copied to new columns and feature flags
        control which format is used.

        Phase 1: Add new camelCase columns without removing old ones
        Phase 2: Data will be accessible in both formats during transition
        Phase 3: Old columns will be removed in future migration

        Tables affected:
        - users: email, password_hash, full_name, processing_mode, created_at, last_login, is_active
        - sessions: user_id, grade_level, strand_code, selected_standards, selected_objectives,
                   additional_standards, additional_objectives, additional_context, lesson_duration,
                   class_size, selected_model, agent_state, conversation_history, current_state,
                   created_at, updated_at
        - lessons: session_id, user_id, processing_mode, is_draft, created_at, updated_at
        - citations: lesson_id, source_type, source_id, source_title, page_number, citation_text,
                    citation_number, file_id, created_at
        - images: user_id, filename, file_path, file_size, mime_type, extracted_text,
                 vision_summary, ocr_confidence, metadata, created_at, last_accessed
        - standards: standard_id, grade_level, strand_code, strand_name, strand_description,
                    standard_text, source_document, file_id, ingestion_date, version
        - objectives: objective_id, standard_id, objective_text, file_id
        """
        current_version = self.get_schema_version()

        if current_version >= 14:
            logger.info(
                f"Database already at version {current_version}, skipping v14 migration"
            )
            return

        logger.info("Starting migration to version 14: Add camelCase field columns")

        conn = self.get_connection()
        try:
            # Enable foreign key support
            conn.execute("PRAGMA foreign_keys = ON")

            # Ensure users table exists before adding camelCase columns
            self._ensure_table(
                conn,
                "users",
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    role TEXT DEFAULT 'teacher',
                    processing_mode TEXT DEFAULT 'cloud',
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
                """,
            )

            # Phase 1: Add camelCase columns to users table
            logger.info("Adding camelCase columns to users table...")
            user_columns = [
                ("passwordHash", "TEXT"),
                ("fullName", "TEXT"),
                ("processingMode", "TEXT"),
                ("createdAt", "TIMESTAMP"),
                ("lastLogin", "TIMESTAMP"),
                ("isActive", "INTEGER"),
            ]

            for col_name, col_type in user_columns:
                try:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        logger.debug(f"Column {col_name} already exists in users table")
                    else:
                        raise

            # Copy data to new camelCase columns
            conn.execute("""
                UPDATE users SET 
                    passwordHash = password_hash,
                    fullName = full_name,
                    processingMode = processing_mode,
                    createdAt = created_at,
                    lastLogin = last_login,
                    isActive = is_active
                WHERE passwordHash IS NULL
            """)

            # Phase 2: Add camelCase columns to sessions table
            logger.info("Adding camelCase columns to sessions table...")
            session_columns = [
                ("userId", "TEXT"),
                ("gradeLevel", "TEXT"),
                ("strandCode", "TEXT"),
                ("selectedStandards", "TEXT"),
                ("selectedObjectives", "TEXT"),
                ("additionalStandards", "TEXT"),
                ("additionalObjectives", "TEXT"),
                ("additionalContext", "TEXT"),
                ("lessonDuration", "TEXT"),
                ("classSize", "INTEGER"),
                ("selectedModel", "TEXT"),
                ("agentState", "TEXT"),
                ("conversationHistory", "TEXT"),
                ("currentState", "TEXT"),
                ("createdAt", "TIMESTAMP"),
                ("updatedAt", "TIMESTAMP"),
            ]

            for col_name, col_type in session_columns:
                try:
                    conn.execute(
                        f"ALTER TABLE sessions ADD COLUMN {col_name} {col_type}"
                    )
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        logger.debug(
                            f"Column {col_name} already exists in sessions table"
                        )
                    else:
                        raise

            # Copy data to new camelCase columns (only if source columns exist)
            # First check which columns exist in the sessions table
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(sessions)")
            existing_columns = {row[1] for row in cursor.fetchall()}

            # Build dynamic UPDATE statement based on existing columns
            update_clauses = []
            if "user_id" in existing_columns:
                update_clauses.append("userId = user_id")
            if "grade_level" in existing_columns:
                update_clauses.append("gradeLevel = grade_level")
            if "strand_code" in existing_columns:
                update_clauses.append("strandCode = strand_code")
            if "selected_standards" in existing_columns:
                update_clauses.append("selectedStandards = selected_standards")
            if "selected_objectives" in existing_columns:
                update_clauses.append("selectedObjectives = selected_objectives")
            if "additional_standards" in existing_columns:
                update_clauses.append("additionalStandards = additional_standards")
            if "additional_objectives" in existing_columns:
                update_clauses.append("additionalObjectives = additional_objectives")
            if "additional_context" in existing_columns:
                update_clauses.append("additionalContext = additional_context")
            if "lesson_duration" in existing_columns:
                update_clauses.append("lessonDuration = lesson_duration")
            if "class_size" in existing_columns:
                update_clauses.append("classSize = class_size")
            if "selected_model" in existing_columns:
                update_clauses.append("selectedModel = selected_model")
            if "agent_state" in existing_columns:
                update_clauses.append("agentState = agent_state")
            if "conversation_history" in existing_columns:
                update_clauses.append("conversationHistory = conversation_history")
            if "current_state" in existing_columns:
                update_clauses.append("currentState = current_state")
            if "created_at" in existing_columns:
                update_clauses.append("createdAt = created_at")
            if "updated_at" in existing_columns:
                update_clauses.append("updatedAt = updated_at")

            if update_clauses:
                update_sql = f"""
                    UPDATE sessions SET 
                        {", ".join(update_clauses)}
                    WHERE userId IS NULL
                """
                conn.execute(update_sql)

            # Ensure lessons table exists before adding camelCase columns
            self._ensure_table(
                conn,
                "lessons",
                """
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
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )

            # Phase 3: Add camelCase columns to lessons table
            logger.info("Adding camelCase columns to lessons table...")
            lesson_columns = [
                ("sessionId", "TEXT"),
                ("userId", "TEXT"),
                ("processingMode", "TEXT"),
                ("isDraft", "INTEGER"),
                ("createdAt", "TIMESTAMP"),
                ("updatedAt", "TIMESTAMP"),
            ]

            for col_name, col_type in lesson_columns:
                try:
                    conn.execute(
                        f"ALTER TABLE lessons ADD COLUMN {col_name} {col_type}"
                    )
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        logger.debug(
                            f"Column {col_name} already exists in lessons table"
                        )
                    else:
                        raise

            # Copy data to new camelCase columns (only if source columns exist)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(lessons)")
            existing_columns = {row[1] for row in cursor.fetchall()}

            update_clauses = []
            if "session_id" in existing_columns:
                update_clauses.append("sessionId = session_id")
            if "user_id" in existing_columns:
                update_clauses.append("userId = user_id")
            if "processing_mode" in existing_columns:
                update_clauses.append("processingMode = processing_mode")
            if "is_draft" in existing_columns:
                update_clauses.append("isDraft = is_draft")
            if "created_at" in existing_columns:
                update_clauses.append("createdAt = created_at")
            if "updated_at" in existing_columns:
                update_clauses.append("updatedAt = updated_at")

            if update_clauses:
                update_sql = f"""
                    UPDATE lessons SET 
                        {", ".join(update_clauses)}
                    WHERE sessionId IS NULL
                """
                conn.execute(update_sql)

            # Ensure citations table exists before adding camelCase columns
            self._ensure_table(
                conn,
                "citations",
                """
                CREATE TABLE IF NOT EXISTS citations (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    source_title TEXT NOT NULL,
                    page_number INTEGER,
                    excerpt TEXT,
                    citation_text TEXT DEFAULT '',
                    citation_number INTEGER DEFAULT 1,
                    file_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )

            # Phase 4: Add camelCase columns to citations table
            logger.info("Adding camelCase columns to citations table...")
            citation_columns = [
                ("lessonId", "TEXT"),
                ("sourceType", "TEXT"),
                ("sourceId", "TEXT"),
                ("sourceTitle", "TEXT"),
                ("pageNumber", "INTEGER"),
                ("citationText", "TEXT"),
                ("citationNumber", "INTEGER"),
                ("fileId", "TEXT"),
                ("createdAt", "TIMESTAMP"),
            ]

            for col_name, col_type in citation_columns:
                try:
                    conn.execute(
                        f"ALTER TABLE citations ADD COLUMN {col_name} {col_type}"
                    )
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        logger.debug(
                            f"Column {col_name} already exists in citations table"
                        )
                    else:
                        raise

            # Copy data to new camelCase columns
            conn.execute("""
                UPDATE citations SET 
                    lessonId = lesson_id,
                    sourceType = source_type,
                    sourceId = source_id,
                    sourceTitle = source_title,
                    pageNumber = page_number,
                    citationText = citation_text,
                    citationNumber = citation_number,
                    fileId = file_id,
                    createdAt = created_at
                WHERE lessonId IS NULL
            """)

            # Ensure images table exists before adding camelCase columns
            self._ensure_table(
                conn,
                "images",
                """
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
                    last_accessed TIMESTAMP
                )
                """,
            )

            # Phase 5: Add camelCase columns to images table
            logger.info("Adding camelCase columns to images table...")
            image_columns = [
                ("userId", "TEXT"),
                ("filePath", "TEXT"),
                ("fileSize", "INTEGER"),
                ("mimeType", "TEXT"),
                ("extractedText", "TEXT"),
                ("visionSummary", "TEXT"),
                ("ocrConfidence", "REAL"),
                ("createdAt", "TIMESTAMP"),
                ("lastAccessed", "TIMESTAMP"),
            ]

            for col_name, col_type in image_columns:
                try:
                    conn.execute(f"ALTER TABLE images ADD COLUMN {col_name} {col_type}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        logger.debug(
                            f"Column {col_name} already exists in images table"
                        )
                    else:
                        raise

            # Copy data to new camelCase columns
            conn.execute("""
                UPDATE images SET 
                    userId = user_id,
                    filePath = file_path,
                    fileSize = file_size,
                    mimeType = mime_type,
                    extractedText = extracted_text,
                    visionSummary = vision_summary,
                    ocrConfidence = ocr_confidence,
                    createdAt = created_at,
                    lastAccessed = last_accessed
                WHERE userId IS NULL
            """)

            # Phase 6: Add camelCase columns to standards table (if exists)
            logger.info("Adding camelCase columns to standards table...")
            try:
                standard_columns = [
                    ("standardId", "TEXT"),
                    ("gradeLevel", "TEXT"),
                    ("strandCode", "TEXT"),
                    ("strandName", "TEXT"),
                    ("strandDescription", "TEXT"),
                    ("standardText", "TEXT"),
                    ("sourceDocument", "TEXT"),
                    ("fileId", "TEXT"),
                    ("ingestionDate", "TEXT"),
                ]

                for col_name, col_type in standard_columns:
                    try:
                        conn.execute(
                            f"ALTER TABLE standards ADD COLUMN {col_name} {col_type}"
                        )
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e):
                            logger.debug(
                                f"Column {col_name} already exists in standards table"
                            )
                        else:
                            raise

                # Copy data to new camelCase columns (if old columns exist)
                try:
                    conn.execute("""
                        UPDATE standards SET 
                            standardId = standard_id,
                            gradeLevel = grade_level,
                            strandCode = strand_code,
                            strandName = strand_name,
                            strandDescription = strand_description,
                            standardText = standard_text,
                            sourceDocument = source_document,
                            fileId = file_id,
                            ingestionDate = ingestion_date
                        WHERE standardId IS NULL
                    """)
                except sqlite3.OperationalError as e:
                    if "no such column" in str(e):
                        logger.info(
                            "Standards table already using new schema, skipping data copy..."
                        )
                    else:
                        raise

            except sqlite3.OperationalError as e:
                if "no such table" in str(e):
                    logger.info("Standards table does not exist, skipping...")
                else:
                    raise

            # Phase 7: Add camelCase columns to objectives table (if exists)
            logger.info("Adding camelCase columns to objectives table...")
            try:
                objective_columns = [
                    ("objectiveId", "TEXT"),
                    ("standardId", "TEXT"),
                    ("objectiveText", "TEXT"),
                    ("fileId", "TEXT"),
                ]

                for col_name, col_type in objective_columns:
                    try:
                        conn.execute(
                            f"ALTER TABLE objectives ADD COLUMN {col_name} {col_type}"
                        )
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e):
                            logger.debug(
                                f"Column {col_name} already exists in objectives table"
                            )
                        else:
                            raise

                # Copy data to new camelCase columns (if old columns exist)
                try:
                    conn.execute("""
                        UPDATE objectives SET 
                            objectiveId = objective_id,
                            standardId = standard_id,
                            objectiveText = objective_text,
                            fileId = file_id
                        WHERE objectiveId IS NULL
                    """)
                except sqlite3.OperationalError as e:
                    if "no such column" in str(e):
                        logger.info(
                            "Objectives table already using new schema, skipping data copy..."
                        )
                    else:
                        raise

            except sqlite3.OperationalError as e:
                if "no such table" in str(e):
                    logger.info("Objectives table does not exist, skipping...")
                else:
                    raise

            conn.commit()

            # Update schema version
            self.set_schema_version(14)

            logger.info(
                "Version 14 migration (camelCase field columns) completed successfully"
            )
            logger.info(
                "Both snake_case and camelCase columns are now available. "
                "Use feature flags to control which format is used."
            )

        except Exception as e:
            conn.rollback()
            logger.error(f"Migration v14 failed: {e}")
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


def run_migration_v13(db_path: str) -> None:
    """Convenience function to run v13 migration"""
    migrator = MigrationManager(db_path)
    migrator.migrate_to_v13_add_foreign_keys()


def run_migration_v14(db_path: str) -> None:
    """Convenience function to run v14 migration"""
    migrator = MigrationManager(db_path)
    migrator.migrate_to_v14_camelcase_fields()
