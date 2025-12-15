"""Admin repository for database operations."""
from typing import Optional
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Admin
from app.core.config import settings


class AdminRepository:
    """Repository for admin database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize AdminRepository with database session."""
        self.db = db

    async def get_by_username(self, username: str, include_deleted: bool = False) -> Optional[Admin]:
        """Get admin by username, optionally including soft deleted admins."""
        query = select(Admin).where(Admin.username == username)
        if not include_deleted:
            query = query.where(Admin.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str, include_deleted: bool = False) -> Optional[Admin]:
        """Get admin by email, optionally including soft deleted admins."""
        query = select(Admin).where(Admin.email == email)
        if not include_deleted:
            query = query.where(Admin.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username_or_email(self, identifier: str, include_deleted: bool = False) -> Optional[Admin]:
        """Get admin by username or email, optionally including soft deleted admins."""
        query = select(Admin).where(
            or_(Admin.username == identifier, Admin.email == identifier)
        )
        if not include_deleted:
            query = query.where(Admin.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str, include_deleted: bool = False) -> Optional[Admin]:
        """Get admin by phone, optionally including soft deleted admins."""
        query = select(Admin).where(Admin.phone == phone)
        if not include_deleted:
            query = query.where(Admin.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, admin_id: int, include_deleted: bool = False) -> Optional[Admin]:
        """Get admin by ID, optionally including soft deleted admins."""
        query = select(Admin).where(Admin.id == admin_id)
        if not include_deleted:
            query = query.where(Admin.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_admin(
        self,
        username: str,
        name: str,
        email: str,
        hashed_password: str,
        phone: Optional[str] = None,
        avatar: Optional[str] = None,
        is_active: bool = True
    ) -> Admin:
        """Create a new admin."""
        admin = Admin(
            username=username,
            name=name,
            email=email,
            phone=phone,
            hashed_password=hashed_password,
            avatar=avatar,
            is_active=is_active
        )
        self.db.add(admin)
        await self.db.commit()
        await self.db.refresh(admin)
        return admin

    async def increment_failed_attempts(self, admin: Admin) -> Admin:
        """Increment failed login attempts and lock account if threshold reached."""
        admin.failed_login_attempts += 1
        
        if admin.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            admin.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
        
        await self.db.commit()
        await self.db.refresh(admin)
        return admin

    async def reset_failed_attempts(self, admin: Admin) -> Admin:
        """Reset failed login attempts and unlock account."""
        admin.failed_login_attempts = 0
        admin.locked_until = None
        await self.db.commit()
        await self.db.refresh(admin)
        return admin

    async def lock_account(self, admin: Admin) -> Admin:
        """Lock admin account."""
        admin.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
        await self.db.commit()
        await self.db.refresh(admin)
        return admin

    async def unlock_account(self, admin: Admin) -> Admin:
        """Unlock admin account."""
        admin.locked_until = None
        admin.failed_login_attempts = 0
        await self.db.commit()
        await self.db.refresh(admin)
        return admin

    async def soft_delete_admin(self, admin: Admin) -> Admin:
        """Soft delete an admin."""
        admin.soft_delete()
        await self.db.commit()
        await self.db.refresh(admin)
        return admin

    async def restore_admin(self, admin: Admin) -> Admin:
        """Restore a soft deleted admin."""
        admin.restore()
        await self.db.commit()
        await self.db.refresh(admin)
        return admin
