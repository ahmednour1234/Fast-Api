"""Security utilities for password hashing, JWT tokens, and rate limiting."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from collections import defaultdict

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from starlette.requests import Request

from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# In-memory rate limiting storage: {ip: {count: int, reset_at: datetime}}
_rate_limit_store: Dict[str, Dict] = defaultdict(lambda: {"count": 0, "reset_at": datetime.now(timezone.utc)})


def hash_password(password: str) -> str:
    """Hash a password using argon2."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    """Create a JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def check_rate_limit(request: Optional[Request] = None) -> bool:
    """Check if request exceeds rate limit. Returns True if allowed, False if exceeded."""
    if not request:
        return True  # Skip rate limiting if request not available
    client_ip = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc)
    
    # Cleanup expired entries
    expired_ips = [
        ip for ip, data in _rate_limit_store.items()
        if data["reset_at"] < now
    ]
    for ip in expired_ips:
        del _rate_limit_store[ip]
    
    # Check current IP
    if client_ip in _rate_limit_store:
        data = _rate_limit_store[client_ip]
        if data["reset_at"] > now:
            if data["count"] >= settings.RATE_LIMIT_ATTEMPTS:
                return False
            data["count"] += 1
        else:
            # Reset window
            data["count"] = 1
            data["reset_at"] = now + timedelta(minutes=settings.RATE_LIMIT_WINDOW_MINUTES)
    else:
        # First request from this IP
        _rate_limit_store[client_ip] = {
            "count": 1,
            "reset_at": now + timedelta(minutes=settings.RATE_LIMIT_WINDOW_MINUTES)
        }
    
    return True


def get_rate_limit_exception():
    """Get rate limit exceeded exception."""
    from app.core.exceptions import AppException
    return AppException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Too many login attempts. Please try again after {settings.RATE_LIMIT_WINDOW_MINUTES} minutes.",
        error_code="RATE_LIMIT_EXCEEDED"
    )
