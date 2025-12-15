"""Tests for UserRepository."""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from app.repositories.user_repo import UserRepository
from app.models.user import User
from app.core.config import settings
from app.core.security import hash_password


class TestUserRepository:
    """Test UserRepository methods."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, test_db, sample_user_data):
        """Test user creation."""
        repo = UserRepository(test_db)
        
        user = await repo.create_user(
            username=sample_user_data["username"],
            name=sample_user_data["name"],
            email=sample_user_data["email"],
            hashed_password=hash_password(sample_user_data["password"]),
            phone=sample_user_data["phone"]
        )
        
        assert user.id is not None
        assert user.username == sample_user_data["username"]
        assert user.email == sample_user_data["email"]
        assert user.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_by_username(self, test_db, sample_user_data):
        """Test getting user by username."""
        repo = UserRepository(test_db)
        
        # Create user
        user = await repo.create_user(
            username=sample_user_data["username"],
            name=sample_user_data["name"],
            email=sample_user_data["email"],
            hashed_password=hash_password(sample_user_data["password"])
        )
        
        # Retrieve user
        found_user = await repo.get_by_username(sample_user_data["username"])
        
        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.username == user.username
    
    @pytest.mark.asyncio
    async def test_get_by_email(self, test_db, sample_user_data):
        """Test getting user by email."""
        repo = UserRepository(test_db)
        
        # Create user
        user = await repo.create_user(
            username=sample_user_data["username"],
            name=sample_user_data["name"],
            email=sample_user_data["email"],
            hashed_password=hash_password(sample_user_data["password"])
        )
        
        # Retrieve user
        found_user = await repo.get_by_email(sample_user_data["email"])
        
        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.email == user.email
    
    @pytest.mark.asyncio
    async def test_increment_failed_attempts(self, test_db, sample_user_data):
        """Test incrementing failed login attempts."""
        repo = UserRepository(test_db)
        
        user = await repo.create_user(
            username=sample_user_data["username"],
            name=sample_user_data["name"],
            email=sample_user_data["email"],
            hashed_password=hash_password(sample_user_data["password"])
        )
        
        initial_attempts = user.failed_login_attempts
        
        # Increment attempts
        updated_user = await repo.increment_failed_attempts(user)
        
        assert updated_user.failed_login_attempts == initial_attempts + 1
    
    @pytest.mark.asyncio
    async def test_increment_failed_attempts_locks_account(self, test_db, sample_user_data):
        """Test that account gets locked after max attempts."""
        repo = UserRepository(test_db)
        
        user = await repo.create_user(
            username=sample_user_data["username"],
            name=sample_user_data["name"],
            email=sample_user_data["email"],
            hashed_password=hash_password(sample_user_data["password"])
        )
        
        # Set attempts to just below threshold
        user.failed_login_attempts = settings.MAX_LOGIN_ATTEMPTS - 1
        await test_db.commit()
        
        # Increment should lock account
        updated_user = await repo.increment_failed_attempts(user)
        
        assert updated_user.locked_until is not None
        assert updated_user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS
    
    @pytest.mark.asyncio
    async def test_reset_failed_attempts(self, test_db, sample_user_data):
        """Test resetting failed login attempts."""
        repo = UserRepository(test_db)
        
        user = await repo.create_user(
            username=sample_user_data["username"],
            name=sample_user_data["name"],
            email=sample_user_data["email"],
            hashed_password=hash_password(sample_user_data["password"])
        )
        
        # Set some failed attempts and lock
        user.failed_login_attempts = 5
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        await test_db.commit()
        
        # Reset attempts
        updated_user = await repo.reset_failed_attempts(user)
        
        assert updated_user.failed_login_attempts == 0
        assert updated_user.locked_until is None
    
    @pytest.mark.asyncio
    async def test_soft_delete_user(self, test_db, sample_user_data):
        """Test soft deleting a user."""
        repo = UserRepository(test_db)
        
        user = await repo.create_user(
            username=sample_user_data["username"],
            name=sample_user_data["name"],
            email=sample_user_data["email"],
            hashed_password=hash_password(sample_user_data["password"])
        )
        
        # Soft delete
        deleted_user = await repo.soft_delete_user(user)
        
        assert deleted_user.deleted_at is not None
        assert deleted_user.is_deleted is True
    
    @pytest.mark.asyncio
    async def test_get_by_username_excludes_deleted(self, test_db, sample_user_data):
        """Test that deleted users are excluded by default."""
        repo = UserRepository(test_db)
        
        user = await repo.create_user(
            username=sample_user_data["username"],
            name=sample_user_data["name"],
            email=sample_user_data["email"],
            hashed_password=hash_password(sample_user_data["password"])
        )
        
        # Soft delete
        await repo.soft_delete_user(user)
        
        # Should not find deleted user
        found_user = await repo.get_by_username(sample_user_data["username"], include_deleted=False)
        assert found_user is None
        
        # Should find with include_deleted=True
        found_user = await repo.get_by_username(sample_user_data["username"], include_deleted=True)
        assert found_user is not None
