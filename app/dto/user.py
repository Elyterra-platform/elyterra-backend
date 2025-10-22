"""
User DTOs (Data Transfer Objects / Schemas)
Separate DTOs for different operations: create, update, response
"""

from typing import Optional
from pydantic import EmailStr, Field, field_validator
from app.dto.base import BaseDTO, BaseResponseDTO


class UserCreateDTO(BaseDTO):
    """DTO for creating a new user"""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens and underscores')
        return v.lower()


class UserUpdateDTO(BaseDTO):
    """DTO for updating user information"""

    full_name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class UserPasswordUpdateDTO(BaseDTO):
    """DTO for updating user password"""

    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8, max_length=100)


class UserResponseDTO(BaseResponseDTO):
    """DTO for user response (excludes sensitive data)"""

    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    phone_number: Optional[str] = None


class UserLoginDTO(BaseDTO):
    """DTO for user login"""

    email: EmailStr
    password: str


class TokenResponseDTO(BaseDTO):
    """DTO for authentication token response"""

    access_token: str
    token_type: str = "bearer"
    user: UserResponseDTO
