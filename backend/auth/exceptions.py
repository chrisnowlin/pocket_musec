"""Authentication exceptions"""


class AuthError(Exception):
    """Base authentication error"""
    pass


class InvalidCredentialsError(AuthError):
    """Raised when login credentials are invalid"""
    pass


class TokenExpiredError(AuthError):
    """Raised when JWT token has expired"""
    pass


class TokenInvalidError(AuthError):
    """Raised when JWT token is invalid"""
    pass


class InsufficientPermissionsError(AuthError):
    """Raised when user lacks required permissions"""
    pass


class UserNotFoundError(AuthError):
    """Raised when user is not found"""
    pass


class UserExistsError(AuthError):
    """Raised when attempting to create duplicate user"""
    pass


class AccountLockedError(AuthError):
    """Raised when account is locked due to failed attempts"""
    pass


class AccountInactiveError(AuthError):
    """Raised when account is deactivated"""
    pass
