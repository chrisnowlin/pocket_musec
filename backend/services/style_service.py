"""Style management service for presentation generation.

This service handles style validation, processing, and application to
presentation generation with database persistence.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime

from backend.repositories.style_repository import StyleRepository
from backend.models.style_schema import (
    StyleConfig,
    StyleType,
    PresetStyle,
    StyleTemplate,
    validate_style_config,
    merge_styles,
    export_style_config,
    import_style_config,
)
from backend.repositories.database import DatabaseManager

logger = logging.getLogger(__name__)


class StyleValidationError(Exception):
    """Style validation error."""

    pass


class StyleNotFoundError(Exception):
    """Style not found error."""

    pass


class StyleAccessDeniedError(Exception):
    """Style access denied error."""

    pass


class StyleService:
    """Service for managing style configurations."""

    def __init__(
        self,
        style_repo: Optional[StyleRepository] = None,
        db_manager: Optional[DatabaseManager] = None,
    ):
        """Initialize the style service.

        Args:
            style_repo: Style repository instance (creates default if None)
            db_manager: Database manager instance (creates default if None)
        """
        self.db_manager = db_manager or DatabaseManager()
        self.style_repo = style_repo or StyleRepository(self.db_manager)

        # Load preset styles into memory for quick access
        self._preset_styles = PresetStyle.get_default_presets()
        self._preset_dict = {preset.id: preset for preset in self._preset_styles}

    def get_available_presets(self) -> List[Dict[str, Any]]:
        """Get all available preset styles.

        Returns:
            List of preset style dictionaries with ID, name, description
        """
        return [
            {
                "id": preset.id,
                "name": preset.config.name,
                "description": preset.config.description,
                "config": preset.config.to_dict(),
            }
            for preset in self._preset_styles
        ]

    def get_preset_style(self, preset_id: str) -> Optional[StyleConfig]:
        """Get a preset style configuration.

        Args:
            preset_id: ID of the preset style

        Returns:
            StyleConfig for the preset, or None if not found

        Raises:
            StyleNotFoundError: If preset_id is not a valid preset
        """
        preset = self._preset_dict.get(preset_id)
        if not preset:
            raise StyleNotFoundError(f"Preset style '{preset_id}' not found")
        return preset.config

    def create_style(
        self,
        name: str,
        description: Optional[str],
        config: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        template: Optional[StyleTemplate] = None,
    ) -> StyleConfig:
        """Create a new style configuration.

        Args:
            name: Name of the style
            description: Optional description
            config: Optional style configuration dict (overrides template)
            user_id: Optional user ID (for user-specific styles)
            template: Optional template to base style on

        Returns:
            Created StyleConfig

        Raises:
            StyleValidationError: If style configuration is invalid
        """
        try:
            if template and config:
                raise StyleValidationError("Cannot provide both template and config")

            if template:
                # Create from template
                template.name = name
                template.description = description
                style = template.create_style(user_id)
            elif config:
                # Create from config dict
                config["name"] = name
                config["description"] = description
                config["type"] = StyleType.USER
                if user_id:
                    config["user_id"] = user_id
                style = import_style_config(config, validate=True)
                if not style:
                    raise StyleValidationError("Invalid style configuration")
            else:
                # Create empty user style with defaults
                style = StyleConfig(
                    name=name,
                    description=description,
                    type=StyleType.USER,
                    user_id=user_id,
                )

            # Validate the style
            if not validate_style_config(style):
                raise StyleValidationError("Style configuration validation failed")

            # Save to database
            try:
                saved_style = self.style_repo.create_style(style)
                logger.info(
                    f"Created style '{saved_style.name}' (ID: {saved_style.id}) for user {user_id}"
                )
                return saved_style
            except Exception as db_error:
                logger.error(f"Database error creating style: {db_error}")
                raise StyleValidationError(
                    f"Failed to save style to database: {str(db_error)}"
                )

        except (StyleValidationError, StyleNotFoundError, StyleAccessDeniedError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating style: {e}")
            raise StyleValidationError(f"Failed to create style: {str(e)}")

    def get_style(self, style_id: str, user_id: Optional[str] = None) -> StyleConfig:
        """Get a style configuration by ID.

        Args:
            style_id: ID of the style
            user_id: Optional user ID for access control

        Returns:
            StyleConfig for the requested style

        Raises:
            StyleNotFoundError: If style not found
            StyleAccessDeniedError: If user doesn't have access to the style
        """
        # Check if it's a preset
        if style_id in self._preset_dict:
            return self._preset_dict[style_id].config

        # Get from database
        try:
            style = self.style_repo.get_style(style_id)
            if not style:
                raise StyleNotFoundError(f"Style with ID '{style_id}' not found")
        except Exception as db_error:
            logger.error(f"Database error retrieving style {style_id}: {db_error}")
            raise StyleNotFoundError(
                f"Failed to retrieve style '{style_id}': {str(db_error)}"
            )

        # Check access control
        if not self._can_access_style(style, user_id):
            raise StyleAccessDeniedError(f"Access denied to style '{style_id}'")

        return style

    def update_style(
        self, style_id: str, updates: Dict[str, Any], user_id: Optional[str] = None
    ) -> StyleConfig:
        """Update a style configuration.

        Args:
            style_id: ID of the style to update
            updates: Dictionary of updates to apply
            user_id: Optional user ID for access control

        Returns:
            Updated StyleConfig

        Raises:
            StyleNotFoundError: If style not found
            StyleAccessDeniedError: If user doesn't have permission to update
            StyleValidationError: If updates are invalid
        """
        # Get existing style
        existing_style = self.get_style(style_id, user_id)

        # Check update permissions (user can only update their own styles)
        if existing_style.type == StyleType.PRESET:
            raise StyleAccessDeniedError("Cannot update preset styles")
        if existing_style.user_id and existing_style.user_id != user_id:
            raise StyleAccessDeniedError("Cannot update style owned by another user")

        # Apply updates
        updated_data = existing_style.to_dict()
        updated_data.update(updates)

        # Validate the updated style
        updated_style = import_style_config(updated_data, validate=True)
        if not updated_style:
            raise StyleValidationError("Updated style configuration is invalid")

        # Update timestamp
        updated_style.update_timestamp()

        # Save to database
        try:
            saved_style = self.style_repo.update_style(style_id, updated_style)
            logger.info(f"Updated style '{saved_style.name}' (ID: {style_id})")
            return saved_style
        except Exception as db_error:
            logger.error(f"Database error updating style {style_id}: {db_error}")
            raise StyleValidationError(f"Failed to update style: {str(db_error)}")

    def delete_style(self, style_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a style configuration.

        Args:
            style_id: ID of the style to delete
            user_id: Optional user ID for access control

        Returns:
            True if deletion was successful

        Raises:
            StyleNotFoundError: If style not found
            StyleAccessDeniedError: If user doesn't have permission to delete
        """
        # Get existing style
        existing_style = self.get_style(style_id, user_id)

        # Check delete permissions
        if existing_style.type == StyleType.PRESET:
            raise StyleAccessDeniedError("Cannot delete preset styles")
        if existing_style.user_id and existing_style.user_id != user_id:
            raise StyleAccessDeniedError("Cannot delete style owned by another user")

        # Delete from database
        try:
            success = self.style_repo.delete_style(style_id)
            if success:
                logger.info(f"Deleted style '{existing_style.name}' (ID: {style_id})")
            else:
                logger.warning(
                    f"Failed to delete style '{existing_style.name}' (ID: {style_id})"
                )
            return success
        except Exception as db_error:
            logger.error(f"Database error deleting style {style_id}: {db_error}")
            raise StyleValidationError(f"Failed to delete style: {str(db_error)}")

    def list_user_styles(
        self,
        user_id: str,
        include_public: bool = True,
        include_presets: bool = True,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[StyleConfig], int]:
        """List styles available to a user.

        Args:
            user_id: User ID to list styles for
            include_public: Whether to include public styles
            include_presets: Whether to include preset styles
            page: Page number (1-based)
            page_size: Number of styles per page

        Returns:
            Tuple of (styles list, total count)
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 50
        if page_size > 100:
            page_size = 100

        # Get user's custom styles from database
        try:
            user_styles, total_count = self.style_repo.list_styles_by_user(
                user_id=user_id,
                include_public=include_public,
                page=page,
                page_size=page_size,
            )
        except Exception as db_error:
            logger.error(
                f"Database error listing styles for user {user_id}: {db_error}"
            )
            user_styles, total_count = [], 0

        all_styles = list(user_styles)

        # Add preset styles if requested
        if include_presets and page == 1:  # Only include presets on first page
            preset_styles = [preset.config for preset in self._preset_styles]
            all_styles.extend(preset_styles)
            total_count += len(preset_styles)

        # Add public styles if requested and not already included
        if include_public:
            public_styles = self.style_repo.list_public_styles(page=1, page_size=20)
            for style in public_styles:
                if style not in all_styles:
                    all_styles.append(style)
                    total_count += 1

        # Apply pagination to combined results
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_styles = all_styles[start_idx:end_idx]

        return paginated_styles, min(total_count, page_size * len(all_styles))

    def search_styles(
        self,
        query: str,
        user_id: Optional[str] = None,
        search_type: str = "all",  # "all", "user", "preset", "public"
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[StyleConfig], int]:
        """Search for styles by name or description.

        Args:
            query: Search query string
            user_id: Optional user ID for access control
            search_type: Type of search to perform
            page: Page number (1-based)
            page_size: Number of styles per page

        Returns:
            Tuple of (matching styles list, total count)
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > 50:
            page_size = 50

        results = []
        total_count = 0

        # Search presets
        if search_type in ["all", "preset"]:
            for preset in self._preset_styles:
                if query.lower() in preset.config.name.lower() or (
                    preset.config.description
                    and query.lower() in preset.config.description.lower()
                ):
                    results.append(preset.config)
                    total_count += 1

        # Search user styles and public styles
        if search_type in ["all", "user", "public"]:
            try:
                db_results, db_count = self.style_repo.search_styles(
                    query=query,
                    user_id=(user_id if search_type == "user" else None),
                    include_public=(search_type in ["all", "public"]),
                    page=page,
                    page_size=page_size,
                )
                results.extend(db_results)
                total_count += db_count
            except Exception as db_error:
                logger.error(f"Database error searching styles: {db_error}")
                # Continue with preset results only

        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_results = results[start_idx:end_idx]

        return paginated_results, len(results)

    def validate_and_apply_style(
        self, style_config: Union[str, StyleConfig], user_id: Optional[str] = None
    ) -> StyleConfig:
        """Validate and prepare style configuration for use in presentation generation.

        Args:
            style_config: Style configuration to validate
            user_id: Optional user ID for access control

        Returns:
            Validated and processed StyleConfig

        Raises:
            StyleValidationError: If style configuration is invalid
            StyleAccessDeniedError: If user doesn't have access to the style
        """
        # If it's a preset ID, get the preset config
        if isinstance(style_config, str):
            style_config = self.get_style(style_config, user_id)

        # Validate the style
        if not validate_style_config(style_config):
            raise StyleValidationError("Invalid style configuration")

        # For user styles, ensure they have access
        if (
            style_config.type == StyleType.USER
            and style_config.user_id
            and style_config.user_id != user_id
        ):
            raise StyleAccessDeniedError("Access denied to user-owned style")

        # Ensure style is active
        if not style_config.is_active:
            raise StyleValidationError("Style is not active")

        return style_config

    def export_style(
        self, style_id: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Export a style configuration.

        Args:
            style_id: ID of the style to export
            user_id: Optional user ID for access control

        Returns:
            Exportable style configuration dictionary

        Raises:
            StyleNotFoundError: If style not found
            StyleAccessDeniedError: If user doesn't have access to the style
        """
        style = self.get_style(style_id, user_id)
        return export_style_config(style)

    def import_style(
        self,
        style_data: Dict[str, Any],
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        merge_with: Optional[str] = None,
    ) -> StyleConfig:
        """Import a style configuration.

        Args:
            style_data: Style configuration data to import
            name: Optional name to override the imported style name
            user_id: Optional user ID for the imported style
            merge_with: Optional style ID to merge with

        Returns:
            Imported StyleConfig

        Raises:
            StyleValidationError: If import data is invalid
            StyleNotFoundError: If merge_with style not found
        """
        # Import the style data
        imported_style = import_style_config(style_data, validate=True)
        if not imported_style:
            raise StyleValidationError("Invalid style configuration data")

        # Override name if provided
        if name:
            imported_style.name = name

        # Set user ID and type for imported styles
        imported_style.user_id = user_id
        imported_style.type = StyleType.USER
        imported_style.is_public = False  # Imported styles are private by default

        # Merge with existing style if requested
        if merge_with:
            base_style = self.get_style(merge_with, user_id)
            imported_style = merge_styles(base_style, imported_style)

        # Create the style
        return self.create_style(
            name=imported_style.name,
            description=imported_style.description,
            config=imported_style.to_dict(),
            user_id=user_id,
        )

    def create_style_from_template(
        self, template: StyleTemplate, user_id: Optional[str] = None
    ) -> StyleConfig:
        """Create a style from a template.

        Args:
            template: Style template to create from
            user_id: Optional user ID for the created style

        Returns:
            Created StyleConfig

        Raises:
            StyleValidationError: If template is invalid
        """
        style = template.create_style(user_id)
        if not validate_style_config(style):
            raise StyleValidationError("Invalid style from template")

        return self.create_style(
            name=style.name,
            description=style.description,
            config=style.to_dict(),
            user_id=user_id,
        )

    def _can_access_style(self, style: StyleConfig, user_id: Optional[str]) -> bool:
        """Check if user can access a style.

        Args:
            style: Style to check access for
            user_id: User ID to check

        Returns:
            True if user can access the style
        """
        # Preset styles are public
        if style.type == StyleType.PRESET:
            return True

        # Public styles are accessible by anyone
        if style.is_public:
            return True

        # User-specific styles require matching user ID
        if style.user_id:
            return style.user_id == user_id

        # Default to denied
        return False

    def get_style_usage_stats(
        self, style_id: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get usage statistics for a style.

        Args:
            style_id: ID of the style
            user_id: Optional user ID for access control

        Returns:
            Dictionary with usage statistics

        Raises:
            StyleNotFoundError: If style not found
            StyleAccessDeniedError: If user doesn't have access to the style
        """
        style = self.get_style(style_id, user_id)
        try:
            return self.style_repo.get_style_usage_stats(style_id)
        except Exception as db_error:
            logger.error(
                f"Database error getting usage stats for style {style_id}: {db_error}"
            )
            return {
                "usage_count": 0,
                "last_used": None,
                "presentations_created": 0,
                "error": "Failed to retrieve usage statistics",
            }

    def copy_style(
        self, style_id: str, new_name: str, user_id: Optional[str] = None
    ) -> StyleConfig:
        """Create a copy of an existing style.

        Args:
            style_id: ID of the style to copy
            new_name: Name for the copied style
            user_id: Optional user ID for the copied style (defaults to original owner)

        Returns:
            New StyleConfig that is a copy of the original

        Raises:
            StyleNotFoundError: If original style not found
            StyleAccessDeniedError: If user doesn't have access to copy the style
        """
        original_style = self.get_style(style_id, user_id)

        # Create copy
        copy_data = original_style.to_dict()
        copy_data["name"] = new_name
        copy_data["description"] = f"Copy of {original_style.name}" + (
            f": {original_style.description}" if original_style.description else ""
        )
        copy_data.pop("id", None)  # Remove ID to generate new one
        copy_data.pop("created_at", None)
        copy_data.pop("updated_at", None)

        # Set ownership
        if user_id:
            copy_data["user_id"] = user_id
            copy_data["type"] = StyleType.USER
            copy_data["is_public"] = False

        return self.create_style(
            name=new_name,
            description=copy_data["description"],
            config=copy_data,
            user_id=copy_data.get("user_id"),
        )
