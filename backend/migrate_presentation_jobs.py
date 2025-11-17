#!/usr/bin/env python3
"""
Standalone migration script for presentation jobs persistence.

This script can be run independently to migrate the database schema
for the new presentation jobs table without requiring the full application.
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from backend.repositories.migrations import MigrationManager, run_migration_v11
from backend.config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main migration script."""
    parser = argparse.ArgumentParser(description='Migrate database for presentation jobs persistence')
    parser.add_argument(
        '--db-path',
        type=str,
        default=None,
        help='Path to the database file (uses config default if not specified)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force migration even if already at latest version'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine database path
    if args.db_path:
        db_path = args.db_path
    else:
        db_path = config.database.path

    logger.info(f"Starting presentation jobs migration for database: {db_path}")

    try:
        # Initialize migration manager
        migrator = MigrationManager(db_path)

        # Check current version
        current_version = migrator.get_schema_version()
        logger.info(f"Current database schema version: {current_version}")

        if current_version >= 11 and not args.force:
            logger.info("Database already at version 11 or higher. Use --force to re-run migration.")
            return 0

        if args.force:
            logger.info("Force migration requested, proceeding regardless of current version")

        # Run the migration
        logger.info("Running migration to version 11: presentation jobs table")
        migrator.migrate_to_v11_presentation_jobs()

        # Verify migration
        new_version = migrator.get_schema_version()
        logger.info(f"Migration completed. New schema version: {new_version}")

        # Verify table exists
        conn = migrator.get_connection()
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='presentation_jobs'"
            )
            table_exists = cursor.fetchone() is not None

            if table_exists:
                logger.info("✓ presentation_jobs table created successfully")

                # Check indexes
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='presentation_jobs'"
                )
                indexes = [row[0] for row in cursor.fetchall()]
                logger.info(f"✓ Created {len(indexes)} indexes: {', '.join(indexes)}")

            else:
                logger.error("✗ presentation_jobs table was not created")
                return 1

        finally:
            conn.close()

        logger.info("Migration completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if args.verbose:
            import traceback
            logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())