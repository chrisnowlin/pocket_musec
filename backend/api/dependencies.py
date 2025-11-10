"""FastAPI dependencies for authentication and authorization"""

from fastapi import Depends, HTTPException, status, Header
from typing import Optional
import os

from ..auth import AuthService, User, TokenExpiredError, TokenInvalidError, InsufficientPermissionsError
from ..auth.models import UserRole


# Global auth service instance
def get_auth_service() -> AuthService:
    """Get AuthService instance"""
    db_path = os.getenv("DATABASE_PATH", "data/standards/standards.db")
    jwt_secret = os.getenv("JWT_SECRET_KEY")

    if not jwt_secret:
        raise RuntimeError("JWT_SECRET_KEY environment variable not set")

    return AuthService(db_path=db_path, jwt_secret=jwt_secret)


async def get_current_user(
    authorization: Optional[str] = Header(None),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Get current authenticated user from JWT token

    Args:
        authorization: Authorization header with Bearer token
        auth_service: AuthService instance

    Returns:
        Current User object

    Raises:
        HTTPException: 401 if token invalid/expired or missing
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    try:
        user = auth_service.verify_access_token(token)

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )

        return user

    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user

    Alias for get_current_user with explicit active check
    """
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require admin role

    Args:
        current_user: Current authenticated user

    Returns:
        User if admin

    Raises:
        HTTPException: 403 if not admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def require_teacher_or_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require teacher or admin role

    Args:
        current_user: Current authenticated user

    Returns:
        User if teacher or admin
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher or admin privileges required"
        )
    return current_user
