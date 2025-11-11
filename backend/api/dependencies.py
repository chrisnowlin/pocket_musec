"""Simplified dependencies with default user context"""

from fastapi import Depends

from ..auth.models import User, UserRole, ProcessingMode


# Default demo user for single-user mode
# This bypasses authentication and provides a consistent user context for all requests
DEFAULT_USER = User(
    id="demo-user",
    email="demo@pocketmusec.local",
    password_hash="",
    full_name="Demo User",
    role=UserRole.ADMIN,
    processing_mode=ProcessingMode.CLOUD,
    is_active=True,
)


async def get_current_user() -> User:
    """
    Return the default demo user (authentication disabled).
    
    In this demo mode, all API requests use the same demo user context.
    This simplifies the system by removing authentication complexity while
    maintaining the expected user-based data flow in the repositories.
    """
    return DEFAULT_USER


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Alias for get_current_user."""
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """All callers share the demo admin account."""
    return current_user


async def require_teacher_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """All callers share the demo user with teacher/admin privileges."""
    return current_user
