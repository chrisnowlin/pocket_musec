#!/usr/bin/env python3
"""
Database Consolidation Script

This script consolidates all data from various database files into a single database.
It moves data from the old standards.db location to the new unified pocket_musec.db.

Usage:
    python scripts/consolidate_database.py [--source-db path] [--target-db path] [--backup]
"""

import os
import shutil
import sqlite3
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database_info(db_path: str) -> Dict[str, Any]:
    """Get information about a database file."""
    info = {
        'exists': False,
        'size_bytes': 0,
        'tables': [],
        'record_counts': {}
    }
    
    if not Path(db_path).exists():
        return info
    
    info['exists'] = True
    info['size_bytes'] = Path(db_path).stat().st_size
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Get table list
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        info['tables'] = [row[0] for row in cursor.fetchall()]
        
        # Get record counts for each table
        for table in info['tables']:
            try:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                info['record_counts'][table] = cursor.fetchone()[0]
            except sqlite3.Error as e:
                info['record_counts'][table] = f"Error: {e}"
        
        conn.close()
        
    except sqlite3.Error as e:
        logger.error(f"Error reading database {db_path}: {e}")
        info['tables'] = []
        info['record_counts'] = {}
    
    return info

def backup_database(db_path: str) -> str:
    """Create a backup of the database file."""
    if not Path(db_path).exists():
        logger.info(f"No database to backup at {db_path}")
        return ""
    
    backup_path = f"{db_path}.backup.{int(os.path.getmtime(db_path))}"
    shutil.copy2(db_path, backup_path)
    logger.info(f"Created backup: {backup_path}")
    return backup_path

def migrate_database_data(source_path: str, target_path: str) -> bool:
    """Migrate data from source database to target database."""
    logger.info(f"Migrating data from {source_path} to {target_path}")
    
    if not Path(source_path).exists():
        logger.warning(f"Source database {source_path} does not exist")
        return True  # No data to migrate is not an error
    
    try:
        # Initialize target database with migrations
        from backend.repositories.migrations import MigrationManager
        target_manager = MigrationManager(target_path)
        target_manager.migrate()
        
        # Connect to both databases
        source_conn = sqlite3.connect(source_path)
        target_conn = sqlite3.connect(target_path)
        
        # Get source database schema
        cursor = source_conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        source_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found tables in source: {source_tables}")
        
        # Get target database schema
        cursor = target_conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        target_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found tables in target: {target_tables}")
        
        migrated_records = 0
        
        # Migrate data for each table
        for table in source_tables:
            if table in ['schema_version']:  # Skip migration control tables
                continue
                
            if table in target_tables:
                # Get column info for the table
                cursor = source_conn.execute(f"PRAGMA table_info({table})")
                source_columns = [row[1] for row in cursor.fetchall()]
                
                cursor = target_conn.execute(f"PRAGMA table_info({table})")
                target_columns = [row[1] for row in cursor.fetchall()]
                
                # Use intersection of columns
                common_columns = [col for col in source_columns if col in target_columns]
                
                if common_columns:
                    logger.info(f"Migrating table {table} ({len(common_columns)} columns)")
                    
                    # Get data from source
                    cursor = source_conn.execute(f"SELECT {','.join(common_columns)} FROM {table}")
                    source_data = cursor.fetchall()
                    
                    if source_data:
                        # Insert into target (avoiding duplicates)
                        placeholders = ','.join(['?' for _ in common_columns])
                        
                        if table.endswith('s'):  # Likely has an 'id' column
                            insert_sql = f"""
                                INSERT OR IGNORE INTO {table} ({','.join(common_columns)})
                                VALUES ({placeholders})
                            """
                        else:
                            insert_sql = f"""
                                INSERT OR IGNORE INTO {table} ({','.join(common_columns)})
                                VALUES ({placeholders})
                            """
                        
                        target_conn.executemany(insert_sql, source_data)
                        migrated_records += len(source_data)
                        logger.info(f"Migrated {len(source_data)} records from {table}")
                else:
                    logger.warning(f"No common columns found for table {table}")
            else:
                logger.warning(f"Table {table} does not exist in target database")
        
        # Commit changes
        target_conn.commit()
        
        # Close connections
        source_conn.close()
        target_conn.close()
        
        logger.info(f"Migration completed. {migrated_records} total records migrated.")
        return True
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return False

