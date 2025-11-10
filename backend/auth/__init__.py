"""Authentication module for pocket_musec

Provides user authentication, JWT token management, and RBAC
"""

from .models import User, RefreshToken, TokenPair
from .password import hash_password, verify_password
from .jwt_manager import JWTManager, TokenType
from .exceptions import (
    AuthError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
    InsufficientPermissionsError,
)

__all__ = [
    "User",
    "RefreshToken",
    "TokenPair",
    "hash_password",
    "verify_password",
    "JWTManager",
    "TokenType",
    "AuthError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "TokenInvalidError",
    "InsufficientPermissionsError",
]
