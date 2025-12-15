from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.exceptions import NotFoundError, ConflictError
from app.core.security import hash_password
from app.repositories.admin_repo import AdminRepository
from app.models.user import Admin


class AdminService:
    def __init__(self, db: AsyncSession):
        self.admin_repo = AdminRepository(db)
        self.db = db

    async def get_admin_by_id(self, admin_id: int, include_deleted: bool = False) -> Optional[Admin]:
        """Get admin by ID."""
        return await self.admin_repo.get_by_id(admin_id, include_deleted=include_deleted)

    async def get_all_admins(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> Tuple[List[Admin], int]:
        """Get all admins with pagination."""
        query = select(Admin)
        if not include_deleted:
            query = query.where(Admin.deleted_at.is_(None))
        
        # Get total count
        count_query = select(func.count()).select_from(Admin)
        if not include_deleted:
            count_query = count_query.where(Admin.deleted_at.is_(None))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Admin.created_at.desc())
        result = await self.db.execute(query)
        admins = result.scalars().all()
        
        return list(admins), total

    async def update_admin(
        self,
        admin: Admin,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        password: Optional[str] = None,
        avatar: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Admin:
        """Update admin data."""
        # Check email uniqueness if email is being updated
        if email and email != admin.email:
            existing = await self.admin_repo.get_by_email(email, include_deleted=False)
            if existing and existing.id != admin.id:
                raise ConflictError("Email already exists")

        # Check phone uniqueness if phone is being updated
        if phone and phone != admin.phone:
            if phone:  # Only check if phone is not None/empty
                existing = await self.admin_repo.get_by_phone(phone, include_deleted=False)
                if existing and existing.id != admin.id:
                    raise ConflictError("Phone number already exists")

        # Update fields
        if name is not None:
            admin.name = name
        if email is not None:
            admin.email = email
        if phone is not None:
            admin.phone = phone
        if password is not None:
            admin.hashed_password = hash_password(password)
        if avatar is not None:
            admin.avatar = avatar
        if is_active is not None:
            admin.is_active = is_active

        await self.db.commit()
        await self.db.refresh(admin)
        return admin

    async def activate_admin(self, admin: Admin) -> Admin:
        """Activate an admin."""
        admin.is_active = True
        await self.db.commit()
        await self.db.refresh(admin)
        return admin

    async def deactivate_admin(self, admin: Admin) -> Admin:
        """Deactivate an admin."""
        admin.is_active = False
        await self.db.commit()
        await self.db.refresh(admin)
        return admin

    async def soft_delete_admin(self, admin: Admin) -> Admin:
        """Soft delete an admin."""
        return await self.admin_repo.soft_delete_admin(admin)
