"""Authentication module for pocket_musec

Provides user authentication, JWT token management, and RBAC
"""

from .models import User, RefreshToken, TokenPair
from .password import hash_password, verify_password
from .jwt_manager import JWTManager, TokenType
from .auth_service import AuthService
from .user_repository import UserRepository
from .exceptions import (
    AuthError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
    InsufficientPermissionsError,
    UserNotFoundError,
    UserExistsError,
    AccountLockedError,
    AccountInactiveError,
)

__all__ = [
    "User",
    "RefreshToken",
    "TokenPair",
    "hash_password",
    "verify_password",
    "JWTManager",
    "TokenType",
    "AuthService",
    "UserRepository",
    "AuthError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "TokenInvalidError",
    "InsufficientPermissionsError",
    "UserNotFoundError",
    "UserExistsError",
    "AccountLockedError",
    "AccountInactiveError",
]
