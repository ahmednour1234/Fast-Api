"""Tests for AuthService."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile

from app.services.auth_service import AuthService
from app.core.exceptions import ConflictError, UnauthorizedError, ForbiddenError
from app.models.user import User
from app.core.security import hash_password


class TestAuthServiceRegister:
    """Test user registration."""
    
    @pytest.mark.asyncio
    async def test_register_success(self, mock_db_session, sample_user_data):
        """Test successful user registration."""
        service = AuthService(mock_db_session)
        
        # Mock repository methods
        service.user_repo.get_by_username = AsyncMock(return_value=None)
        service.user_repo.get_by_email = AsyncMock(return_value=None)
        service.user_repo.get_by_phone = AsyncMock(return_value=None)
        
        # Mock user creation
        mock_user = User(
            id=1,
            username=sample_user_data["username"],
            name=sample_user_data["name"],
            email=sample_user_data["email"],
            hashed_password=hash_password(sample_user_data["password"]),
            is_active=True
        )
        service.user_repo.create_user = AsyncMock(return_value=mock_user)
        
        # Mock avatar upload
        with patch("app.services.auth_service.save_image", new_callable=AsyncMock) as mock_save:
            mock_save.return_value = "avatar.jpg"
            
            user = await service.register(
                username=sample_user_data["username"],
                name=sample_user_data["name"],
                email=sample_user_data["email"],
                password=sample_user_data["password"],
                phone=sample_user_data["phone"]
            )
            
            assert user is not None
            assert user.username == sample_user_data["username"]
            service.user_repo.create_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_username_exists(self, mock_db_session, sample_user_data):
        """Test registration with existing username."""
        service = AuthService(mock_db_session)
        
        existing_user = User(id=1, username=sample_user_data["username"])
        service.user_repo.get_by_username = AsyncMock(return_value=existing_user)
        
        with pytest.raises(ConflictError, match="Username already exists"):
            await service.register(
                username=sample_user_data["username"],
                name=sample_user_data["name"],
                email=sample_user_data["email"],
                password=sample_user_data["password"]
            )
    
    @pytest.mark.asyncio
    async def test_register_email_exists(self, mock_db_session, sample_user_data):
        """Test registration with existing email."""
        service = AuthService(mock_db_session)
        
        service.user_repo.get_by_username = AsyncMock(return_value=None)
        existing_user = User(id=1, email=sample_user_data["email"])
        service.user_repo.get_by_email = AsyncMock(return_value=existing_user)
        
        with pytest.raises(ConflictError, match="Email already exists"):
            await service.register(
                username=sample_user_data["username"],
                name=sample_user_data["name"],
                email=sample_user_data["email"],
                password=sample_user_data["password"]
            )


class TestAuthServiceLogin:
    """Test user login."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, mock_db_session, sample_user_data):
        """Test successful login."""
        service = AuthService(mock_db_session)
        
        mock_user = User(
            id=1,
            username=sample_user_data["username"],
            email=sample_user_data["email"],
            hashed_password=hash_password(sample_user_data["password"]),
            is_active=True,
            failed_login_attempts=0,
            locked_until=None
        )
        
        service.user_repo.get_by_username_or_email = AsyncMock(return_value=mock_user)
        service.user_repo.reset_failed_attempts = AsyncMock(return_value=mock_user)
        
        with patch("app.services.auth_service.check_rate_limit", return_value=True):
            token = await service.login(
                identifier=sample_user_data["username"],
                password=sample_user_data["password"]
            )
            
            assert token is not None
            assert isinstance(token, str)
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_db_session):
        """Test login with invalid credentials."""
        service = AuthService(mock_db_session)
        
        service.user_repo.get_by_username_or_email = AsyncMock(return_value=None)
        
        with patch("app.services.auth_service.check_rate_limit", return_value=True):
            with pytest.raises(UnauthorizedError, match="Invalid credentials"):
                await service.login("nonexistent", "wrongpass")
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, mock_db_session, sample_user_data):
        """Test login with wrong password."""
        service = AuthService(mock_db_session)
        
        mock_user = User(
            id=1,
            username=sample_user_data["username"],
            hashed_password=hash_password(sample_user_data["password"]),
            is_active=True,
            failed_login_attempts=0
        )
        
        service.user_repo.get_by_username_or_email = AsyncMock(return_value=mock_user)
        service.user_repo.increment_failed_attempts = AsyncMock(return_value=mock_user)
        
        with patch("app.services.auth_service.check_rate_limit", return_value=True):
            with pytest.raises(UnauthorizedError, match="Invalid credentials"):
                await service.login(sample_user_data["username"], "wrongpassword")
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, mock_db_session, sample_user_data):
        """Test login with inactive user."""
        service = AuthService(mock_db_session)
        
        mock_user = User(
            id=1,
            username=sample_user_data["username"],
            hashed_password=hash_password(sample_user_data["password"]),
            is_active=False,
            failed_login_attempts=0
        )
        
        service.user_repo.get_by_username_or_email = AsyncMock(return_value=mock_user)
        
        with patch("app.services.auth_service.check_rate_limit", return_value=True):
            with pytest.raises(ForbiddenError, match="User account is inactive"):
                await service.login(
                    sample_user_data["username"],
                    sample_user_data["password"]
                )
