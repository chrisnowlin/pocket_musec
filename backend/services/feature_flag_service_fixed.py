"""
PocketMuseC Feature Flag Service

Manages feature flags for camelCase migration and other feature rollouts.
Integrates with the rollout configuration system to provide dynamic feature control.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from enum import Enum
import threading
from dataclasses import dataclass, asdict

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from config.rollout_config import rollout_config, RolloutStrategy

    ROLLOUT_CONFIG_AVAILABLE = True
except ImportError:
    ROLLOUT_CONFIG_AVAILABLE = False
    rollout_config = None
    RolloutStrategy = None

logger = logging.getLogger(__name__)


class FlagType(Enum):
    """Types of feature flags."""

    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"


@dataclass
class FeatureFlag:
    """Feature flag definition."""

    name: str
    flag_type: FlagType
    enabled: bool
    value: Any = None
    description: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: Optional[List[str]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.tags is None:
            self.tags = []


class FeatureFlagService:
    """Service for managing feature flags with Redis caching."""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = None
        self._flags = {}
        self._lock = threading.RLock()
        self._cache_ttl = 300  # 5 minutes
        self._init_redis()
        self._load_default_flags()

    def _init_redis(self):
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available. Using in-memory cache only.")
            self.redis_client = None
            return

        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Connected to Redis for feature flag caching")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory cache only.")
            self.redis_client = None

    def _load_default_flags(self):
        """Load default feature flags."""
        default_flags = {
            "CAMELCASE_API_RESPONSES": FeatureFlag(
                name="CAMELCASE_API_RESPONSES",
                flag_type=FlagType.BOOLEAN,
                enabled=False,
                description="Enable camelCase API responses instead of snake_case",
                tags=["api", "migration", "camelcase"],
            ),
            "CAMELCASE_ROLLOUT_ENABLED": FeatureFlag(
                name="CAMELCASE_ROLLOUT_ENABLED",
                flag_type=FlagType.BOOLEAN,
                enabled=False,
                description="Enable gradual rollout of camelCase responses",
                tags=["api", "migration", "rollout"],
            ),
            "ADVANCED_FIELD_MAPPING": FeatureFlag(
                name="ADVANCED_FIELD_MAPPING",
                flag_type=FlagType.BOOLEAN,
                enabled=True,
                description="Enable advanced field mapping with custom rules",
                tags=["api", "utilities", "mapping"],
            ),
            "MIGRATION_ANALYTICS": FeatureFlag(
                name="MIGRATION_ANALYTICS",
                flag_type=FlagType.BOOLEAN,
                enabled=True,
                description="Enable analytics tracking for migration usage",
                tags=["analytics", "migration", "monitoring"],
            ),
            "PERFORMANCE_MONITORING": FeatureFlag(
                name="PERFORMANCE_MONITORING",
                flag_type=FlagType.BOOLEAN,
                enabled=True,
                description="Enable performance monitoring for format conversion",
                tags=["performance", "monitoring", "migration"],
            ),
        }

        with self._lock:
            self._flags.update(default_flags)

        # Cache in Redis if available
        if self.redis_client:
            self._cache_flags_in_redis()

    def _cache_flags_in_redis(self):
        """Cache all flags in Redis."""
        if not self.redis_client:
            return

        try:
            for flag_name, flag in self._flags.items():
                flag_data = {
                    **asdict(flag),
                    "created_at": flag.created_at.isoformat()
                    if flag.created_at
                    else None,
                    "updated_at": flag.updated_at.isoformat()
                    if flag.updated_at
                    else None,
                    "flag_type": flag.flag_type.value,
                }
                self.redis_client.setex(
                    f"feature_flag:{flag_name}", self._cache_ttl, json.dumps(flag_data)
                )
        except Exception as e:
            logger.error(f"Failed to cache flags in Redis: {e}")

    def _load_flag_from_redis(self, flag_name: str) -> Optional[FeatureFlag]:
        """Load a specific flag from Redis cache."""
        if not self.redis_client:
            return None

        try:
            cached_data = self.redis_client.get(f"feature_flag:{flag_name}")
            if cached_data:
                data = json.loads(cached_data)
                data["flag_type"] = FlagType(data["flag_type"])
                if data.get("created_at"):
                    data["created_at"] = datetime.fromisoformat(data["created_at"])
                if data.get("updated_at"):
                    data["updated_at"] = datetime.fromisoformat(data["updated_at"])
                return FeatureFlag(**data)
        except Exception as e:
            logger.error(f"Failed to load flag {flag_name} from Redis: {e}")

        return None

    def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get a feature flag by name."""
        # Try Redis cache first
        cached_flag = self._load_flag_from_redis(flag_name)
        if cached_flag:
            return cached_flag

        # Fall back to in-memory cache
        with self._lock:
            return self._flags.get(flag_name)

    def is_enabled(
        self, flag_name: str, user_id: Optional[str] = None, **kwargs
    ) -> bool:
        """
        Check if a feature flag is enabled for a specific user or context.

        Args:
            flag_name: Name of the feature flag
            user_id: User ID (for user-specific flags)
            **kwargs: Additional context for flag evaluation

        Returns:
            True if the flag is enabled for the given context
        """
        flag = self.get_flag(flag_name)
        if not flag:
            return False

        if not flag.enabled:
            return False

        # Handle different flag types
        if flag.flag_type == FlagType.BOOLEAN:
            return flag.value if flag.value is not None else True

        elif flag.flag_type == FlagType.PERCENTAGE:
            if user_id and flag.value is not None:
                import hashlib

                hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
                return (hash_value % 100) < flag.value
            return False

        elif flag.flag_type == FlagType.USER_LIST:
            if user_id and flag.value:
                return user_id in flag.value
            return False

        elif flag.flag_type == FlagType.WHITELIST:
            if user_id and flag.value:
                return user_id in flag.value
            return False

        elif flag.flag_type == FlagType.BLACKLIST:
            if user_id and flag.value:
                return user_id not in flag.value
            return True

        return False

    def set_flag(
        self,
        flag_name: str,
        enabled: bool,
        value: Any = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Set a feature flag.

        Args:
            flag_name: Name of the feature flag
            enabled: Whether the flag is enabled
            value: Flag value (for percentage, user lists, etc.)
            description: Flag description
            tags: List of tags for categorization

        Returns:
            True if the flag was set successfully
        """
        try:
            with self._lock:
                if flag_name in self._flags:
                    flag = self._flags[flag_name]
                    flag.enabled = enabled
                    flag.value = value
                    flag.updated_at = datetime.utcnow()
                    if description:
                        flag.description = description
                    if tags:
                        flag.tags = tags
                else:
                    flag = FeatureFlag(
                        name=flag_name,
                        flag_type=FlagType.BOOLEAN,
                        enabled=enabled,
                        value=value,
                        description=description or "",
                        tags=tags or [],
                    )
                    self._flags[flag_name] = flag

            # Update Redis cache
            if self.redis_client:
                flag_data = {
                    **asdict(flag),
                    "created_at": flag.created_at.isoformat()
                    if flag.created_at
                    else None,
                    "updated_at": flag.updated_at.isoformat()
                    if flag.updated_at
                    else None,
                    "flag_type": flag.flag_type.value,
                }
                self.redis_client.setex(
                    f"feature_flag:{flag_name}", self._cache_ttl, json.dumps(flag_data)
                )

            logger.info(
                f"Set feature flag {flag_name}: enabled={enabled}, value={value}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to set feature flag {flag_name}: {e}")
            return False

    def update_flag(self, flag_name: str, **kwargs) -> bool:
        """Update an existing feature flag."""
        flag = self.get_flag(flag_name)
        if not flag:
            return False

        return self.set_flag(
            flag_name=flag_name,
            enabled=kwargs.get("enabled", flag.enabled),
            value=kwargs.get("value", flag.value),
            description=kwargs.get("description", flag.description),
            tags=kwargs.get("tags", flag.tags),
        )

    def delete_flag(self, flag_name: str) -> bool:
        """Delete a feature flag."""
        try:
            with self._lock:
                if flag_name in self._flags:
                    del self._flags[flag_name]

            # Remove from Redis
            if self.redis_client:
                self.redis_client.delete(f"feature_flag:{flag_name}")

            logger.info(f"Deleted feature flag {flag_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete feature flag {flag_name}: {e}")
            return False

    def list_flags(self, tag_filter: Optional[str] = None) -> List[FeatureFlag]:
        """List all feature flags, optionally filtered by tag."""
        flags = list(self._flags.values())

        if tag_filter:
            flags = [flag for flag in flags if tag_filter in flag.tags]

        return flags

    def get_flag_stats(self) -> Dict[str, Any]:
        """Get statistics about feature flags."""
        flags = list(self._flags.values())

        stats = {
            "total_flags": len(flags),
            "enabled_flags": len([f for f in flags if f.enabled]),
            "disabled_flags": len([f for f in flags if not f.enabled]),
            "flag_types": {},
            "tags": {},
            "cache_status": "redis" if self.redis_client else "memory_only",
        }

        # Count by type
        for flag in flags:
            flag_type = flag.flag_type.value
            stats["flag_types"][flag_type] = stats["flag_types"].get(flag_type, 0) + 1

        # Count by tags
        for flag in flags:
            for tag in flag.tags:
                stats["tags"][tag] = stats["tags"].get(tag, 0) + 1

        return stats

    def integrate_with_rollout_config(self) -> bool:
        """Integrate feature flags with rollout configuration."""
        if not ROLLOUT_CONFIG_AVAILABLE or rollout_config is None:
            logger.warning("Rollout config not available, skipping integration")
            return False

        try:
            # Sync camelCase rollout status with feature flags
            rollout_status = rollout_config.get_rollout_status()

            # Set CAMELCASE_API_RESPONSES based on rollout strategy
            if rollout_status["strategy"] == RolloutStrategy.ALL_USERS.value:
                self.set_flag("CAMELCASE_API_RESPONSES", True)
            elif rollout_status["strategy"] == RolloutStrategy.DISABLED.value:
                self.set_flag("CAMELCASE_API_RESPONSES", False)
            else:
                # For gradual rollout, keep the flag enabled but let rollout config handle specifics
                self.set_flag("CAMELCASE_API_RESPONSES", True)

            # Set CAMELCASE_ROLLOUT_ENABLED
            rollout_enabled = rollout_status["strategy"] not in [
                RolloutStrategy.DISABLED.value,
                RolloutStrategy.ALL_USERS.value,
            ]
            self.set_flag("CAMELCASE_ROLLOUT_ENABLED", rollout_enabled)

            logger.info("Integrated feature flags with rollout configuration")
            return True

        except Exception as e:
            logger.error(f"Failed to integrate with rollout config: {e}")
            return False

    def clear_cache(self) -> bool:
        """Clear all caches."""
        try:
            # Clear in-memory cache
            with self._lock:
                self._flags.clear()

            # Clear Redis cache
            if self.redis_client:
                keys = self.redis_client.keys("feature_flag:*")
                if keys:
                    self.redis_client.delete(*keys)

            # Reload default flags
            self._load_default_flags()

            logger.info("Cleared feature flag caches")
            return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False


# Global feature flag service instance
feature_flag_service = FeatureFlagService()


def is_camelcase_enabled(user_id: Optional[str] = None) -> bool:
    """
    Check if camelCase is enabled for a user.
    Integrates both feature flags and rollout configuration.
    """
    # Check feature flag first
    if not feature_flag_service.is_enabled("CAMELCASE_API_RESPONSES"):
        return False

    # If rollout is enabled, use rollout configuration
    if feature_flag_service.is_enabled("CAMELCASE_ROLLOUT_ENABLED"):
        if ROLLOUT_CONFIG_AVAILABLE and rollout_config is not None:
            return rollout_config.is_camelcase_enabled_for_user(user_id)
        else:
            # Fallback to feature flag if rollout config not available
            return feature_flag_service.is_enabled("CAMELCASE_API_RESPONSES", user_id)

    # Otherwise, use the feature flag value
    return feature_flag_service.is_enabled("CAMELCASE_API_RESPONSES", user_id)


def get_feature_flag(flag_name: str) -> Optional[FeatureFlag]:
    """Get a feature flag by name."""
    return feature_flag_service.get_flag(flag_name)


def set_feature_flag(
    flag_name: str, enabled: bool, value: Any = None, **kwargs
) -> bool:
    """Set a feature flag."""
    return feature_flag_service.set_flag(flag_name, enabled, value, **kwargs)
