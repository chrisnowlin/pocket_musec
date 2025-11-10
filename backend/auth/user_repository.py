"""User repository for database operations"""

import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from .models import User, RefreshToken, UserRole, ProcessingMode
from .exceptions import UserNotFoundError, UserExistsError


class UserRepository:
    """Handles database operations for users"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_user(
        self,
        email: str,
        password_hash: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.TEACHER
    ) -> User:
        """
        Create a new user

        Args:
            email: User email (must be unique)
            password_hash: Bcrypt hashed password
            full_name: User's full name
            role: User role (default: teacher)

        Returns:
            Created User object

        Raises:
            UserExistsError: If email already exists
        """
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()

        conn = self.get_connection()
        try:
            conn.execute("""
                INSERT INTO users (id, email, password_hash, full_name, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, email, password_hash, full_name, role.value, now))
            conn.commit()

            return self.get_user_by_id(user_id)

        except sqlite3.IntegrityError:
            raise UserExistsError(f"User with email {email} already exists")
        finally:
            conn.close()

    def get_user_by_id(self, user_id: str) -> User:
        """
        Get user by ID

        Args:
            user_id: User ID

        Returns:
            User object

        Raises:
            UserNotFoundError: If user not found
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()

            if not row:
                raise UserNotFoundError(f"User {user_id} not found")

            return self._row_to_user(row)
        finally:
            conn.close()

    def get_user_by_email(self, email: str) -> User:
        """
        Get user by email

        Args:
            email: User email

        Returns:
            User object

        Raises:
            UserNotFoundError: If user not found
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            )
            row = cursor.fetchone()

            if not row:
                raise UserNotFoundError(f"User with email {email} not found")

            return self._row_to_user(row)
        finally:
            conn.close()

    def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp"""
        now = datetime.utcnow()
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (now, user_id)
            )
            conn.commit()
        finally:
            conn.close()

    def update_processing_mode(self, user_id: str, mode: ProcessingMode) -> None:
        """Update user's processing mode preference"""
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE users SET processing_mode = ? WHERE id = ?",
                (mode.value, user_id)
            )
            conn.commit()
        finally:
            conn.close()

    def update_password(self, user_id: str, new_password_hash: str) -> None:
        """Update user's password"""
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_password_hash, user_id)
            )
            conn.commit()
        finally:
            conn.close()

    def deactivate_user(self, user_id: str) -> None:
        """Deactivate a user account"""
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE users SET is_active = 0 WHERE id = ?",
                (user_id,)
            )
            conn.commit()
        finally:
            conn.close()

    def activate_user(self, user_id: str) -> None:
        """Activate a user account"""
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE users SET is_active = 1 WHERE id = ?",
                (user_id,)
            )
            conn.commit()
        finally:
            conn.close()

    def list_all_users(self) -> List[User]:
        """Get all users (admin only)"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT * FROM users ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_user(row) for row in rows]
        finally:
            conn.close()

    def save_refresh_token(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime
    ) -> str:
        """
        Save refresh token to database

        Args:
            user_id: User ID
            token_hash: SHA-256 hash of the refresh token
            expires_at: Token expiration time

        Returns:
            Token ID
        """
        token_id = str(uuid.uuid4())
        now = datetime.utcnow()

        conn = self.get_connection()
        try:
            conn.execute("""
                INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (token_id, user_id, token_hash, expires_at, now))
            conn.commit()
            return token_id
        finally:
            conn.close()

    def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by hash"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM refresh_tokens WHERE token_hash = ?",
                (token_hash,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return RefreshToken(
                id=row["id"],
                user_id=row["user_id"],
                token_hash=row["token_hash"],
                expires_at=datetime.fromisoformat(row["expires_at"]),
                revoked=bool(row["revoked"]),
                created_at=datetime.fromisoformat(row["created_at"])
            )
        finally:
            conn.close()

    def revoke_refresh_token(self, token_hash: str) -> None:
        """Revoke a refresh token"""
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE refresh_tokens SET revoked = 1 WHERE token_hash = ?",
                (token_hash,)
            )
            conn.commit()
        finally:
            conn.close()

    def revoke_all_user_tokens(self, user_id: str) -> None:
        """Revoke all refresh tokens for a user"""
        conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
        finally:
            conn.close()

    def cleanup_expired_tokens(self) -> int:
        """Delete expired refresh tokens"""
        now = datetime.utcnow()
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM refresh_tokens WHERE expires_at < ?",
                (now,)
            )
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        finally:
            conn.close()

    def _row_to_user(self, row: sqlite3.Row) -> User:
        """Convert database row to User object"""
        return User(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            full_name=row["full_name"],
            role=UserRole(row["role"]),
            processing_mode=ProcessingMode(row["processing_mode"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            last_login=datetime.fromisoformat(row["last_login"]) if row["last_login"] else None,
            is_active=bool(row["is_active"])
        )
