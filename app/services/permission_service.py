"""Service for permission checking."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.admin import Admin
from app.models.role import Permission


class PermissionService:
    """Service for permission operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def admin_has_permission(self, admin: Admin, resource: str, action: str) -> bool:
        """Check if admin has a specific permission."""
        # Load admin roles with permissions
        await self.db.refresh(admin, ["roles"])
        
        # Check if admin has any role with the required permission
        for role in admin.roles:
            if not role.is_active:
                continue
            
            await self.db.refresh(role, ["permissions"])
            for permission in role.permissions:
                if permission.resource == resource and permission.action == action:
                    return True
        
        return False

    async def admin_has_any_permission(self, admin: Admin, permissions: list[tuple[str, str]]) -> bool:
        """Check if admin has any of the specified permissions."""
        for resource, action in permissions:
            if await self.admin_has_permission(admin, resource, action):
                return True
        return False

    async def admin_has_all_permissions(self, admin: Admin, permissions: list[tuple[str, str]]) -> bool:
        """Check if admin has all of the specified permissions."""
        for resource, action in permissions:
            if not await self.admin_has_permission(admin, resource, action):
                return False
        return True