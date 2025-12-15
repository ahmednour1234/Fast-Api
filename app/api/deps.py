from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.repositories.user_repo import UserRepository
from app.repositories.admin_repo import AdminRepository
from app.models.user import User, Admin

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency to get the current authenticated user."""
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token")

    username: str = payload.get("sub")
    if username is None:
        raise UnauthorizedError("Invalid or expired token")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_username(username, include_deleted=False)
    
    if user is None or not user.is_active:
        raise UnauthorizedError("Invalid or expired token")

    return user


async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    """Dependency to get the current authenticated admin."""
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token")

    username: str = payload.get("sub")
    if username is None:
        raise UnauthorizedError("Invalid or expired token")

    admin_repo = AdminRepository(db)
    admin = await admin_repo.get_by_username(username, include_deleted=False)
    
    if admin is None or not admin.is_active:
        raise UnauthorizedError("Invalid or expired token")

    return admin


def require_permission(resource: str, action: str):
    """Dependency factory to check if admin has a specific permission."""
    async def permission_checker(
        current_admin: Admin = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
    ) -> Admin:
        from app.services.permission_service import PermissionService
        
        permission_service = PermissionService(db)
        has_permission = await permission_service.admin_has_permission(current_admin, resource, action)
        
        if not has_permission:
            raise ForbiddenError(f"Permission required: {resource}:{action}")
        
        return current_admin
    
    return permission_checker
