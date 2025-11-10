"""JWT token management for authentication"""

import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional
from enum import Enum


class TokenType(str, Enum):
    """JWT token types"""
    ACCESS = "access"
    REFRESH = "refresh"


class JWTManager:
    """Manages JWT token generation and validation"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize JWT manager

        Args:
            secret_key: Secret key for signing tokens (min 256 bits)
            algorithm: JWT algorithm (default HS256)
        """
        if len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters (256 bits)")

        self.secret_key = secret_key
        self.algorithm = algorithm

        # Token expiration times
        self.access_token_expires = timedelta(minutes=15)
        self.refresh_token_expires = timedelta(days=7)

    def generate_access_token(
        self,
        user_id: str,
        email: str,
        role: str,
        additional_claims: Optional[Dict] = None
    ) -> str:
        """
        Generate JWT access token

        Args:
            user_id: User ID
            email: User email
            role: User role (teacher or admin)
            additional_claims: Optional additional JWT claims

        Returns:
            Encoded JWT access token
        """
        now = datetime.utcnow()
        expires_at = now + self.access_token_expires

        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "type": TokenType.ACCESS.value,
            "exp": expires_at,
            "iat": now,
        }

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def generate_refresh_token(
        self,
        user_id: str,
        additional_claims: Optional[Dict] = None
    ) -> str:
        """
        Generate JWT refresh token

        Args:
            user_id: User ID
            additional_claims: Optional additional JWT claims

        Returns:
            Encoded JWT refresh token
        """
        now = datetime.utcnow()
        expires_at = now + self.refresh_token_expires

        payload = {
            "sub": user_id,
            "type": TokenType.REFRESH.value,
            "exp": expires_at,
            "iat": now,
        }

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str, token_type: TokenType) -> Dict:
        """
        Verify and decode JWT token

        Args:
            token: JWT token to verify
            token_type: Expected token type (access or refresh)

        Returns:
            Decoded token payload

        Raises:
            TokenExpiredError: If token has expired
            TokenInvalidError: If token is invalid or wrong type
        """
        from .exceptions import TokenExpiredError, TokenInvalidError

        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Verify token type
            if payload.get("type") != token_type.value:
                raise TokenInvalidError(f"Invalid token type, expected {token_type.value}")

            return payload

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(f"Invalid token: {str(e)}")

    def decode_token_unsafe(self, token: str) -> Optional[Dict]:
        """
        Decode token without verification (for debugging only)

        Args:
            token: JWT token to decode

        Returns:
            Decoded payload or None if decoding fails
        """
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False}
            )
        except Exception:
            return None

    def hash_token(self, token: str) -> str:
        """
        Generate SHA-256 hash of token for storage

        Used for refresh token storage to prevent token leakage

        Args:
            token: Token to hash

        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def get_expiration_time(self, token_type: TokenType) -> datetime:
        """
        Get expiration time for token type

        Args:
            token_type: Type of token

        Returns:
            Expiration datetime
        """
        now = datetime.utcnow()
        if token_type == TokenType.ACCESS:
            return now + self.access_token_expires
        else:
            return now + self.refresh_token_expires
