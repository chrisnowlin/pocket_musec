"""Feature flags for gradual camelCase rollout"""

import os
from typing import Dict, Any


class FeatureFlags:
    """Manages feature flags for camelCase migration"""

    def __init__(self):
        self._flags = {
            # Enable camelCase responses in APIs
            "CAMELCASE_API_RESPONSES": os.getenv(
                "ENABLE_CAMELCASE_API", "false"
            ).lower()
            == "true",
            # Enable camelCase database field access
            "CAMELCASE_DB_FIELDS": os.getenv("ENABLE_CAMELCASE_DB", "false").lower()
            == "true",
            # Enable camelCase in internal processing
            "CAMELCASE_INTERNAL": os.getenv(
                "ENABLE_CAMELCASE_INTERNAL", "false"
            ).lower()
            == "true",
            # Enable backward compatibility mode
            "SNAKECASE_COMPATIBILITY": os.getenv(
                "ENABLE_SNAKECASE_COMPAT", "true"
            ).lower()
            == "true",
            # Force camelCase for new data (writes only)
            "CAMELCASE_WRITES_ONLY": os.getenv(
                "ENABLE_CAMELCASE_WRITES", "false"
            ).lower()
            == "true",
        }

    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        return self._flags.get(flag_name, False)

    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags"""
        return self._flags.copy()

    def set_flag(self, flag_name: str, value: bool) -> None:
        """Set a feature flag (for testing)"""
        self._flags[flag_name] = value


# Global instance
feature_flags = FeatureFlags()
