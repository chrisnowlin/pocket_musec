"""Pydantic models for API requests and responses"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Auth Request Models
class RegisterRequest(BaseModel):
    """User registration request"""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role: str = Field(default="teacher", pattern="^(teacher|admin)$")


class LoginRequest(BaseModel):
    """User login request"""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Token refresh request"""

    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Password change request"""

    current_password: str
    new_password: str = Field(..., min_length=8)


# Auth Response Models
class TokenResponse(BaseModel):
    """Authentication token response"""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """User information response"""

    id: str
    email: str
    full_name: Optional[str]
    role: str
    processing_mode: str
    created_at: Optional[datetime]
    last_login: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response with user and tokens"""

    user: UserResponse
    tokens: TokenResponse


class MessageResponse(BaseModel):
    """Generic message response"""

    message: str


class ErrorResponse(BaseModel):
    """Error response"""

    detail: str
    error_code: Optional[str] = None


class StandardResponse(BaseModel):
    """Standard metadata for UI"""

    id: str
    code: str
    grade: str
    strand_code: str
    strand_name: str
    title: str
    description: str
    objectives: int
    learning_objectives: List[str]
    last_used: Optional[str] = None


class SessionCreateRequest(BaseModel):
    """Request to start a new session"""

    grade_level: Optional[str] = None
    strand_code: Optional[str] = None
    standard_id: Optional[str] = None  # Primary standard (for backward compatibility)
    standard_ids: Optional[List[str]] = (
        None  # Multiple standards (new unified approach)
    )
    additional_context: Optional[str] = None
    lesson_duration: Optional[str] = None
    class_size: Optional[int] = None
    selected_objectives: Optional[List[str]] = None  # Multiple objectives
    selected_model: Optional[str] = None  # Selected AI model for cloud mode


class SessionUpdateRequest(BaseModel):
    """Update session context"""

    grade_level: Optional[str] = None
    strand_code: Optional[str] = None
    standard_id: Optional[str] = None  # Primary standard (for backward compatibility)
    standard_ids: Optional[List[str]] = (
        None  # Multiple standards (new unified approach)
    )
    additional_context: Optional[str] = None
    lesson_duration: Optional[str] = None
    class_size: Optional[int] = None
    selected_objectives: Optional[List[str]] = None  # Multiple objectives
    selected_model: Optional[str] = None  # Selected AI model for cloud mode


class SessionResponse(BaseModel):
    """Session summary returned to the client"""

    id: str
    grade_level: Optional[str]
    strand_code: Optional[str]
    selected_standards: Optional[List[StandardResponse]] = None  # Multiple standards
    selected_objectives: Optional[List[str]] = None  # Multiple objectives
    selected_model: Optional[str] = None  # Selected AI model for cloud mode
    additional_context: Optional[str]
    conversation_history: Optional[str] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class LessonSummary(BaseModel):
    """Lesson summary returned with chat response"""

    id: str
    title: str
    summary: str
    content: str
    metadata: Dict[str, Any]
    citations: List[str] = Field(default_factory=list)
    presentation_status: Optional[Dict[str, Any]] = None


class ChatMessageRequest(BaseModel):
    """Chat message sent from the workspace"""

    message: str
    lesson_duration: Optional[str] = None
    class_size: Optional[str] = None


class ModelSelectionRequest(BaseModel):
    """Request to update the selected model for a session"""

    selected_model: Optional[str] = None


class ModelAvailabilityResponse(BaseModel):
    """Response with available models and their status"""

    available_models: List[Dict[str, Any]]
    current_model: Optional[str] = None
    processing_mode: str


class ChatResponse(BaseModel):
    """Response payload containing AI reply and lesson"""

    response: str
    lesson: LessonSummary
    session: SessionResponse


# Draft Models
class DraftCreateRequest(BaseModel):
    """Request to create a new draft"""

    session_id: str
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class DraftUpdateRequest(BaseModel):
    """Request to update an existing draft"""

    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DraftResponse(BaseModel):
    """Draft response for the frontend"""

    id: str
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    grade: Optional[str] = None
    strand: Optional[str] = None
    standard: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
