"""
Security utilities for password hashing and JWT token management
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing context
# Use bcrypt with proper configuration for Python 3.13
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b"
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Dictionary of data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({
        "exp": expire,
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return encoded_jwt


def create_refresh_token(data: Dict) -> str:
    """
    Create a JWT refresh token with longer expiration

    Args:
        data: Dictionary of data to encode in the token

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return encoded_jwt


def decode_token(token: str) -> Optional[Dict]:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None


def create_tokens_for_user(user_id: int, email: str, role: str, tier: Optional[str] = None) -> Dict[str, str]:
    """
    Create both access and refresh tokens for a user

    Args:
        user_id: User's database ID
        email: User's email address
        role: User's role (developer, investor, agency, buyer, admin)
        tier: User's tier (optional, depends on role)

    Returns:
        Dictionary with access_token and refresh_token
    """
    token_data = {
        "sub": email,
        "user_id": user_id,
        "role": role,
        "tier": tier
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": email, "user_id": user_id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
