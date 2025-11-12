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
        """Run all necessary migrations in order"""
        logger.info("Starting database migration...")
        
        # Run core migrations
        self.migrate_standards_table()
        self.migrate_to_milestone3()
        self.migrate_to_v4_session_persistence()
        
        # Run extended migrations
        self.migrate_to_extended_schema()
        
        # Run drafts migration
        self.migrate_to_drafts_support()
        
        logger.info("All migrations completed successfully")

    def migrate_standards_table(self) -> None:
        """
        Create standards and objectives tables if they don't exist
        
        Adds:
        - standards table for music education standards
        - objectives table for learning objectives
        """
        current_version = self.get_schema_version()

        if current_version >= 1:
            logger.info(
                f"Database already at version {current_version}, skipping standards migration"
            )
            return

        logger.info("Starting standards table migration...")

        conn = self.get_connection()
        try:
            # Create standards table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS standards (
                    standard_id TEXT PRIMARY KEY,
                    grade_level TEXT NOT NULL,
                    strand_code TEXT NOT NULL,
                    strand_name TEXT NOT NULL,
                    strand_description TEXT,
                    standard_text TEXT NOT NULL,
                    source_document TEXT,
                    ingestion_date TEXT,
                    version TEXT DEFAULT '1.0'
                )
            """)

            # Create objectives table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS objectives (
                    objective_id TEXT PRIMARY KEY,
                    standard_id TEXT NOT NULL,
                    objective_text TEXT NOT NULL,
                    FOREIGN KEY (standard_id) REFERENCES standards(standard_id)
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_standards_grade ON standards(grade_level)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_standards_strand ON standards(strand_code)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_objectives_standard ON objectives(standard_id)")

            conn.commit()

            # Update schema version
            self.set_schema_version(1)

            logger.info("Standards table migration completed successfully")

        except Exception as e:
            conn.rollback()
            logger.error(f"Standards migration failed: {e}")
            raise
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
                    is_draft INTEGER DEFAULT 0,
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

    def migrate_to_extended_schema(self) -> None:
        """Migrate database to support extended document types"""
        logger.info("Starting extended schema migration...")

        conn = self.get_connection()
        try:
            # Create unpacking document tables
            self._create_unpacking_tables(conn)

            # Create alignment document tables
            self._create_alignment_tables(conn)

            # Create reference document tables
            self._create_reference_tables(conn)

            # Create indexes for performance
            self._create_extended_indexes(conn)

            conn.commit()
            logger.info("Extended schema migration completed successfully")

        except Exception as e:
            conn.rollback()
            logger.error(f"Extended schema migration failed: {e}")
            raise
        finally:
            conn.close()

    def _create_unpacking_tables(self, conn: sqlite3.Connection) -> None:
        """Create tables for unpacking document content"""

        # Unpacking sections table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS unpacking_sections (
                section_id TEXT PRIMARY KEY,
                grade_level TEXT NOT NULL,
                strand_code TEXT,
                standard_id TEXT,
                section_title TEXT NOT NULL,
                content TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                source_document TEXT NOT NULL,
                ingestion_date TEXT NOT NULL,
                version TEXT DEFAULT '1.0',
                FOREIGN KEY (standard_id) REFERENCES standards(standard_id)
            );
        """)

        # Teaching strategies table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS teaching_strategies (
                strategy_id TEXT PRIMARY KEY,
                section_id TEXT NOT NULL,
                strategy_text TEXT NOT NULL,
                grade_level TEXT NOT NULL,
                strand_code TEXT,
                standard_id TEXT,
                source_document TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                ingestion_date TEXT NOT NULL,
                FOREIGN KEY (section_id) REFERENCES unpacking_sections(section_id),
                FOREIGN KEY (standard_id) REFERENCES standards(standard_id)
            );
        """)

        # Assessment guidance table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assessment_guidance (
                guidance_id TEXT PRIMARY KEY,
                section_id TEXT NOT NULL,
                guidance_text TEXT NOT NULL,
                grade_level TEXT NOT NULL,
                strand_code TEXT,
                standard_id TEXT,
                source_document TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                ingestion_date TEXT NOT NULL,
                FOREIGN KEY (section_id) REFERENCES unpacking_sections(section_id),
                FOREIGN KEY (standard_id) REFERENCES standards(standard_id)
            );
        """)

        logger.info("Created unpacking document tables")

    def _create_alignment_tables(self, conn: sqlite3.Connection) -> None:
        """Create tables for alignment document content"""

        # Alignment relationships table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alignment_relationships (
                relationship_id TEXT PRIMARY KEY,
                standard_id TEXT NOT NULL,
                related_standard_ids TEXT NOT NULL,  -- JSON array of related standard IDs
                relationship_type TEXT NOT NULL,
                grade_level TEXT NOT NULL,
                strand_code TEXT NOT NULL,
                description TEXT,
                source_document TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                ingestion_date TEXT NOT NULL,
                version TEXT DEFAULT '1.0',
                FOREIGN KEY (standard_id) REFERENCES standards(standard_id)
            );
        """)

        # Progression mappings table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS progression_mappings (
                mapping_id TEXT PRIMARY KEY,
                skill_name TEXT NOT NULL,
                grade_levels TEXT NOT NULL,  -- JSON array of grade levels
                standard_mappings TEXT NOT NULL,  -- JSON object mapping grade -> standard_id
                progression_notes TEXT,
                source_document TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                ingestion_date TEXT NOT NULL,
                version TEXT DEFAULT '1.0'
            );
        """)

        logger.info("Created alignment document tables")

    def _create_reference_tables(self, conn: sqlite3.Connection) -> None:
        """Create tables for reference document content"""

        # Glossary entries table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS glossary_entries (
                entry_id TEXT PRIMARY KEY,
                term TEXT NOT NULL,
                definition TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                related_standards TEXT,  -- JSON array of related standard IDs
                source_document TEXT NOT NULL,
                ingestion_date TEXT NOT NULL,
                version TEXT DEFAULT '1.0'
            );
        """)

        # FAQ entries table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS faq_entries (
                entry_id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                category TEXT,
                source_document TEXT NOT NULL,
                ingestion_date TEXT NOT NULL,
                version TEXT DEFAULT '1.0'
            );
        """)

        # General resource entries table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS resource_entries (
                entry_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                content_type TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                metadata TEXT,  -- JSON object for additional metadata
                source_document TEXT NOT NULL,
                ingestion_date TEXT NOT NULL,
                version TEXT DEFAULT '1.0'
            );
        """)

        logger.info("Created reference document tables")

    def _create_extended_indexes(self, conn: sqlite3.Connection) -> None:
        """Create indexes for extended tables"""

        # Unpacking indexes
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_unpacking_grade ON unpacking_sections(grade_level);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_unpacking_strand ON unpacking_sections(strand_code);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_unpacking_standard ON unpacking_sections(standard_id);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_strategies_grade ON teaching_strategies(grade_level);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_strategies_section ON teaching_strategies(section_id);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_guidance_grade ON assessment_guidance(grade_level);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_guidance_section ON assessment_guidance(section_id);"
        )

        # Alignment indexes
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_alignment_standard ON alignment_relationships(standard_id);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_alignment_type ON alignment_relationships(relationship_type);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_alignment_grade ON alignment_relationships(grade_level);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_progression_skill ON progression_mappings(skill_name);"
        )

        # Reference indexes
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_glossary_term ON glossary_entries(term);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_faq_category ON faq_entries(category);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_resource_type ON resource_entries(content_type);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_resource_source ON resource_entries(source_document);"
        )

        logger.info("Created extended table indexes")

    def get_migration_status(self) -> dict:
        """Get the current migration status"""
        conn = self.get_connection()
        try:
            # Get basic schema version
            schema_version = self.get_schema_version()
            
            # Check for extended tables
            tables = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name IN ('unpacking_sections', 'teaching_strategies', 'assessment_guidance',
                           'alignment_relationships', 'progression_mappings',
                           'glossary_entries', 'faq_entries', 'resource_entries')
                ORDER BY name
            """).fetchall()

            table_names = [row[0] for row in tables]

            # Get record counts for each table
            counts = {}
            for table in table_names:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                counts[table] = count

            return {
                "schema_version": schema_version,
                "extended_tables_exist": len(table_names) > 0,
                "table_count": len(table_names),
                "tables": table_names,
                "record_counts": counts,
            }

        finally:
            conn.close()

    def clear_extended_data(self, confirm: bool = False) -> None:
        """Clear all extended document data (for testing/re-ingestion)"""
        if not confirm:
            raise ValueError("Must confirm data deletion by setting confirm=True")

        logger.warning("Clearing all extended document data...")

        conn = self.get_connection()
        try:
            # Clear all extended tables
            extended_tables = [
                "unpacking_sections",
                "teaching_strategies",
                "assessment_guidance",
                "alignment_relationships",
                "progression_mappings",
                "glossary_entries",
                "faq_entries",
                "resource_entries",
            ]

            for table in extended_tables:
                conn.execute(f"DELETE FROM {table}")

            conn.commit()
            logger.info("Cleared all extended document data")

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to clear extended data: {e}")
            raise
        finally:
            conn.close()

    def migrate_to_drafts_support(self) -> None:
        """
        Migrate to version 5: Add drafts support to lessons table
        
        Adds:
        - is_draft column to lessons table for distinguishing drafts from published lessons
        """
        current_version = self.get_schema_version()

        if current_version >= 5:
            logger.info(
                f"Database already at version {current_version}, skipping drafts migration"
            )
            return

        logger.info("Starting version 5 database migration (drafts support)...")

        conn = self.get_connection()
        try:
            # Add is_draft column to lessons table
            try:
                conn.execute("""
                    ALTER TABLE lessons
                    ADD COLUMN is_draft INTEGER DEFAULT 0
                """)
                logger.info("Added is_draft column to lessons table")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise
                logger.info("is_draft column already exists")

            conn.commit()

            # Update schema version
            self.set_schema_version(5)

            logger.info("Version 5 migration completed successfully")

        except Exception as e:
            conn.rollback()
            logger.error(f"Migration v5 failed: {e}")
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


# Alias for backward compatibility
DatabaseMigrator = MigrationManager
ExtendedDatabaseMigrator = MigrationManager


# Convenience functions
def migrate_extended_schema(db_path: str) -> None:
    """Convenience function to migrate database to extended schema"""
    migrator = MigrationManager(db_path)
    migrator.migrate_to_extended_schema()


def get_extended_migration_status(db_path: str) -> dict:
    """Convenience function to get migration status"""
    migrator = MigrationManager(db_path)
    return migrator.get_migration_status()
