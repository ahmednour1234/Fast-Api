"""User management service."""
from typing import Optional, Tuple, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.exceptions import ConflictError
from app.core.security import hash_password
from app.repositories.user_repo import UserRepository
from app.models.user import User


class UserService:
    """Service for user management operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize UserService with database session."""
        self.user_repo = UserRepository(db)
        self.db = db

    async def get_user_by_id(self, user_id: int, include_deleted: bool = False) -> Optional[User]:
        """Get user by ID."""
        return await self.user_repo.get_by_id(user_id, include_deleted=include_deleted)

    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> Tuple[List[User], int]:
        """Get all users with pagination."""
        query = select(User)
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        
        # Get total count
        count_query = select(func.count()).select_from(User)
        if not include_deleted:
            count_query = count_query.where(User.deleted_at.is_(None))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return list(users), total

    async def update_user(
        self,
        user: User,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        password: Optional[str] = None,
        avatar: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> User:
        """Update user data."""
        # Check email uniqueness if email is being updated
        if email and email != user.email:
            existing = await self.user_repo.get_by_email(email, include_deleted=False)
            if existing and existing.id != user.id:
                raise ConflictError("Email already exists")

        # Check phone uniqueness if phone is being updated
        if phone and phone != user.phone:
            if phone:  # Only check if phone is not None/empty
                existing = await self.user_repo.get_by_phone(phone, include_deleted=False)
                if existing and existing.id != user.id:
                    raise ConflictError("Phone number already exists")

        # Update fields
        if name is not None:
            user.name = name
        if email is not None:
            user.email = email
        if phone is not None:
            user.phone = phone
        if password is not None:
            user.hashed_password = hash_password(password)
        if avatar is not None:
            user.avatar = avatar
        if is_active is not None:
            user.is_active = is_active

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def activate_user(self, user: User) -> User:
        """Activate a user."""
        user.is_active = True
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def deactivate_user(self, user: User) -> User:
        """Deactivate a user."""
        user.is_active = False
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def soft_delete_user(self, user: User) -> User:
        """Soft delete a user."""
        return await self.user_repo.soft_delete_user(user)
