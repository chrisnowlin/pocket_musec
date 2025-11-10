"""Authentication service orchestrating all auth operations"""

from datetime import datetime
from typing import Tuple
import logging

from .models import User, TokenPair, UserRole
from .user_repository import UserRepository
from .jwt_manager import JWTManager, TokenType
from .password import hash_password, verify_password
from .exceptions import (
    InvalidCredentialsError,
    AccountInactiveError,
    TokenExpiredError,
    TokenInvalidError,
)

logger = logging.getLogger(__name__)


class AuthService:
    """
    High-level authentication service

    Coordinates user authentication, token management, and session handling
    """

    def __init__(self, db_path: str, jwt_secret: str):
        self.user_repo = UserRepository(db_path)
        self.jwt_manager = JWTManager(jwt_secret)

    def register_user(
        self,
        email: str,
        password: str,
        full_name: str = None,
        role: UserRole = UserRole.TEACHER
    ) -> User:
        """
        Register a new user

        Args:
            email: User email
            password: Plain text password
            full_name: User's full name
            role: User role (default: teacher)

        Returns:
            Created User object

        Raises:
            ValueError: If password doesn't meet complexity requirements
            UserExistsError: If email already exists
        """
        logger.info(f"Registering new user: {email} with role {role.value}")

        # Hash password (this validates complexity)
        password_hash = hash_password(password)

        # Create user in database
        user = self.user_repo.create_user(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role
        )

        logger.info(f"User registered successfully: {user.id}")
        return user

    def login(self, email: str, password: str) -> Tuple[User, TokenPair]:
        """
        Authenticate user and generate tokens

        Args:
            email: User email
            password: Plain text password

        Returns:
            Tuple of (User, TokenPair)

        Raises:
            InvalidCredentialsError: If credentials are invalid
            AccountInactiveError: If account is deactivated
        """
        logger.info(f"Login attempt for: {email}")

        try:
            # Get user by email
            user = self.user_repo.get_user_by_email(email)
        except Exception:
            # Don't reveal if email exists
            raise InvalidCredentialsError("Invalid email or password")

        # Check if account is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive account: {email}")
            raise AccountInactiveError("Account is deactivated")

        # Verify password
        if not verify_password(password, user.password_hash):
            logger.warning(f"Failed login attempt for: {email}")
            raise InvalidCredentialsError("Invalid email or password")

        # Update last login
        self.user_repo.update_last_login(user.id)

        # Generate tokens
        tokens = self._generate_token_pair(user)

        logger.info(f"User logged in successfully: {user.id}")
        return user, tokens

    def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """
        Generate new access token using refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            New TokenPair with rotated refresh token

        Raises:
            TokenExpiredError: If refresh token expired
            TokenInvalidError: If refresh token invalid or revoked
        """
        # Verify refresh token
        payload = self.jwt_manager.verify_token(refresh_token, TokenType.REFRESH)
        user_id = payload["sub"]

        # Check if token is revoked
        token_hash = self.jwt_manager.hash_token(refresh_token)
        stored_token = self.user_repo.get_refresh_token(token_hash)

        if not stored_token or stored_token.revoked:
            raise TokenInvalidError("Refresh token has been revoked")

        if stored_token.is_expired():
            raise TokenExpiredError("Refresh token has expired")

        # Get user
        user = self.user_repo.get_user_by_id(user_id)

        # Revoke old refresh token (rotation)
        self.user_repo.revoke_refresh_token(token_hash)

        # Generate new token pair
        tokens = self._generate_token_pair(user)

        logger.info(f"Access token refreshed for user: {user_id}")
        return tokens

    def logout(self, refresh_token: str) -> None:
        """
        Logout user by revoking refresh token

        Args:
            refresh_token: Refresh token to revoke
        """
        token_hash = self.jwt_manager.hash_token(refresh_token)
        self.user_repo.revoke_refresh_token(token_hash)
        logger.info("User logged out, refresh token revoked")

    def verify_access_token(self, access_token: str) -> User:
        """
        Verify access token and return user

        Args:
            access_token: JWT access token

        Returns:
            User object

        Raises:
            TokenExpiredError: If token expired
            TokenInvalidError: If token invalid
        """
        payload = self.jwt_manager.verify_token(access_token, TokenType.ACCESS)
        user_id = payload["sub"]
        return self.user_repo.get_user_by_id(user_id)

    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> None:
        """
        Change user password

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password

        Raises:
            InvalidCredentialsError: If current password is wrong
            ValueError: If new password doesn't meet requirements
        """
        # Get user and verify current password
        user = self.user_repo.get_user_by_id(user_id)

        if not verify_password(current_password, user.password_hash):
            raise InvalidCredentialsError("Current password is incorrect")

        # Hash new password (validates complexity)
        new_password_hash = hash_password(new_password)

        # Update password
        self.user_repo.update_password(user_id, new_password_hash)

        # Revoke all existing tokens for security
        self.user_repo.revoke_all_user_tokens(user_id)

        logger.info(f"Password changed for user: {user_id}")

    def _generate_token_pair(self, user: User) -> TokenPair:
        """
        Generate access and refresh token pair

        Args:
            user: User object

        Returns:
            TokenPair with both tokens
        """
        # Generate access token
        access_token = self.jwt_manager.generate_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value
        )

        # Generate refresh token
        refresh_token = self.jwt_manager.generate_refresh_token(user_id=user.id)

        # Store refresh token hash
        token_hash = self.jwt_manager.hash_token(refresh_token)
        expires_at = self.jwt_manager.get_expiration_time(TokenType.REFRESH)
        self.user_repo.save_refresh_token(user.id, token_hash, expires_at)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=900  # 15 minutes
        )

    def cleanup_expired_tokens(self) -> int:
        """Clean up expired refresh tokens"""
        deleted = self.user_repo.cleanup_expired_tokens()
        logger.info(f"Cleaned up {deleted} expired refresh tokens")
        return deleted
