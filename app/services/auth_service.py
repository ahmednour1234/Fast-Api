"""Authentication service for user operations."""
import asyncio
from typing import Optional
from datetime import datetime, timezone

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
from app.repositories.user_repo import UserRepository
from app.services.audit_service import AuditService
from app.models.user import User
from app.utils.upload import save_image


class AuthService:
    """Service for user authentication operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize AuthService with database session."""
        self.user_repo = UserRepository(db)
        self.audit_service = AuditService(db)

    async def register(
        self,
        username: str,
        name: str,
        email: str,  # Will be validated by Pydantic EmailStr in the route
        password: str,
        phone: Optional[str] = None,
        avatar: Optional[UploadFile] = None
    ) -> User:
        """Register a new user."""
        # Check if username already exists
        existing_username = await self.user_repo.get_by_username(username, include_deleted=False)
        if existing_username:
            raise ConflictError("Username already exists")

        # Check if email already exists
        existing_email = await self.user_repo.get_by_email(email, include_deleted=False)
        if existing_email:
            raise ConflictError("Email already exists")

        # Check if phone already exists (if provided)
        if phone:
            existing_phone = await self.user_repo.get_by_phone(phone, include_deleted=False)
            if existing_phone:
                raise ConflictError("Phone number already exists")

        # Handle avatar upload if provided
        avatar_filename = None
        if avatar:
            avatar_filename = await save_image(avatar)

        # Create user with hashed password
        hashed = hash_password(password)
        user = await self.user_repo.create_user(
            username=username,
            name=name,
            email=email,
            hashed_password=hashed,
            phone=phone,
            avatar=avatar_filename
        )
        return user

    async def login(self, identifier: str, password: str, request: Optional[Request] = None) -> str:
        """Authenticate user and return access token."""
        # Check rate limiting (skip if request not available)
        if request and not check_rate_limit(request):
            await self.audit_service.log_login(
                entity_type="user",
                entity_id=0,  # Unknown user
                success=False,
                request=request,
                error_message="Rate limit exceeded"
            )
            raise get_rate_limit_exception()

        # Find user by username or email
        user = await self.user_repo.get_by_username_or_email(identifier, include_deleted=False)
        
        if not user:
            # Add delay to prevent timing attacks
            await asyncio.sleep(0.5)
            await self.audit_service.log_login(
                entity_type="user",
                entity_id=0,
                success=False,
                request=request,
                error_message="User not found"
            )
            raise UnauthorizedError("Invalid credentials")

        # Check if account is locked
        now = datetime.now(timezone.utc)
        if user.locked_until and user.locked_until > now:
            remaining_minutes = int((user.locked_until - now).total_seconds() / 60)
            await self.audit_service.log_login(
                entity_type="user",
                entity_id=user.id,
                success=False,
                request=request,
                error_message=f"Account locked until {user.locked_until}"
            )
            raise UnauthorizedError(f"Account is locked. Please try again in {remaining_minutes} minutes.")

        # Verify password
        if not verify_password(password, user.hashed_password):
            # Increment failed attempts
            await self.user_repo.increment_failed_attempts(user)
            # Add delay to prevent timing attacks
            await asyncio.sleep(0.5)
            await self.audit_service.log_login(
                entity_type="user",
                entity_id=user.id,
                success=False,
                request=request,
                error_message="Invalid password"
            )
            raise UnauthorizedError("Invalid credentials")

        # Check if user is active
        if not user.is_active:
            await self.audit_service.log_login(
                entity_type="user",
                entity_id=user.id,
                success=False,
                request=request,
                error_message="Account inactive"
            )
            raise ForbiddenError("User account is inactive")

        # Reset failed attempts on successful login
        if user.failed_login_attempts > 0:
            await self.user_repo.reset_failed_attempts(user)

        # Log successful login
        await self.audit_service.log_login(
            entity_type="user",
            entity_id=user.id,
            success=True,
            request=request
        )

        # Create and return access token
        token = create_access_token(subject=user.username)
        return token
