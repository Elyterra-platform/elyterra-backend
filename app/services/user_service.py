"""
User Service - Business logic layer
Handles business operations and orchestrates repositories
"""

from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.repositories.user_repository import UserRepository
from app.dto.user import UserCreateDTO, UserUpdateDTO, UserPasswordUpdateDTO
from app.models.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Service for User business logic"""

    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def create_user(self, user_data: UserCreateDTO) -> User:
        """
        Create a new user
        Validates uniqueness and hashes password
        """
        # Check if email already exists
        if self.repository.exists_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if username already exists
        if self.repository.exists_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Hash password
        hashed_password = self._hash_password(user_data.password)

        # Prepare user data
        user_dict = user_data.model_dump(exclude={'password'})
        user_dict['hashed_password'] = hashed_password

        # Create user
        return self.repository.create(user_dict)

    def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID or raise 404"""
        user = self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.repository.get_by_email(email)

    def get_all_users(self, skip: int = 0, limit: int = 100) -> tuple[List[User], int]:
        """
        Get all users with pagination
        Returns (users, total_count)
        """
        users = self.repository.get_all(skip=skip, limit=limit)
        total = self.repository.count()
        return users, total

    def update_user(self, user_id: int, update_data: UserUpdateDTO) -> User:
        """Update user information"""
        user = self.get_user_by_id(user_id)

        # Filter out None values
        update_dict = update_data.model_dump(exclude_unset=True)

        return self.repository.update(user, update_dict)

    def update_password(self, user_id: int, password_data: UserPasswordUpdateDTO) -> User:
        """Update user password"""
        user = self.get_user_by_id(user_id)

        # Verify current password
        if not self._verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )

        # Hash new password
        new_hashed_password = self._hash_password(password_data.new_password)

        return self.repository.update(user, {'hashed_password': new_hashed_password})

    def delete_user(self, user_id: int) -> None:
        """Delete user"""
        user = self.get_user_by_id(user_id)
        self.repository.delete(user)

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password
        Returns user if valid, None otherwise
        """
        user = self.repository.get_by_email(email)
        if not user:
            return None

        if not self._verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is inactive"
            )

        return user

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    @staticmethod
    def _verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
