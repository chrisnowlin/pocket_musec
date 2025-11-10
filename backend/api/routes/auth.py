"""Authentication API routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
import logging

from ...auth import (
    AuthService,
    User,
    InvalidCredentialsError,
    AccountInactiveError,
    TokenExpiredError,
    TokenInvalidError,
)
from ...auth.exceptions import UserExistsError, UserNotFoundError
from ...auth.models import UserRole
from ..models import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    TokenResponse,
    UserResponse,
    LoginResponse,
    MessageResponse,
)
from ..dependencies import get_auth_service, get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(require_admin)
):
    """
    Register a new user (admin only)

    Args:
        request: Registration request with email, password, full_name, role
        auth_service: AuthService instance
        current_user: Current admin user

    Returns:
        Created user information

    Raises:
        400: If user already exists or password invalid
        403: If not admin
    """
    try:
        user = auth_service.register_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            role=UserRole(request.role)
        )

        logger.info(f"Admin {current_user.id} created user {user.id} ({user.email})")

        return UserResponse(**user.to_dict())

    except UserExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        # Password complexity validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and return tokens

    Args:
        request: Login request with email and password
        auth_service: AuthService instance

    Returns:
        User information and JWT tokens

    Raises:
        401: If credentials invalid
        403: If account inactive
    """
    try:
        user, tokens = auth_service.login(request.email, request.password)

        logger.info(f"User logged in: {user.id} ({user.email})")

        return LoginResponse(
            user=UserResponse(**user.to_dict()),
            tokens=TokenResponse(**tokens.to_dict())
        )

    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except AccountInactiveError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token

    Args:
        request: Refresh token request
        auth_service: AuthService instance

    Returns:
        New token pair

    Raises:
        401: If refresh token invalid or expired
    """
    try:
        tokens = auth_service.refresh_access_token(request.refresh_token)

        logger.info("Access token refreshed")

        return TokenResponse(**tokens.to_dict())

    except (TokenExpiredError, TokenInvalidError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user)
):
    """
    Logout user by revoking refresh token

    Args:
        request: Refresh token to revoke
        auth_service: AuthService instance
        current_user: Current authenticated user

    Returns:
        Success message
    """
    auth_service.logout(request.refresh_token)

    logger.info(f"User logged out: {current_user.id}")

    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return UserResponse(**current_user.to_dict())


@router.put("/password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user)
):
    """
    Change user password

    Args:
        request: Password change request
        auth_service: AuthService instance
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        400: If password invalid
        401: If current password wrong
    """
    try:
        auth_service.change_password(
            user_id=current_user.id,
            current_password=request.current_password,
            new_password=request.new_password
        )

        logger.info(f"Password changed for user: {current_user.id}")

        return MessageResponse(message="Password changed successfully. Please log in again.")

    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValueError as e:
        # Password complexity validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(require_admin)
):
    """
    List all users (admin only)

    Args:
        auth_service: AuthService instance
        current_user: Current admin user

    Returns:
        List of all users
    """
    users = auth_service.user_repo.list_all_users()
    return [UserResponse(**user.to_dict()) for user in users]


@router.put("/users/{user_id}/activate", response_model=MessageResponse)
async def activate_user(
    user_id: str,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(require_admin)
):
    """
    Activate a user account (admin only)

    Args:
        user_id: User ID to activate
        auth_service: AuthService instance
        current_user: Current admin user

    Returns:
        Success message

    Raises:
        404: If user not found
    """
    try:
        auth_service.user_repo.activate_user(user_id)
        logger.info(f"Admin {current_user.id} activated user {user_id}")
        return MessageResponse(message=f"User {user_id} activated successfully")

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )


@router.put("/users/{user_id}/deactivate", response_model=MessageResponse)
async def deactivate_user(
    user_id: str,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(require_admin)
):
    """
    Deactivate a user account (admin only)

    Args:
        user_id: User ID to deactivate
        auth_service: AuthService instance
        current_user: Current admin user

    Returns:
        Success message

    Raises:
        404: If user not found
    """
    try:
        auth_service.user_repo.deactivate_user(user_id)
        auth_service.user_repo.revoke_all_user_tokens(user_id)
        logger.info(f"Admin {current_user.id} deactivated user {user_id}")
        return MessageResponse(message=f"User {user_id} deactivated successfully")

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
