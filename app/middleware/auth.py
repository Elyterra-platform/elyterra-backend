"""
Authentication middleware for JWT verification and role/tier-based access control
"""

from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from functools import wraps

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user_repository import UserRepository

# HTTP Bearer token security scheme
security = HTTPBearer()


class AuthMiddleware:
    """Authentication middleware for JWT token verification"""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def get_current_user_from_token(self, token_payload: dict) -> Optional[User]:
        """
        Get user from database using token payload

        Args:
            token_payload: Decoded JWT payload

        Returns:
            User object or None if not found
        """
        user_id = token_payload.get("user_id")
        if not user_id:
            return None

        return self.user_repo.get_by_id(user_id)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token

    Args:
        credentials: HTTP Bearer token from request header
        db: Database session

    Returns:
        Authenticated User object

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extract and decode token
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise credentials_exception

    # Verify token type is access token
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    middleware = AuthMiddleware(db)
    user = middleware.get_current_user_from_token(payload)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user (checks if user is not disabled)

    Args:
        current_user: Current authenticated user

    Returns:
        Active User object

    Raises:
        HTTPException: 400 if user account is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    return current_user


def require_role(*allowed_roles: str):
    """
    Decorator to require specific role(s) for endpoint access

    Usage:
        @require_role("developer", "admin")
        async def some_endpoint(current_user: User = Depends(get_current_active_user)):
            pass

    Args:
        *allowed_roles: Variable number of allowed role strings

    Returns:
        Dependency function that checks user role
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker


def require_tier(allowed_tiers: List[str]):
    """
    Decorator to require specific tier(s) for endpoint access

    Usage:
        @require_tier(["growth", "elite"])
        async def premium_endpoint(current_user: User = Depends(get_current_active_user)):
            pass

    Args:
        allowed_tiers: List of allowed tier strings

    Returns:
        Dependency function that checks user tier
    """
    async def tier_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.tier not in allowed_tiers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required tier: {', '.join(allowed_tiers)}"
            )
        return current_user

    return tier_checker


def require_subscription_active():
    """
    Decorator to require active subscription

    Usage:
        @require_subscription_active()
        async def premium_endpoint(current_user: User = Depends(get_current_active_user)):
            pass

    Returns:
        Dependency function that checks subscription status
    """
    async def subscription_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.subscription_status not in ["active", "trial"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Active subscription required. Please upgrade your account."
            )
        return current_user

    return subscription_checker


def require_verified():
    """
    Decorator to require verified user status

    Usage:
        @require_verified()
        async def verified_only_endpoint(current_user: User = Depends(get_current_active_user)):
            pass

    Returns:
        Dependency function that checks verified status
    """
    async def verified_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.verified_status:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Verified account required. Please complete verification."
            )
        return current_user

    return verified_checker


# Optional dependency - returns None if no token provided (for public endpoints with optional auth)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication - returns User if authenticated, None if not

    Useful for endpoints that work for both authenticated and anonymous users

    Args:
        credentials: Optional HTTP Bearer token
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = decode_token(token)

        if payload is None or payload.get("type") != "access":
            return None

        middleware = AuthMiddleware(db)
        user = middleware.get_current_user_from_token(payload)

        return user if user and user.is_active else None

    except Exception:
        return None
