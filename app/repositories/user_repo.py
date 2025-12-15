"""User repository for database operations."""
from typing import Optional
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.config import settings


class UserRepository:
    """Repository for user database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize UserRepository with database session."""
        self.db = db

    async def get_by_username(self, username: str, include_deleted: bool = False) -> Optional[User]:
        """Get user by username, optionally including soft deleted users."""
        query = select(User).where(User.username == username)
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str, include_deleted: bool = False) -> Optional[User]:
        """Get user by email, optionally including soft deleted users."""
        query = select(User).where(User.email == email)
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username_or_email(self, identifier: str, include_deleted: bool = False) -> Optional[User]:
        """Get user by username or email, optionally including soft deleted users."""
        query = select(User).where(
            or_(User.username == identifier, User.email == identifier)
        )
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str, include_deleted: bool = False) -> Optional[User]:
        """Get user by phone, optionally including soft deleted users."""
        query = select(User).where(User.phone == phone)
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int, include_deleted: bool = False) -> Optional[User]:
        """Get user by ID, optionally including soft deleted users."""
        query = select(User).where(User.id == user_id)
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        username: str,
        name: str,
        email: str,
        hashed_password: str,
        phone: Optional[str] = None,
        avatar: Optional[str] = None
    ) -> User:
        """Create a new user."""
        user = User(
            username=username,
            name=name,
            email=email,
            phone=phone,
            hashed_password=hashed_password,
            avatar=avatar,
            is_active=True
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def increment_failed_attempts(self, user: User) -> User:
        """Increment failed login attempts and lock account if threshold reached."""
        user.failed_login_attempts += 1
        
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def reset_failed_attempts(self, user: User) -> User:
        """Reset failed login attempts and unlock account."""
        user.failed_login_attempts = 0
        user.locked_until = None
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def lock_account(self, user: User) -> User:
        """Lock user account."""
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def unlock_account(self, user: User) -> User:
        """Unlock user account."""
        user.locked_until = None
        user.failed_login_attempts = 0
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def soft_delete_user(self, user: User) -> User:
        """Soft delete a user."""
        user.soft_delete()
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def restore_user(self, user: User) -> User:
        """Restore a soft deleted user."""
        user.restore()
        await self.db.commit()
        await self.db.refresh(user)
        return user
