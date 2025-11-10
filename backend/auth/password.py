"""Password hashing and verification using bcrypt"""

import bcrypt
import re


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with cost factor 12

    Args:
        password: Plain text password

    Returns:
        Hashed password as string

    Raises:
        ValueError: If password doesn't meet complexity requirements
    """
    validate_password_complexity(password)

    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash

    Args:
        password: Plain text password to verify
        password_hash: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception:
        # Handle any bcrypt errors (malformed hash, etc.)
        return False


def validate_password_complexity(password: str) -> None:
    """
    Validate password meets complexity requirements

    Requirements:
    - At least 8 characters long
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number

    Args:
        password: Password to validate

    Raises:
        ValueError: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")

    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(r'\d', password):
        raise ValueError("Password must contain at least one number")
