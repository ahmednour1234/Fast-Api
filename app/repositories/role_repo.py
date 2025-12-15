"""Repository for role and permission operations."""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role, Permission
from app.models.admin import Admin


class RoleRepository:
    """Repository for role database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        query = select(Role).where(Role.id == role_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        query = select(Role).where(Role.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_roles(self) -> List[Role]:
        """Get all roles."""
        query = select(Role).order_by(Role.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_role(
        self,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True
    ) -> Role:
        """Create a new role."""
        role = Role(
            name=name,
            description=description,
            is_active=is_active
        )
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def update_role(
        self,
        role: Role,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Role:
        """Update a role."""
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        if is_active is not None:
            role.is_active = is_active
        
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def assign_permissions_to_role(self, role: Role, permission_ids: List[int]) -> Role:
        """Assign permissions to a role."""
        from sqlalchemy.orm import selectinload
        
        # Load permissions
        query = select(Permission).where(Permission.id.in_(permission_ids))
        result = await self.db.execute(query)
        permissions = list(result.scalars().all())
        
        # Refresh role with permissions relationship loaded
        await self.db.refresh(role, ["permissions"])
        
        # Assign permissions
        role.permissions = permissions
        await self.db.commit()
        await self.db.refresh(role, ["permissions"])
        return role

    async def assign_roles_to_admin(self, admin: Admin, role_ids: List[int]) -> Admin:
        """Assign roles to an admin."""
        # Load roles
        query = select(Role).where(Role.id.in_(role_ids))
        result = await self.db.execute(query)
        roles = list(result.scalars().all())
        
        # Refresh admin with roles relationship loaded
        await self.db.refresh(admin, ["roles"])
        
        # Assign roles
        admin.roles = roles
        await self.db.commit()
        await self.db.refresh(admin, ["roles"])
        return admin


class PermissionRepository:
    """Repository for permission database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_permission_by_id(self, permission_id: int) -> Optional[Permission]:
        """Get permission by ID."""
        query = select(Permission).where(Permission.id == permission_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_permission_by_name(self, name: str) -> Optional[Permission]:
        """Get permission by name."""
        query = select(Permission).where(Permission.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_permissions(self) -> List[Permission]:
        """Get all permissions."""
        query = select(Permission).order_by(Permission.resource, Permission.action)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_permissions_by_resource(self, resource: str) -> List[Permission]:
        """Get permissions by resource."""
        query = select(Permission).where(Permission.resource == resource)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_permission(
        self,
        name: str,
        resource: str,
        action: str,
        description: Optional[str] = None
    ) -> Permission:
        """Create a new permission."""
        permission = Permission(
            name=name,
            resource=resource,
            action=action,
            description=description
        )
        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)
        return permission