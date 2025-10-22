"""
Authentication Service - Business logic for auth operations
"""

from datetime import datetime
from typing import Dict, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.dto.auth import RegisterDTO, LoginDTO, TokenResponseDTO
from app.core.security import (
    hash_password,
    verify_password,
    create_tokens_for_user,
    decode_token
)
from app.core.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    """Service for authentication operations"""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register_user(
        self,
        register_data: RegisterDTO,
        ip_address: Optional[str] = None
    ) -> Dict:
        """
        Register a new user with ToS/Non-Circumvention acceptance

        Args:
            register_data: Registration data DTO
            ip_address: Client IP address for legal compliance

        Returns:
            Dictionary with user info and JWT tokens

        Raises:
            HTTPException: If email/username already exists or validation fails
        """
        # Check if email already exists
        existing_user = self.user_repo.get_by_email(register_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if username already exists
        existing_username = self.db.query(User).filter(
            User.username == register_data.username
        ).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Validate ToS acceptance
        if not register_data.accepted_non_circumvention:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must accept the Terms of Service and Non-Circumvention agreement"
            )

        # Hash password
        hashed_password = hash_password(register_data.password)

        # Create user with ToS metadata
        # Debug: Print role value
        print(f"DEBUG: register_data.role = {register_data.role!r} (type: {type(register_data.role)})")

        user_data = {
            "email": register_data.email,
            "username": register_data.username,
            "hashed_password": hashed_password,
            "full_name": register_data.full_name,
            "phone_number": register_data.phone_number,
            "role": register_data.role,  # SQLEnum will handle string validation
            "tier": register_data.tier,
            "country": register_data.country,
            "city": register_data.city,
            "company_name": register_data.company_name,
            "tax_id": register_data.tax_id,
            # Legal compliance fields
            "accepted_non_circumvention": True,
            "non_circumvention_accepted_at": datetime.utcnow(),
            "tos_version_accepted": register_data.tos_version_accepted,
            "ip_registered": ip_address,
            "subscription_status": "none",  # SQLEnum will handle string validation
            "verified_status": False,  # Not verified by default
            "is_active": True
        }

        # Debug: Print user_data before User creation
        print(f"DEBUG: user_data role = {user_data['role']!r}, subscription_status = {user_data['subscription_status']!r}")

        user = User(**user_data)
        print(f"DEBUG: After User creation, user.role = {user.role!r} (type: {type(user.role)})")
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Generate JWT tokens
        tokens = create_tokens_for_user(
            user_id=user.id,
            email=user.email,
            role=user.role,
            tier=user.tier
        )

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "tier": user.tier,
                "verified_status": user.verified_status,
                "subscription_status": user.subscription_status,
                "created_at": user.created_at
            },
            "tokens": TokenResponseDTO(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type=tokens["token_type"],
                expires_in=settings.access_token_expire_minutes * 60  # Convert to seconds
            )
        }

    def login_user(self, login_data: LoginDTO) -> Dict:
        """
        Authenticate user and generate JWT tokens

        Args:
            login_data: Login credentials DTO

        Returns:
            Dictionary with user info and JWT tokens

        Raises:
            HTTPException: If credentials are invalid or user is inactive
        """
        # Get user by email
        user = self.user_repo.get_by_email(login_data.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Please contact support."
            )

        # Generate JWT tokens
        tokens = create_tokens_for_user(
            user_id=user.id,
            email=user.email,
            role=user.role,
            tier=user.tier
        )

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "tier": user.tier,
                "verified_status": user.verified_status,
                "subscription_status": user.subscription_status
            },
            "tokens": TokenResponseDTO(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type=tokens["token_type"],
                expires_in=settings.access_token_expire_minutes * 60
            )
        }

    def refresh_access_token(self, refresh_token: str) -> TokenResponseDTO:
        """
        Generate new access token from refresh token

        Args:
            refresh_token: JWT refresh token

        Returns:
            New TokenResponseDTO with fresh access token

        Raises:
            HTTPException: If refresh token is invalid or expired
        """
        # Decode and validate refresh token
        payload = decode_token(refresh_token)

        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify token type is refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database
        user_id = payload.get("user_id")
        user = self.user_repo.get_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generate new tokens
        tokens = create_tokens_for_user(
            user_id=user.id,
            email=user.email,
            role=user.role,
            tier=user.tier
        )

        return TokenResponseDTO(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=settings.access_token_expire_minutes * 60
        )

    def get_current_user_info(self, user: User) -> Dict:
        """
        Get current authenticated user information

        Args:
            user: Authenticated User object

        Returns:
            Dictionary with user information
        """
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "tier": user.tier,
            "subscription_status": user.subscription_status,
            "verified_status": user.verified_status,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "country": user.country,
            "city": user.city,
            "company_name": user.company_name,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
