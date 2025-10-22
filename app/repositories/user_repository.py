"""
User Repository - Data access layer
Handles all database operations for User model
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User


class UserRepository:
    """Repository for User model database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, user_data: dict) -> User:
        """Create a new user"""
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        return self.db.query(User).offset(skip).limit(limit).all()

    def count(self) -> int:
        """Get total count of users"""
        return self.db.query(func.count(User.id)).scalar()

    def update(self, user: User, update_data: dict) -> User:
        """Update user"""
        for key, value in update_data.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        """Delete user"""
        self.db.delete(user)
        self.db.commit()

    def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        return self.db.query(User).filter(User.email == email).first() is not None

    def exists_by_username(self, username: str) -> bool:
        """Check if user exists by username"""
        return self.db.query(User).filter(User.username == username).first() is not None
