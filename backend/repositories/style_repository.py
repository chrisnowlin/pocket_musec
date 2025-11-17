"""Style repository for database persistence of style configurations."""

import json
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from backend.repositories.database import DatabaseManager
from backend.models.style_schema import StyleConfig, StyleType, import_style_config
from backend.models.progress_tracking import DetailedProgress, ProgressStep


class StyleRepository:
    """Handles CRUD operations for style configurations."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize the style repository.

        Args:
            db_manager: Database manager instance (creates default if None)
        """
        self.db_manager = db_manager or DatabaseManager()
        self._ensure_tables_exist()

    def _ensure_tables_exist(self):
        """Create the styles table if it doesn't exist."""
        conn = self.db_manager.get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS styles (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    type TEXT NOT NULL,
                    user_id TEXT,
                    is_public BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    color_scheme TEXT DEFAULT 'default',
                    colors TEXT,
                    fonts TEXT,
                    layout TEXT,
                    transitions TEXT,
                    show_progress_indicator BOOLEAN DEFAULT TRUE,
                    show_slide_numbers BOOLEAN DEFAULT TRUE,
                    show_section_headers BOOLEAN DEFAULT TRUE,
                    use_animations BOOLEAN DEFAULT FALSE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
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
            conn.commit()
        finally:
            conn.close()

    def create_style(self, style: StyleConfig) -> StyleConfig:
        """Create a new style in the database.

        Args:
            style: Style configuration to create

        Returns:
            Created style with any database-generated values
        """
        conn = self.db_manager.get_connection()
        try:
            conn.execute("""
                INSERT INTO styles (
                    id, name, description, type, user_id, is_public, is_active,
                    color_scheme, colors, fonts, layout, transitions,
                    show_progress_indicator, show_slide_numbers, show_section_headers, use_animations,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                style.id,
                style.name,
                style.description,
                style.type.value,
                style.user_id,
                int(style.is_public),
                int(style.is_active),
                style.color_scheme.value,
                json.dumps(style.colors.model_dump()),
                json.dumps(style.fonts.model_dump()),
                json.dumps(style.layout.model_dump()),
                json.dumps(style.transitions.model_dump()),
                int(style.show_progress_indicator),
                int(style.show_slide_numbers),
                int(style.show_section_headers),
                int(style.use_animations),
                style.created_at.isoformat(),
                style.updated_at.isoformat(),
            ))
            conn.commit()
            return self.get_style(style.id)
        finally:
            conn.close()

    def get_style(self, style_id: str) -> Optional[StyleConfig]:
        """Get a style by ID.

        Args:
            style_id: ID of the style to retrieve

        Returns:
            Style configuration or None if not found
        """
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM styles WHERE id = ?", (style_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_style(row)
        finally:
            conn.close()

    def update_style(self, style_id: str, style: StyleConfig) -> StyleConfig:
        """Update an existing style.

        Args:
            style_id: ID of the style to update
            style: Updated style configuration

        Returns:
            Updated style configuration
        """
        conn = self.db_manager.get_connection()
        try:
            conn.execute("""
                UPDATE styles SET
                    name = ?, description = ?, type = ?, user_id = ?,
                    is_public = ?, is_active = ?, color_scheme = ?,
                    colors = ?, fonts = ?, layout = ?, transitions = ?,
                    show_progress_indicator = ?, show_slide_numbers = ?,
                    show_section_headers = ?, use_animations = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                style.name,
                style.description,
                style.type.value,
                style.user_id,
                int(style.is_public),
                int(style.is_active),
                style.color_scheme.value,
                json.dumps(style.colors.model_dump()),
                json.dumps(style.fonts.model_dump()),
                json.dumps(style.layout.model_dump()),
                json.dumps(style.transitions.model_dump()),
                int(style.show_progress_indicator),
                int(style.show_slide_numbers),
                int(style.show_section_headers),
                int(style.use_animations),
                style.updated_at.isoformat(),
                style_id,
            ))
            conn.commit()
            return self.get_style(style_id)
        finally:
            conn.close()

    def delete_style(self, style_id: str) -> bool:
        """Delete a style by ID.

        Args:
            style_id: ID of the style to delete

        Returns:
            True if deletion was successful
        """
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM styles WHERE id = ?", (style_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def list_styles_by_user(
        self,
        user_id: str,
        include_public: bool = True,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[StyleConfig], int]:
        """List styles for a specific user.

        Args:
            user_id: User ID to list styles for
            include_public: Whether to include public styles
            page: Page number (1-based)
            page_size: Number of styles per page

        Returns:
            Tuple of (styles list, total count)
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 50

        conn = self.db_manager.get_connection()
        try:
            # Get total count
            if include_public:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM styles
                    WHERE (user_id = ? AND is_active = TRUE)
                    OR (is_public = TRUE AND is_active = TRUE)
                """, (user_id,))
            else:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM styles
                    WHERE user_id = ? AND is_active = TRUE
                """, (user_id,))
            total_count = cursor.fetchone()[0]

            # Get paginated results
            offset = (page - 1) * page_size
            if include_public:
                cursor = conn.execute("""
                    SELECT * FROM styles
                    WHERE (user_id = ? AND is_active = TRUE)
                    OR (is_public = TRUE AND is_active = TRUE)
                    ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?
                """, (user_id, page_size, offset))
            else:
                cursor = conn.execute("""
                    SELECT * FROM styles
                    WHERE user_id = ? AND is_active = TRUE
                    ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?
                """, (user_id, page_size, offset))

            styles = [self._row_to_style(row) for row in cursor.fetchall()]
            return styles, total_count
        finally:
            conn.close()

    def list_public_styles(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> List[StyleConfig]:
        """List public styles.

        Args:
            page: Page number (1-based)
            page_size: Number of styles per page

        Returns:
            List of public style configurations
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20

        conn = self.db_manager.get_connection()
        try:
            offset = (page - 1) * page_size
            cursor = conn.execute("""
                SELECT * FROM styles
                WHERE is_public = TRUE AND is_active = TRUE
                AND type != 'preset'  # Exclude presets since they're handled separately
                ORDER BY name ASC
                LIMIT ? OFFSET ?
            """, (page_size, offset))

            return [self._row_to_style(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def search_styles(
        self,
        query: str,
        user_id: Optional[str] = None,
        include_public: bool = True,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[StyleConfig], int]:
        """Search styles by name or description.

        Args:
            query: Search query string
            user_id: Optional user ID to restrict search to
            include_public: Whether to include public styles in search
            page: Page number (1-based)
            page_size: Number of styles per page

        Returns:
            Tuple of (matching styles list, total count)
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20

        conn = self.db_manager.get_connection()
        try:
            search_term = f"%{query}%"

            # Build WHERE clause based on parameters
            where_conditions = ["is_active = TRUE"]
            params = []

            if user_id:
                where_conditions.append("user_id = ?")
                params.append(user_id)

            if include_public:
                where_conditions.append("(is_public = TRUE OR user_id = ?)")
                params.extend([user_id] if user_id else [""])
            else:
                where_conditions.append("user_id = ? AND is_public = FALSE")
                params.extend([user_id] if user_id else [""])

            where_clause = " AND ".join(where_conditions)

            # Get total count
            count_query = f"""
                SELECT COUNT(*) FROM styles
                WHERE {where_clause} AND (
                    name LIKE ? OR description LIKE ?
                )
            """
            cursor = conn.execute(count_query, params + [search_term, search_term])
            total_count = cursor.fetchone()[0]

            # Get search results
            offset = (page - 1) * page_size
            search_query = f"""
                SELECT * FROM styles
                WHERE {where_clause} AND (
                    name LIKE ? OR description LIKE ?
                )
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """
            cursor = conn.execute(
                search_query,
                params + [search_term, search_term, page_size, offset]
            )

            styles = [self._row_to_style(row) for row in cursor.fetchall()]
            return styles, min(total_count, page_size * (page if page > 0 else 1))
        finally:
            conn.close()

    def get_style_usage_stats(self, style_id: str) -> Dict[str, Any]:
        """Get usage statistics for a style.

        Args:
            style_id: ID of the style to get stats for

        Returns:
            Dictionary with usage statistics
        """
        conn = self.db_manager.get_connection()
        try:
            # Count presentations using this style
            cursor = conn.execute("""
                SELECT COUNT(*) FROM presentations
                WHERE style = ? AND status = 'complete'
            """, (style_id,))
            presentation_count = cursor.fetchone()[0]

            # Get style details
            cursor = conn.execute("""
                SELECT created_at, updated_at FROM styles WHERE id = ?
            """, (style_id,))
            row = cursor.fetchone()
            if not row:
                return {"presentation_count": 0, "created_at": None, "updated_at": None}

            return {
                "presentation_count": presentation_count,
                "created_at": row[0],
                "updated_at": row[1],
            }
        finally:
            conn.close()

    def cleanup_old_styles(self, days_old: int = 365) -> int:
        """Clean up old inactive styles.

        Args:
            days_old: Minimum age in days for styles to be eligible for cleanup

        Returns:
            Number of styles cleaned up
        """
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                DELETE FROM styles
                WHERE is_active = FALSE
                AND updated_at < datetime('now', '-{} days')
                AND type != 'preset'
            """.format(days_old))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def _row_to_style(self, row) -> StyleConfig:
        """Convert database row to StyleConfig.

        Args:
            row: Database row containing style data

        Returns:
            StyleConfig instance
        """
        # Parse JSON fields
        colors_dict = json.loads(row[9]) if row[9] and isinstance(row[9], str) else {}
        fonts_dict = json.loads(row[10]) if row[10] and isinstance(row[10], str) else {}
        layout_dict = json.loads(row[11]) if row[11] and isinstance(row[11], str) else {}
        transitions_dict = json.loads(row[12]) if row[12] and isinstance(row[12], str) else {}

        from backend.models.style_schema import (
            ColorPalette, FontConfig, LayoutConfig, TransitionConfig,
            ColorScheme, StyleType
        )

        # Create the config objects from dictionaries
        colors_obj = ColorPalette(**colors_dict) if colors_dict else ColorPalette()
        fonts_obj = FontConfig(**fonts_dict) if fonts_dict else FontConfig()
        layout_obj = LayoutConfig(**layout_dict) if layout_dict else LayoutConfig()
        transitions_obj = TransitionConfig(**transitions_dict) if transitions_dict else TransitionConfig()

        style_data = {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "type": StyleType(row[3] if row[3] else "custom"),
            "user_id": row[4],
            "is_public": bool(row[5]),
            "is_active": bool(row[6]),
            "color_scheme": ColorScheme(row[7] if row[7] else "default"),
            "colors": colors_obj,
            "fonts": fonts_obj,
            "layout": layout_obj,
            "transitions": transitions_obj,
            "show_progress_indicator": bool(row[13]),
            "show_slide_numbers": bool(row[14]),
            "show_section_headers": bool(row[15]),
            "use_animations": bool(row[16]),
            "created_at": datetime.fromisoformat(row[17]),
            "updated_at": datetime.fromisoformat(row[18]),
        }

        return StyleConfig(**style_data)