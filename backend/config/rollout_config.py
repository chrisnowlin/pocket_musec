"""
PocketMuseC camelCase Migration Rollout Configuration

This module provides configuration management for gradual rollout of camelCase API responses.
Supports user group-based rollout, percentage-based rollout, and feature flag management.
"""

import os
import json
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class RolloutStrategy(Enum):
    """Rollout strategy types."""

    DISABLED = "disabled"
    INTERNAL_USERS = "internal_users"
    PERCENTAGE = "percentage"
    USER_GROUPS = "user_groups"
    ALL_USERS = "all_users"


class RolloutConfig:
    """Manages rollout configuration for camelCase migration."""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), "rollout_config.json"
        )
        self.config = self._load_config()
        self._user_cache = {}
        self._cache_expiry = {}

    def _load_config(self) -> Dict[str, Any]:
        """Load rollout configuration from file."""
        default_config = {
            "strategy": RolloutStrategy.DISABLED.value,
            "enabled": False,
            "percentage": 0,
            "user_groups": {"camelcase_enabled": [], "snakecase_default": True},
            "internal_users": [
                # Internal user IDs who always get camelCase
            ],
            "excluded_users": [
                # Users who should never get camelCase (e.g., integrations)
            ],
            "auto_rollout": {
                "enabled": False,
                "start_percentage": 1,
                "max_percentage": 100,
                "increment": 5,
                "interval_hours": 24,
                "error_threshold": 0.01,
                "performance_threshold": 1.1,
            },
            "monitoring": {
                "track_usage": True,
                "track_performance": True,
                "track_errors": True,
                "sample_rate": 1.0,
            },
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "version": "1.0",
            },
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all fields exist
                    config = {**default_config, **loaded_config}
                    logger.info(f"Loaded rollout config from {self.config_file}")
                    return config
            else:
                logger.info("Creating default rollout configuration")
                self._save_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Failed to load rollout config: {e}")
            return default_config

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save rollout configuration to file."""
        try:
            config["metadata"]["updated_at"] = datetime.utcnow().isoformat()
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved rollout config to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save rollout config: {e}")

    def is_camelcase_enabled_for_user(
        self, user_id: str, user_email: Optional[str] = None
    ) -> bool:
        """
        Check if camelCase is enabled for a specific user.

        Args:
            user_id: Unique user identifier
            user_email: User email (optional, for internal user detection)

        Returns:
            True if camelCase should be used for this user
        """
        # Check cache first
        cache_key = f"{user_id}:{user_email or ''}"
        if cache_key in self._user_cache:
            cached_result, cached_time = self._user_cache[cache_key]
            if datetime.utcnow() < cached_time:
                return cached_result

        result = self._calculate_camelcase_enabled(user_id, user_email)

        # Cache result for 5 minutes
        self._user_cache[cache_key] = (result, datetime.utcnow() + timedelta(minutes=5))

        return result

    def _calculate_camelcase_enabled(
        self, user_id: str, user_email: Optional[str] = None
    ) -> bool:
        """Calculate if camelCase should be enabled for user based on current strategy."""
        strategy = RolloutStrategy(
            self.config.get("strategy", RolloutStrategy.DISABLED.value)
        )

        # Check if user is explicitly excluded
        if user_id in self.config.get("excluded_users", []):
            return False

        # Check if user is explicitly included (internal users)
        if user_id in self.config.get("internal_users", []):
            return True

        # Check if user is in enabled groups
        enabled_groups = self.config.get("user_groups", {}).get("camelcase_enabled", [])
        if user_id in enabled_groups:
            return True

        # Apply strategy-based logic
        if strategy == RolloutStrategy.DISABLED:
            return False

        elif strategy == RolloutStrategy.INTERNAL_USERS:
            # Only internal users (already checked above)
            return False

        elif strategy == RolloutStrategy.PERCENTAGE:
            return self._is_user_in_percentage(user_id)

        elif strategy == RolloutStrategy.USER_GROUPS:
            # Check if user is in any enabled group (already checked above)
            return False

        elif strategy == RolloutStrategy.ALL_USERS:
            return True

        return False

    def _is_user_in_percentage(self, user_id: str) -> bool:
        """Determine if user falls within the percentage rollout."""
        percentage = self.config.get("percentage", 0)
        if percentage <= 0:
            return False
        if percentage >= 100:
            return True

        # Use consistent hashing to determine if user is in rollout percentage
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return (hash_value % 100) < percentage

    def update_strategy(self, strategy: RolloutStrategy, **kwargs) -> bool:
        """
        Update rollout strategy.

        Args:
            strategy: New rollout strategy
            **kwargs: Additional strategy-specific parameters

        Returns:
            True if update was successful
        """
        try:
            old_strategy = self.config.get("strategy")
            self.config["strategy"] = strategy.value

            # Update strategy-specific settings
            if strategy == RolloutStrategy.PERCENTAGE:
                if "percentage" in kwargs:
                    self.config["percentage"] = max(0, min(100, kwargs["percentage"]))
            elif strategy == RolloutStrategy.USER_GROUPS:
                if "enabled_groups" in kwargs:
                    self.config["user_groups"]["camelcase_enabled"] = kwargs[
                        "enabled_groups"
                    ]

            # Clear cache when strategy changes
            self._user_cache.clear()

            self._save_config(self.config)
            logger.info(
                f"Updated rollout strategy from {old_strategy} to {strategy.value}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update rollout strategy: {e}")
            return False

    def add_user_to_group(self, user_id: str, group: str = "camelcase_enabled") -> bool:
        """Add user to a specific rollout group."""
        try:
            if group not in self.config["user_groups"]:
                self.config["user_groups"][group] = []

            if user_id not in self.config["user_groups"][group]:
                self.config["user_groups"][group].append(user_id)
                self._user_cache.clear()  # Clear cache
                self._save_config(self.config)
                logger.info(f"Added user {user_id} to group {group}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to add user to group: {e}")
            return False

    def remove_user_from_group(
        self, user_id: str, group: str = "camelcase_enabled"
    ) -> bool:
        """Remove user from a specific rollout group."""
        try:
            if (
                group in self.config["user_groups"]
                and user_id in self.config["user_groups"][group]
            ):
                self.config["user_groups"][group].remove(user_id)
                self._user_cache.clear()  # Clear cache
                self._save_config(self.config)
                logger.info(f"Removed user {user_id} from group {group}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to remove user from group: {e}")
            return False

    def set_percentage(self, percentage: int) -> bool:
        """Set percentage rollout value."""
        try:
            percentage = max(0, min(100, percentage))
            self.config["percentage"] = percentage
            self._user_cache.clear()  # Clear cache
            self._save_config(self.config)
            logger.info(f"Set rollout percentage to {percentage}%")
            return True

        except Exception as e:
            logger.error(f"Failed to set percentage: {e}")
            return False

    def get_rollout_status(self) -> Dict[str, Any]:
        """Get current rollout status and statistics."""
        strategy = RolloutStrategy(
            self.config.get("strategy", RolloutStrategy.DISABLED.value)
        )

        status = {
            "strategy": strategy.value,
            "enabled": self.config.get("enabled", False),
            "percentage": self.config.get("percentage", 0),
            "enabled_users_count": len(
                self.config.get("user_groups", {}).get("camelcase_enabled", [])
            ),
            "internal_users_count": len(self.config.get("internal_users", [])),
            "excluded_users_count": len(self.config.get("excluded_users", [])),
            "auto_rollout_enabled": self.config.get("auto_rollout", {}).get(
                "enabled", False
            ),
            "last_updated": self.config.get("metadata", {}).get("updated_at"),
            "cache_size": len(self._user_cache),
        }

        return status

    def enable_auto_rollout(self, **kwargs) -> bool:
        """Enable automatic percentage-based rollout."""
        try:
            auto_config = self.config.get("auto_rollout", {})
            auto_config["enabled"] = True

            # Update auto-rollout parameters
            for key, value in kwargs.items():
                if key in auto_config:
                    auto_config[key] = value

            self.config["auto_rollout"] = auto_config
            self._save_config(self.config)
            logger.info("Enabled auto rollout")
            return True

        except Exception as e:
            logger.error(f"Failed to enable auto rollout: {e}")
            return False

    def disable_auto_rollout(self) -> bool:
        """Disable automatic percentage-based rollout."""
        try:
            self.config["auto_rollout"]["enabled"] = False
            self._save_config(self.config)
            logger.info("Disabled auto rollout")
            return True

        except Exception as e:
            logger.error(f"Failed to disable auto rollout: {e}")
            return False

    def should_increment_percentage(self) -> bool:
        """Check if percentage should be incremented based on auto-rollout rules."""
        auto_config = self.config.get("auto_rollout", {})
        if not auto_config.get("enabled", False):
            return False

        # Check if we've reached max percentage
        current_percentage = self.config.get("percentage", 0)
        max_percentage = auto_config.get("max_percentage", 100)
        if current_percentage >= max_percentage:
            return False

        # Check timing (simplified - in production, use proper scheduling)
        # This would be called by a scheduled job
        return True

    def increment_percentage(self) -> bool:
        """Increment rollout percentage according to auto-rollout configuration."""
        try:
            auto_config = self.config.get("auto_rollout", {})
            if not auto_config.get("enabled", False):
                return False

            current_percentage = self.config.get("percentage", 0)
            increment = auto_config.get("increment", 5)
            max_percentage = auto_config.get("max_percentage", 100)

            new_percentage = min(current_percentage + increment, max_percentage)
            return self.set_percentage(new_percentage)

        except Exception as e:
            logger.error(f"Failed to increment percentage: {e}")
            return False


# Global rollout configuration instance
rollout_config = RolloutConfig()


def is_camelcase_enabled_for_user(
    user_id: str, user_email: Optional[str] = None
) -> bool:
    """Convenience function to check if camelCase is enabled for a user."""
    return rollout_config.is_camelcase_enabled_for_user(user_id, user_email)


def get_rollout_status() -> Dict[str, Any]:
    """Convenience function to get current rollout status."""
    return rollout_config.get_rollout_status()
