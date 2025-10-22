"""
Authentication Controller - HTTP endpoints for authentication
"""

from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.dto.auth import (
    RegisterDTO,
    LoginDTO,
    TokenResponseDTO,
    RefreshTokenDTO,
    AuthUserResponseDTO,
    CurrentUserDTO
)
from app.utils.request import get_client_ip

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to get AuthService instance"""
    return AuthService(db)


@router.post("/register", response_model=AuthUserResponseDTO, status_code=status.HTTP_201_CREATED)
async def register(
    register_data: RegisterDTO,
    request: Request,
    service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user with ToS/Non-Circumvention acceptance

    **Requirements:**
    - Valid email address (must be unique)
    - Username (3-100 characters, must be unique)
    - Password (minimum 8 characters)
    - Role selection (developer, investor, agency, buyer)
    - **Must accept ToS & Non-Circumvention agreement**

    **Legal Compliance:**
    - Captures IP address and timestamp of registration
    - Stores ToS version accepted
    - Records Non-Circumvention agreement acceptance

    **Returns:**
    - User information
    - JWT access token (expires in 30 minutes)
    - JWT refresh token (expires in 7 days)

    **Notes:**
    - User starts with 'none' subscription status
    - Verification required for certain features (verified_status: false by default)
    - Default tier depends on role (e.g., developer: 'launch')
    """
    # Extract client IP address for legal compliance
    ip_address = get_client_ip(request)

    result = service.register_user(register_data, ip_address)

    return AuthUserResponseDTO(**result)


@router.post("/login", response_model=AuthUserResponseDTO)
async def login(
    login_data: LoginDTO,
    service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and receive JWT tokens

    **Credentials:**
    - Email address
    - Password

    **Returns:**
    - User information
    - JWT access token (expires in 30 minutes)
    - JWT refresh token (expires in 7 days)

    **Security:**
    - Password is verified using bcrypt
    - Account must be active (is_active: true)
    - Failed attempts do not reveal if email exists (generic error message)

    **Token Usage:**
    - Include access token in Authorization header: `Bearer <access_token>`
    - Use refresh token to obtain new access token when expired
    """
    result = service.login_user(login_data)

    return AuthUserResponseDTO(**result)


@router.post("/refresh", response_model=TokenResponseDTO)
async def refresh_token(
    refresh_data: RefreshTokenDTO,
    service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token

    **Usage:**
    - When access token expires (after 30 minutes), use refresh token to get new access token
    - Refresh token is valid for 7 days

    **Request:**
    - Provide refresh_token in request body

    **Returns:**
    - New access token
    - New refresh token (token rotation for security)
    - Token type and expiry information

    **Security:**
    - Refresh token can only be used once (token rotation)
    - User must still be active in database
    - Invalid/expired refresh tokens return 401 Unauthorized
    """
    tokens = service.refresh_access_token(refresh_data.refresh_token)

    return tokens


@router.get("/me", response_model=CurrentUserDTO)
async def get_current_user(
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service)
):
    """
    Get current authenticated user information

    **Authentication Required:**
    - Must include valid access token in Authorization header
    - Format: `Authorization: Bearer <access_token>`

    **Returns:**
    - Complete user profile information
    - Role and tier information
    - Subscription and verification status
    - Account metadata (created_at, updated_at)

    **Use Cases:**
    - Verify authentication status
    - Display user profile information
    - Check role/tier for client-side UI rendering
    - Validate subscription status before accessing features
    """
    user_info = service.get_current_user_info(current_user)

    return CurrentUserDTO(**user_info)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout current user (client-side token removal)

    **Note:**
    - JWT tokens are stateless (stored on client, not server)
    - Logout is handled client-side by removing tokens from storage
    - This endpoint confirms authentication before client clears tokens

    **Client Implementation:**
    1. Call this endpoint to verify token is still valid
    2. Remove access_token and refresh_token from client storage
    3. Redirect to login page

    **Returns:**
    - Success message confirming logout
    """
    return {
        "message": "Successfully logged out",
        "detail": "Please remove tokens from client storage"
    }
