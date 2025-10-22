"""
Authentication Data Transfer Objects (DTOs)
Pydantic schemas for auth requests and responses
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class RegisterDTO(BaseModel):
    """User registration request"""
    email: EmailStr = Field(..., description="Valid email address")
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")

    # Role and tier
    role: str = Field(..., description="User role: developer, investor, agency, buyer")
    tier: Optional[str] = Field(None, description="User tier (depends on role)")

    # Legal compliance - REQUIRED
    accepted_non_circumvention: bool = Field(..., description="Must accept Non-Circumvention agreement")
    tos_version_accepted: str = Field(..., description="Version of ToS accepted (e.g., '1.0')")

    # Optional profile fields
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)

    @validator('role')
    def validate_role(cls, v):
        """Validate role is one of the allowed values"""
        allowed_roles = ['developer', 'investor', 'agency', 'buyer', 'admin']
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v

    @validator('accepted_non_circumvention')
    def validate_tos_acceptance(cls, v):
        """Ensure ToS and Non-Circumvention are accepted"""
        if not v:
            raise ValueError('You must accept the Terms of Service and Non-Circumvention agreement to register')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "developer@example.com",
                "username": "johndoe",
                "password": "SecurePass123!",
                "full_name": "John Doe",
                "role": "developer",
                "tier": "launch",
                "accepted_non_circumvention": True,
                "tos_version_accepted": "1.0",
                "country": "Portugal",
                "city": "Lisbon"
            }
        }


class LoginDTO(BaseModel):
    """User login request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "developer@example.com",
                "password": "SecurePass123!"
            }
        }


class TokenResponseDTO(BaseModel):
    """JWT token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class RefreshTokenDTO(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(..., description="JWT refresh token")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class AuthUserResponseDTO(BaseModel):
    """Authenticated user response with tokens"""
    user: dict = Field(..., description="User information")
    tokens: TokenResponseDTO = Field(..., description="JWT tokens")

    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": 1,
                    "email": "developer@example.com",
                    "username": "johndoe",
                    "role": "developer",
                    "tier": "launch",
                    "verified_status": False
                },
                "tokens": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 1800
                }
            }
        }


class CurrentUserDTO(BaseModel):
    """Current authenticated user information"""
    id: int
    email: str
    username: str
    role: str
    tier: Optional[str]
    subscription_status: str
    verified_status: bool
    full_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "developer@example.com",
                "username": "johndoe",
                "role": "developer",
                "tier": "launch",
                "subscription_status": "none",
                "verified_status": False,
                "full_name": "John Doe",
                "created_at": "2024-10-22T12:00:00"
            }
        }
