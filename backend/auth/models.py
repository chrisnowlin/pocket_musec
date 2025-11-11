"""Data models for authentication"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""

    TEACHER = "teacher"
    ADMIN = "admin"


class ProcessingMode(str, Enum):
    """Processing mode for LLM"""

    CLOUD = "cloud"
    LOCAL = "local"


@dataclass
class User:
    """User account model"""

    id: str
    email: str
    password_hash: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.TEACHER
    processing_mode: ProcessingMode = ProcessingMode.CLOUD
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_active: bool = True

    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == UserRole.ADMIN

    def is_teacher(self) -> bool:
        """Check if user has teacher role"""
        return self.role == UserRole.TEACHER

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary representation"""
        data = {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "processing_mode": self.processing_mode.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active,
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
        return data


@dataclass
class RefreshToken:
    """Refresh token model for JWT token rotation"""

    id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    revoked: bool = False
    created_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.utcnow() >= self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not revoked)"""
        return not self.is_expired() and not self.revoked


@dataclass
class TokenPair:
    """Access and refresh token pair"""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900  # 15 minutes in seconds

    def to_dict(self) -> dict:
        """Convert to dictionary for API response"""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
        }


@dataclass
class Session:
    """Lesson generation session"""

    id: str
    user_id: str
    grade_level: Optional[str] = None
    strand_code: Optional[str] = None
    selected_standards: Optional[str] = None
    selected_objectives: Optional[str] = None
    additional_context: Optional[str] = None
    agent_state: Optional[str] = None  # JSON serialized agent state
    conversation_history: Optional[str] = None  # JSON serialized conversation history
    current_state: Optional[str] = "welcome"  # Current conversation state
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Lesson:
    """Generated lesson plan"""

    id: str
    session_id: str
    user_id: str
    title: str
    content: str
    metadata: Optional[str] = None
    processing_mode: ProcessingMode = ProcessingMode.CLOUD
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Citation:
    """Source citation for lesson content"""

    id: str
    lesson_id: str
    source_type: str  # 'standard', 'objective', 'document', 'image'
    source_id: str
    source_title: str
    page_number: Optional[int] = None
    excerpt: Optional[str] = None
    citation_text: str = ""
    citation_number: int = 1
    created_at: Optional[datetime] = None


@dataclass
class Image:
    """Uploaded image with OCR and vision analysis"""

    id: str
    user_id: str
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    extracted_text: Optional[str] = None
    vision_summary: Optional[str] = None
    ocr_confidence: Optional[float] = None
    metadata: Optional[str] = None
    created_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
