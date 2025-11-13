"""
Migration script to rebuild standards database with comprehensive schema
Loads data from NC Music Standards JSON files
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "pocket_musec.db"
FRAMEWORK_JSON = PROJECT_ROOT / "NC Music Standards and Resources" / "json_data" / "nc_arts_education_standards_framework_2024.json"
MUSIC_STANDARDS_JSON = PROJECT_ROOT / "NC Music Standards and Resources" / "json_data" / "nc_music_standards_expanded_2024.json"


class StandardsDatabaseMigration:
    """Handles database migration for NC Standards"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

        # Cache for foreign key lookups
        self.document_ids: Dict[str, int] = {}
        self.strand_ids: Dict[str, int] = {}
        self.discipline_ids: Dict[str, int] = {}
        self.level_ids: Dict[str, int] = {}
        self.standard_ids: Dict[str, int] = {}

        # Strand code mapping (abbreviated -> full)
        self.strand_code_mapping = {
            'CN': 'CONNECT',
            'CR': 'CREATE',
            'PR': 'PRESENT',
            'RE': 'RESPOND'
        }

    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Connected to database: {self.db_path}")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def drop_existing_tables(self):
        """Drop all existing tables and views"""
        logger.info("Dropping existing tables and views...")

        # Drop views first
        views = ['objectives_full', 'standards_full']
        for view in views:
            try:
                self.conn.execute(f"DROP VIEW IF EXISTS {view}")
                logger.info(f"Dropped view: {view}")
            except Exception as e:
                logger.warning(f"Could not drop view {view}: {e}")

        # Then drop tables
        tables = [
            'objectives',
            'standard_variants',
            'standards',
            'levels',
            'disciplines',
            'strands',
            'documents'
        ]

        for table in tables:
            try:
                self.conn.execute(f"DROP TABLE IF EXISTS {table}")
                logger.info(f"Dropped table: {table}")
            except Exception as e:
                logger.warning(f"Could not drop table {table}: {e}")

        self.conn.commit()
        logger.info("All tables and views dropped successfully")

    def create_schema(self):
        """Create new database schema"""
        logger.info("Creating new database schema...")

        schema = """
        -- Document metadata table
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            revision_date TEXT,
            note TEXT,
            source TEXT,
            organization TEXT,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Strands table (CONNECT, CREATE, PRESENT, RESPOND)
        CREATE TABLE strands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            essential_question TEXT,
            display_order INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Disciplines table (music, dance, theatre, visual_arts)
        CREATE TABLE disciplines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Grade/Proficiency levels table
        CREATE TABLE levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discipline_id INTEGER REFERENCES disciplines(id) ON DELETE CASCADE,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            level_type TEXT NOT NULL, -- 'grade' or 'proficiency'
            description TEXT,
            display_order INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(discipline_id, code)
        );

        -- Standards table
        CREATE TABLE standards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
            strand_id INTEGER REFERENCES strands(id) ON DELETE CASCADE,
            discipline_id INTEGER REFERENCES disciplines(id) ON DELETE CASCADE,
            level_id INTEGER REFERENCES levels(id) ON DELETE CASCADE,
            code TEXT NOT NULL,
            category TEXT,
            text TEXT NOT NULL,
            is_variant INTEGER DEFAULT 0,
            parent_standard_id INTEGER REFERENCES standards(id) ON DELETE CASCADE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(document_id, level_id, code)
        );

        -- Standard variants table (for discipline-specific variations like GM/VIM)
        CREATE TABLE standard_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            standard_id INTEGER REFERENCES standards(id) ON DELETE CASCADE,
            variant_type TEXT NOT NULL,
            variant_type_full TEXT,
            text TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(standard_id, variant_type)
        );

        -- Objectives table (the specific learning objectives under each standard)
        CREATE TABLE objectives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            standard_id INTEGER REFERENCES standards(id) ON DELETE CASCADE,
            code TEXT NOT NULL,
            text TEXT NOT NULL,
            display_order INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(standard_id, code)
        );

        -- Indexes for common queries
        CREATE INDEX idx_standards_document ON standards(document_id);
        CREATE INDEX idx_standards_strand ON standards(strand_id);
        CREATE INDEX idx_standards_discipline ON standards(discipline_id);
        CREATE INDEX idx_standards_level ON standards(level_id);
        CREATE INDEX idx_standards_code ON standards(code);
        CREATE INDEX idx_objectives_standard ON objectives(standard_id);
        CREATE INDEX idx_objectives_code ON objectives(code);
        CREATE INDEX idx_levels_discipline ON levels(discipline_id);
        CREATE INDEX idx_standard_variants_standard ON standard_variants(standard_id);

        -- Views for easy querying
        CREATE VIEW standards_full AS
        SELECT
            s.id AS standard_id,
            s.code AS standard_code,
            s.category,
            s.text AS standard_text,
            str.code AS strand_code,
            str.name AS strand_name,
            str.description AS strand_description,
            d.code AS discipline_code,
            d.name AS discipline_name,
            l.code AS level_code,
            l.name AS level_name,
            l.level_type,
            doc.title AS document_title,
            doc.revision_date
        FROM standards s
        JOIN strands str ON s.strand_id = str.id
        JOIN disciplines d ON s.discipline_id = d.id
        JOIN levels l ON s.level_id = l.id
        JOIN documents doc ON s.document_id = doc.id
        WHERE s.is_variant = 0;

        CREATE VIEW objectives_full AS
        SELECT
            o.id AS objective_id,
            o.code AS objective_code,
            o.text AS objective_text,
            s.id AS standard_id,
            s.code AS standard_code,
            s.text AS standard_text,
            s.category,
            str.code AS strand_code,
            str.name AS strand_name,
            d.code AS discipline_code,
            d.name AS discipline_name,
            l.code AS level_code,
            l.name AS level_name,
            l.level_type,
            doc.title AS document_title
        FROM objectives o
        JOIN standards s ON o.standard_id = s.id
        JOIN strands str ON s.strand_id = str.id
        JOIN disciplines d ON s.discipline_id = d.id
        JOIN levels l ON s.level_id = l.id
        JOIN documents doc ON s.document_id = doc.id;
        """

        self.conn.executescript(schema)
        self.conn.commit()
        logger.info("Schema created successfully")

    def load_framework_data(self, framework_path: Path):
        """Load data from framework JSON"""
        logger.info(f"Loading framework data from {framework_path}")

        with open(framework_path, 'r') as f:
            data = json.load(f)

        # Insert document
        doc = data['document']
        cursor = self.conn.execute("""
            INSERT INTO documents (title, revision_date, note, source, organization)
            VALUES (?, ?, ?, ?, ?)
        """, (
            doc['title'],
            doc.get('revision_date'),
            doc.get('note'),
            doc.get('source'),
            doc.get('organization')
        ))
        framework_doc_id = cursor.lastrowid
        self.document_ids['framework'] = framework_doc_id
        logger.info(f"Inserted framework document (ID: {framework_doc_id})")

        # Insert strands
        for idx, strand in enumerate(data['strands']):
            cursor = self.conn.execute("""
                INSERT INTO strands (code, name, description, essential_question, display_order)
                VALUES (?, ?, ?, ?, ?)
            """, (
                strand['code'],
                strand['name'],
                strand['description'],
                strand['essential_question'],
                idx
            ))
            self.strand_ids[strand['code']] = cursor.lastrowid
            logger.info(f"Inserted strand: {strand['code']} - {strand['name']}")

        # Insert disciplines (but not their standards yet - that comes from expanded JSON)
        for disc_code, disc_data in data['disciplines'].items():
            cursor = self.conn.execute("""
                INSERT INTO disciplines (code, name)
                VALUES (?, ?)
            """, (disc_code, disc_data['name']))
            self.discipline_ids[disc_code] = cursor.lastrowid
            logger.info(f"Inserted discipline: {disc_code} - {disc_data['name']}")

        self.conn.commit()
        logger.info("Framework data loaded successfully")

    def load_music_standards(self, standards_path: Path):
        """Load music standards from expanded JSON"""
        logger.info(f"Loading music standards from {standards_path}")

        with open(standards_path, 'r') as f:
            data = json.load(f)

        # Insert music document
        doc = data['document']
        cursor = self.conn.execute("""
            INSERT INTO documents (title, revision_date, source, organization, description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            doc['title'],
            doc.get('revision_date'),
            doc.get('source'),
            doc.get('organization'),
            doc.get('description')
        ))
        music_doc_id = cursor.lastrowid
        self.document_ids['music'] = music_doc_id
        logger.info(f"Inserted music document (ID: {music_doc_id})")

        # Get music discipline ID
        music_discipline_id = self.discipline_ids['music']

        # Process General Music
        if 'general_music' in data:
            logger.info("Processing General Music standards...")
            self._process_music_category(
                data['general_music'],
                music_doc_id,
                music_discipline_id,
                'general_music'
            )

        # Process Vocal/Instrumental Music
        if 'vocal_instrumental_music' in data:
            logger.info("Processing Vocal/Instrumental Music standards...")
            self._process_music_category(
                data['vocal_instrumental_music'],
                music_doc_id,
                music_discipline_id,
                'vocal_instrumental_music'
            )

        self.conn.commit()
        logger.info("Music standards loaded successfully")

    def _process_music_category(self, category_data: Dict, doc_id: int, discipline_id: int, category_name: str):
        """Process a music category (General or Vocal/Instrumental)"""

        # Determine if this uses grade levels or proficiency levels
        levels_data = category_data.get('grade_levels') or category_data.get('proficiency_levels')
        level_type = 'grade' if 'grade_levels' in category_data else 'proficiency'

        if not levels_data:
            logger.warning(f"No levels found in {category_name}")
            return

        # Process each level
        for level_key, level_data in levels_data.items():
            level_code = level_data.get('code') or level_data.get('grade') or level_key
            level_name = level_data.get('grade') or level_data.get('level') or level_key

            # Insert or get level
            level_id = self._insert_or_get_level(
                discipline_id,
                level_code,
                level_name,
                level_type,
                level_data.get('description')
            )

            # Process strands
            strands_data = level_data.get('strands', {})
            for strand_key, strand_data in strands_data.items():
                strand_code = strand_data.get('strand_code')

                # Map abbreviated strand code to full code
                if strand_code in self.strand_code_mapping:
                    strand_code = self.strand_code_mapping[strand_code]

                if not strand_code or strand_code not in self.strand_ids:
                    logger.warning(f"Unknown strand code: {strand_code}")
                    continue

                strand_id = self.strand_ids[strand_code]

                # Process standards
                standards = strand_data.get('standards', [])
                for standard in standards:
                    self._insert_standard_with_objectives(
                        standard,
                        doc_id,
                        strand_id,
                        discipline_id,
                        level_id
                    )

    def _insert_or_get_level(self, discipline_id: int, code: str, name: str, level_type: str, description: Optional[str]) -> int:
        """Insert a level or return existing ID"""
        cache_key = f"{discipline_id}:{code}"

        if cache_key in self.level_ids:
            return self.level_ids[cache_key]

        # Try to get existing
        cursor = self.conn.execute(
            "SELECT id FROM levels WHERE discipline_id = ? AND code = ?",
            (discipline_id, code)
        )
        row = cursor.fetchone()

        if row:
            level_id = row[0]
        else:
            cursor = self.conn.execute("""
                INSERT INTO levels (discipline_id, code, name, level_type, description)
                VALUES (?, ?, ?, ?, ?)
            """, (discipline_id, code, name, level_type, description))
            level_id = cursor.lastrowid
            logger.info(f"Inserted level: {code} - {name}")

        self.level_ids[cache_key] = level_id
        return level_id

    def _insert_standard_with_objectives(self, standard: Dict, doc_id: int, strand_id: int,
                                        discipline_id: int, level_id: int):
        """Insert a standard and its objectives"""

        # Insert standard
        cursor = self.conn.execute("""
            INSERT INTO standards (document_id, strand_id, discipline_id, level_id, code, category, text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            strand_id,
            discipline_id,
            level_id,
            standard['code'],
            standard.get('category'),
            standard['text']
        ))
        standard_id = cursor.lastrowid
        self.standard_ids[standard['code']] = standard_id

        # Insert standard variants if present
        if 'variants' in standard:
            for variant in standard['variants']:
                self.conn.execute("""
                    INSERT INTO standard_variants (standard_id, variant_type, variant_type_full, text)
                    VALUES (?, ?, ?, ?)
                """, (
                    standard_id,
                    variant['type'],
                    variant.get('type_full'),
                    variant['text']
                ))

        # Insert objectives
        objectives = standard.get('objectives', [])
        for idx, objective in enumerate(objectives):
            self.conn.execute("""
                INSERT INTO objectives (standard_id, code, text, display_order)
                VALUES (?, ?, ?, ?)
            """, (
                standard_id,
                objective['code'],
                objective['text'],
                idx
            ))

    def verify_data(self):
        """Verify loaded data"""
        logger.info("Verifying data integrity...")

        counts = {
            'documents': self.conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
            'strands': self.conn.execute("SELECT COUNT(*) FROM strands").fetchone()[0],
            'disciplines': self.conn.execute("SELECT COUNT(*) FROM disciplines").fetchone()[0],
            'levels': self.conn.execute("SELECT COUNT(*) FROM levels").fetchone()[0],
            'standards': self.conn.execute("SELECT COUNT(*) FROM standards").fetchone()[0],
            'objectives': self.conn.execute("SELECT COUNT(*) FROM objectives").fetchone()[0],
            'standard_variants': self.conn.execute("SELECT COUNT(*) FROM standard_variants").fetchone()[0],
        }

        logger.info("Data counts:")
        for table, count in counts.items():
            logger.info(f"  {table}: {count}")

        # Sample query
        logger.info("\nSample data - First 5 objectives:")
        cursor = self.conn.execute("""
            SELECT objective_code, objective_text, standard_code, level_name
            FROM objectives_full
            LIMIT 5
        """)
        for row in cursor.fetchall():
            logger.info(f"  {row[0]}: {row[1][:50]}... (Standard: {row[2]}, Level: {row[3]})")

    def run_migration(self):
        """Execute complete migration"""
        try:
            self.connect()

            logger.info("=" * 80)
            logger.info("Starting Standards Database Migration")
            logger.info("=" * 80)

            # Step 1: Drop existing tables
            self.drop_existing_tables()

            # Step 2: Create new schema
            self.create_schema()

            # Step 3: Load framework data
            if FRAMEWORK_JSON.exists():
                self.load_framework_data(FRAMEWORK_JSON)
            else:
                logger.error(f"Framework JSON not found: {FRAMEWORK_JSON}")
                return False

            # Step 4: Load music standards
            if MUSIC_STANDARDS_JSON.exists():
                self.load_music_standards(MUSIC_STANDARDS_JSON)
            else:
                logger.error(f"Music standards JSON not found: {MUSIC_STANDARDS_JSON}")
                return False

            # Step 5: Verify
            self.verify_data()

            logger.info("=" * 80)
            logger.info("Migration completed successfully!")
            logger.info("=" * 80)

            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            if self.conn:
                self.conn.rollback()
            return False

        finally:
            self.close()


def main():
    """Main migration function"""
    # Ensure database directory exists
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Run migration
    migration = StandardsDatabaseMigration(DATABASE_PATH)
    success = migration.run_migration()

    if success:
        logger.info(f"\nDatabase successfully migrated at: {DATABASE_PATH}")
        return 0
    else:
        logger.error("\nMigration failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    exit(main())
