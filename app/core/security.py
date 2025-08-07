"""
Security utilities for authentication and authorization.
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> bool:
    """
    Validate password strength.
    Requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character
    """
    if len(password) < 8:
        return False
    
    # Check for uppercase letter
    if not re.search(r"[A-Z]", password):
        return False
    
    # Check for lowercase letter
    if not re.search(r"[a-z]", password):
        return False
    
    # Check for digit
    if not re.search(r"\d", password):
        return False
    
    # Check for special character
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    
    return True


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # Refresh tokens last 7 days
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        # Check token type
        if payload.get("type") != "access":
            return None
            
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> Optional[dict]:
    """Decode and validate JWT refresh token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        # Check token type
        if payload.get("type") != "refresh":
            return None
            
        return payload
    except JWTError:
        return None


# Token blacklist storage (in production, use Redis or database)
_token_blacklist = set()


async def add_token_to_blacklist(token: str, expiry_time: datetime) -> None:
    """Add token to blacklist."""
    from app.utils.database import get_database
    
    db = await get_database()
    await db.token_blacklist.insert_one({
        "token": token,
        "blacklisted_at": datetime.utcnow(),
        "expires_at": expiry_time
    })


async def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted."""
    from app.utils.database import get_database
    
    db = get_database()
    result = await db.token_blacklist.find_one({"token": token})
    return result is not None


async def cleanup_expired_tokens() -> None:
    """Clean up expired tokens from blacklist."""
    from app.utils.database import get_database
    
    db = await get_database()
    await db.token_blacklist.delete_many({
        "expires_at": {"$lt": datetime.utcnow()}
    })
