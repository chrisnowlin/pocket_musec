"""Extended database migrations for unpacking, alignment, and reference documents"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ExtendedDatabaseMigrator:
    """Manages database schema migrations for extended document types"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection"""
        return sqlite3.connect(self.db_path)

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


def migrate_extended_schema(db_path: str) -> None:
    """Convenience function to migrate database to extended schema"""
    migrator = ExtendedDatabaseMigrator(db_path)
    migrator.migrate_to_extended_schema()


def get_extended_migration_status(db_path: str) -> dict:
    """Convenience function to get migration status"""
    migrator = ExtendedDatabaseMigrator(db_path)
    return migrator.get_migration_status()
