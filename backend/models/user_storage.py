"""Models for user storage tracking"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


@dataclass
class UserStorageUsage:
    """Track storage usage per user"""

    user_id: str
    total_bytes: int = 0
    file_count: int = 0
    last_updated: Optional[datetime] = None
    quota_bytes: int = 50 * 1024 * 1024  # 50MB default per user

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()

    @property
    def usage_mb(self) -> float:
        """Get usage in megabytes"""
        return self.total_bytes / (1024 * 1024)

    @property
    def quota_mb(self) -> float:
        """Get quota in megabytes"""
        return self.quota_bytes / (1024 * 1024)

    @property
    def available_bytes(self) -> int:
        """Get available bytes"""
        return max(0, self.quota_bytes - self.total_bytes)

    @property
    def available_mb(self) -> float:
        """Get available megabytes"""
        return self.available_bytes / (1024 * 1024)

    @property
    def usage_percentage(self) -> float:
        """Get usage as percentage of quota"""
        if self.quota_bytes <= 0:
            return 0.0
        return min(100.0, (self.total_bytes / self.quota_bytes) * 100)

    def can_add_file(self, file_size_bytes: int) -> bool:
        """Check if user can add a file of this size"""
        return (self.total_bytes + file_size_bytes) <= self.quota_bytes

    def add_file(self, file_size_bytes: int):
        """Add a file to usage tracking"""
        self.total_bytes += file_size_bytes
        self.file_count += 1
        self.last_updated = datetime.utcnow()

    def remove_file(self, file_size_bytes: int):
        """Remove a file from usage tracking"""
        self.total_bytes = max(0, self.total_bytes - file_size_bytes)
        self.file_count = max(0, self.file_count - 1)
        self.last_updated = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "total_bytes": self.total_bytes,
            "file_count": self.file_count,
            "last_updated": self.last_updated.isoformat()
            if self.last_updated
            else None,
            "quota_bytes": self.quota_bytes,
            "usage_mb": self.usage_mb,
            "quota_mb": self.quota_mb,
            "available_bytes": self.available_bytes,
            "available_mb": self.available_mb,
            "usage_percentage": self.usage_percentage,
        }