def verify_migration(source_path: str, target_path: str) -> bool:
    """Verify that migration was successful by comparing data."""
    logger.info("Verifying migration results...")
    
    try:
        source_info = get_database_info(source_path)
        target_info = get_database_info(target_path)
        
        if not source_info['exists']:
            logger.info("Source database didn't exist - nothing to verify")
            return True
        
        logger.info("Source database info:")
        for table, count in source_info['record_counts'].items():
            logger.info(f"  {table}: {count}")
        
        logger.info("Target database info:")
        for table, count in target_info['record_counts'].items():
            logger.info(f"  {table}: {count}")
        
        # Check that all expected tables have data
        critical_tables = ['standards', 'objectives', 'sessions', 'lessons', 'users', 'images']
        
        for table in critical_tables:
            if table in source_info['record_counts']:
                source_count = source_info['record_counts'][table]
                target_count = target_info['record_counts'].get(table, 0)
                
                if isinstance(source_count, int) and isinstance(target_count, int):
                    if target_count >= source_count:
                        logger.info(f"✓ {table}: {target_count} records (≥ {source_count} source)")
                    else:
                        logger.error(f"✗ {table}: {target_count} records (< {source_count} source)")
                        return False
                else:
                    logger.warning(f"⚠ {table}: Cannot compare counts due to errors")
        
        logger.info("✓ Migration verification passed")
        return True
        
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        return False

def main():
    """Main consolidation function."""
    parser = argparse.ArgumentParser(description="Consolidate database files")
    parser.add_argument("--source-db", default="data/standards/standards.db", 
                       help="Source database path")
    parser.add_argument("--target-db", default="data/pocket_musec.db", 
                       help="Target database path")
    parser.add_argument("--backup", action="store_true", 
                       help="Create backup of target database")
    parser.add_argument("--verify-only", action="store_true",
                       help="Only verify migration, don't perform it")
    
    args = parser.parse_args()
    
    # Normalize paths
    source_path = Path(args.source_db)
    target_path = Path(args.target_db)
    
    logger.info("=== Database Consolidation Script ===")
    logger.info(f"Source: {source_path.absolute()}")
    logger.info(f"Target: {target_path.absolute()}")
    
    # Show current database information
    logger.info("\n=== Current Database Information ===")
    
    source_info = get_database_info(str(source_path))
    target_info = get_database_info(str(target_path))
    
    logger.info(f"Source database exists: {source_info['exists']}")
    if source_info['exists']:
        logger.info(f"Source size: {source_info['size_bytes']:,} bytes")
        for table, count in source_info['record_counts'].items():
            logger.info(f"  {table}: {count}")
    
    logger.info(f"Target database exists: {target_info['exists']}")
    if target_info['exists']:
        logger.info(f"Target size: {target_info['size_bytes']:,} bytes")
        for table, count in target_info['record_counts'].items():
            logger.info(f"  {table}: {count}")
    
    if args.verify_only:
        logger.info("\n=== Verification Mode ===")
        success = verify_migration(str(source_path), str(target_path))
        if success:
            logger.info("✓ Verification completed successfully")
        else:
            logger.error("✗ Verification failed")
            return 1
        return 0
    
    # Create backup if requested
    if args.backup and target_path.exists():
        backup_path = backup_database(str(target_path))
    
    # Ensure target directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Perform migration
    logger.info("\n=== Starting Migration ===")
    success = migrate_database_data(str(source_path), str(target_path))
    
    if not success:
        logger.error("Migration failed!")
        return 1
    
    # Verify migration
    logger.info("\n=== Verifying Migration ===")
    success = verify_migration(str(source_path), str(target_path))
    
    if not success:
        logger.error("Migration verification failed!")
        return 1
    
    logger.info("\n=== Consolidation Complete ===")
    logger.info("✓ Database consolidation completed successfully")
    logger.info(f"✓ All data consolidated into: {target_path.absolute()}")
    logger.info("\nNext steps:")
    logger.info("1. Update your .env file to use the new database path")
    logger.info("2. Test your application to ensure everything works")
    logger.info("3. After verification, you can remove old database files")
    
    return 0

if __name__ == "__main__":
    exit(main())