"""
User Controller - HTTP request handlers
Handles HTTP requests and responses for User endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.user_service import UserService
from app.middleware.auth import get_current_active_user, require_role
from app.models.user import User
from app.dto.user import (
    UserCreateDTO,
    UserUpdateDTO,
    UserResponseDTO,
    UserPasswordUpdateDTO
)
from app.dto.base import PaginationParams, PaginatedResponse

# Create router
router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency to get UserService instance"""
    return UserService(db)


@router.post("/", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateDTO,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_role("admin"))
):
    """
    Create a new user (Admin only)

    **Note**: Regular users should use /api/auth/register instead

    - **email**: Valid email address (unique)
    - **username**: Username (3-100 chars, unique)
    - **password**: Password (min 8 chars)
    - **full_name**: Optional full name
    - **phone_number**: Optional phone number
    """
    user = service.create_user(user_data)
    return UserResponseDTO.model_validate(user)


@router.get("/{user_id}", response_model=UserResponseDTO)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user by ID

    - Users can view their own profile
    - Admins can view any user profile

    Returns user details without sensitive information (password excluded)
    """
    # Check authorization: user can see themselves, or must be admin
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )

    user = service.get_user_by_id(user_id)
    return UserResponseDTO.model_validate(user)


@router.get("/", response_model=PaginatedResponse)
async def get_all_users(
    pagination: PaginationParams = Depends(),
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_role("admin"))
):
    """
    Get all users with pagination (Admin only)

    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 10)

    Returns paginated list of all users in the system
    """
    users, total = service.get_all_users(skip=pagination.skip, limit=pagination.limit)

    return PaginatedResponse(
        total=total,
        page=pagination.page,
        limit=pagination.limit,
        pages=(total + pagination.limit - 1) // pagination.limit,
        data=[UserResponseDTO.model_validate(user) for user in users]
    )


@router.put("/{user_id}", response_model=UserResponseDTO)
async def update_user(
    user_id: int,
    update_data: UserUpdateDTO,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update user information

    - Users can update their own profile
    - Admins can update any user profile

    Only provided fields will be updated (partial update supported)
    """
    # Check authorization: user can update themselves, or must be admin
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )

    user = service.update_user(user_id, update_data)
    return UserResponseDTO.model_validate(user)


@router.put("/{user_id}/password", response_model=UserResponseDTO)
async def update_password(
    user_id: int,
    password_data: UserPasswordUpdateDTO,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update user password

    - Users can update their own password (requires current password)
    - Admins can update any user password

    **Security**: Current password verification required for non-admin users
    """
    # Check authorization: user can update themselves, or must be admin
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's password"
        )

    user = service.update_password(user_id, password_data)
    return UserResponseDTO.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_role("admin"))
):
    """
    Delete user (Admin only)

    **Warning**: Permanently removes user from database
    This action cannot be undone!
    """
    service.delete_user(user_id)
    return None
