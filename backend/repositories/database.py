"""Database connection and initialization for pocket_musec"""

import sqlite3
from pathlib import Path
from typing import Optional

from backend.config import config


class DatabaseManager:
    """Manages SQLite database connections and initialization"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Use centralized configuration
            db_path = config.database.path

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_database(self) -> None:
        """Create database tables if they don't exist"""
        from .migrations import MigrationManager

        # Run migrations to ensure all tables exist
        migrator = MigrationManager(str(self.db_path))
        migrator.migrate()

    def database_exists(self) -> bool:
        """Check if database file exists"""
        return self.db_path.exists()
