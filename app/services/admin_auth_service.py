import asyncio
from typing import Optional
from fastapi import UploadFile
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError, ForbiddenError
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    check_rate_limit,
    get_rate_limit_exception
)
from app.repositories.admin_repo import AdminRepository
from app.services.audit_service import AuditService
from app.models.user import Admin
from app.utils.upload import save_image
from datetime import datetime, timezone


class AdminAuthService:
    """Service for admin authentication operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize AdminAuthService with database session."""
        self.admin_repo = AdminRepository(db)
        self.audit_service = AuditService(db)

    async def register(
        self,
        username: str,
        name: str,
        email: str,
        password: str,
        phone: Optional[str] = None,
        avatar: Optional[UploadFile] = None
    ) -> Admin:
        """Register a new admin."""
        # Check if username already exists
        existing_username = await self.admin_repo.get_by_username(username, include_deleted=False)
        if existing_username:
            raise ConflictError("Username already exists")

        # Check if email already exists
        existing_email = await self.admin_repo.get_by_email(email, include_deleted=False)
        if existing_email:
            raise ConflictError("Email already exists")

        # Check if phone already exists (if provided)
        if phone:
            existing_phone = await self.admin_repo.get_by_phone(phone, include_deleted=False)
            if existing_phone:
                raise ConflictError("Phone number already exists")

        # Handle avatar upload if provided
        avatar_filename = None
        if avatar:
            avatar_filename = await save_image(avatar)

        # Create admin with hashed password
        hashed = hash_password(password)
        admin = await self.admin_repo.create_admin(
            username=username,
            name=name,
            email=email,
            hashed_password=hashed,
            phone=phone,
            avatar=avatar_filename
        )
        return admin

    async def login(self, identifier: str, password: str, request: Optional[Request] = None) -> str:
        """Authenticate admin and return access token."""
        # Check rate limiting
        if request and not check_rate_limit(request):
            await self.audit_service.log_login(
                entity_type="admin",
                entity_id=0,
                success=False,
                request=request,
                error_message="Rate limit exceeded"
            )
            raise get_rate_limit_exception()

        # Find admin by username or email
        admin = await self.admin_repo.get_by_username_or_email(identifier, include_deleted=False)
        
        if not admin:
            await asyncio.sleep(0.5)
            await self.audit_service.log_login(
                entity_type="admin",
                entity_id=0,
                success=False,
                request=request,
                error_message="Admin not found"
            )
            raise UnauthorizedError("Invalid credentials")

        # Check if account is locked
        now = datetime.now(timezone.utc)
        if admin.locked_until and admin.locked_until > now:
            remaining_minutes = int((admin.locked_until - now).total_seconds() / 60)
            await self.audit_service.log_login(
                entity_type="admin",
                entity_id=admin.id,
                success=False,
                request=request,
                error_message=f"Account locked until {admin.locked_until}"
            )
            raise UnauthorizedError(f"Admin account is locked. Please try again in {remaining_minutes} minutes.")

        # Verify password
        if not verify_password(password, admin.hashed_password):
            await self.admin_repo.increment_failed_attempts(admin)
            await asyncio.sleep(0.5)
            await self.audit_service.log_login(
                entity_type="admin",
                entity_id=admin.id,
                success=False,
                request=request,
                error_message="Invalid password"
            )
            raise UnauthorizedError("Invalid credentials")

        # Check if admin is active
        if not admin.is_active:
            await self.audit_service.log_login(
                entity_type="admin",
                entity_id=admin.id,
                success=False,
                request=request,
                error_message="Account inactive"
            )
            raise ForbiddenError("Admin account is inactive")

        # Reset failed attempts on successful login
        if admin.failed_login_attempts > 0:
            await self.admin_repo.reset_failed_attempts(admin)

        # Log successful login
        await self.audit_service.log_login(
            entity_type="admin",
            entity_id=admin.id,
            success=True,
            request=request
        )

        # Create and return access token
        token = create_access_token(subject=admin.username)
        return token
