"""Tests for security utilities."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    check_rate_limit
)
from app.core.config import settings


class TestPasswordHashing:
    """Test password hashing functions."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password("wrongpassword", hashed) is False
    
    def test_hash_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "testpassword123"
        hashed1 = hash_password(password)
        hashed2 = hash_password(password)
        
        # Hashes should be different due to salt
        assert hashed1 != hashed2
        # But both should verify correctly
        assert verify_password(password, hashed1) is True
        assert verify_password(password, hashed2) is True


class TestJWT:
    """Test JWT token functions."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        username = "testuser"
        token = create_access_token(username)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_access_token_valid(self):
        """Test decoding valid token."""
        username = "testuser"
        token = create_access_token(username)
        payload = decode_access_token(token)
        
        assert payload is not None
        assert payload.get("sub") == username
        assert "exp" in payload
        assert "iat" in payload
    
    def test_decode_access_token_invalid(self):
        """Test decoding invalid token."""
        invalid_token = "invalid.token.here"
        payload = decode_access_token(invalid_token)
        
        assert payload is None
    
    def test_decode_access_token_expired(self):
        """Test decoding expired token."""
        # Create token with very short expiration
        from app.core.security import jwt
        from datetime import datetime, timedelta, timezone
        
        now = datetime.now(timezone.utc)
        expire = now - timedelta(minutes=1)
        payload_data = {
            "sub": "testuser",
            "exp": expire,
            "iat": now
        }
        expired_token = jwt.encode(
            payload_data,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        result = decode_access_token(expired_token)
        assert result is None


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_check_rate_limit_first_request(self):
        """Test rate limit check on first request."""
        request = MagicMock()
        request.client.host = "127.0.0.1"
        
        # First request should be allowed
        result = check_rate_limit(request)
        assert result is True
    
    def test_check_rate_limit_within_limit(self):
        """Test rate limit check within allowed limit."""
        request = MagicMock()
        request.client.host = "127.0.0.3"
        
        # Make requests up to the limit (should all pass)
        for i in range(settings.RATE_LIMIT_ATTEMPTS):
            result = check_rate_limit(request)
            assert result is True, f"Request {i+1} should be allowed"
    
    def test_check_rate_limit_exceeded(self):
        """Test rate limit check when limit exceeded."""
        request = MagicMock()
        request.client.host = "127.0.0.2"
        
        # Make requests exceeding the limit
        for _ in range(settings.RATE_LIMIT_ATTEMPTS):
            check_rate_limit(request)
        
        # Next request should be blocked
        result = check_rate_limit(request)
        assert result is False