"""Routes for role and permission management."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.core.resources import ResponseResource
from app.core.exceptions import NotFoundError, ConflictError
from app.repositories.role_repo import RoleRepository, PermissionRepository
from app.repositories.admin_repo import AdminRepository
from app.schemas.role import (
    RoleResponse,
    RoleCreateRequest,
    RoleUpdateRequest,
    PermissionResponse,
    PermissionCreateRequest
)
from app.models.user import Admin
from app.services.audit_service import AuditService
from app.models.audit_log import AuditLogAction

router = APIRouter()


# Permission endpoints
@router.get("/permissions", response_model=ResponseResource[List[PermissionResponse]])
async def get_all_permissions(
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all permissions (admin only)."""
    permission_repo = PermissionRepository(db)
    permissions = await permission_repo.get_all_permissions()
    
    return ResponseResource.success_response(
        data=[PermissionResponse.model_validate(p) for p in permissions],
        message="Permissions retrieved successfully"
    )


@router.post("/permissions", response_model=ResponseResource[PermissionResponse], status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new permission (admin only)."""
    permission_repo = PermissionRepository(db)
    audit_service = AuditService(db)
    
    # Check if permission already exists
    existing = await permission_repo.get_permission_by_name(permission_data.name)
    if existing:
        raise ConflictError(f"Permission '{permission_data.name}' already exists")
    
    permission = await permission_repo.create_permission(
        name=permission_data.name,
        resource=permission_data.resource,
        action=permission_data.action,
        description=permission_data.description
    )
    
    # Log the action
    await audit_service.log_action(
        action=AuditLogAction.CREATE,
        entity_type="permission",
        entity_id=permission.id,
        admin_id=current_admin.id,
        description=f"Permission '{permission.name}' created",
        success=True,
        request=None
    )
    
    return ResponseResource.success_response(
        data=PermissionResponse.model_validate(permission),
        message="Permission created successfully"
    )


# Role endpoints
@router.get("/roles", response_model=ResponseResource[List[RoleResponse]])
async def get_all_roles(
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all roles (admin only)."""
    role_repo = RoleRepository(db)
    roles = await role_repo.get_all_roles()
    
    # Load permissions for each role
    for role in roles:
        await db.refresh(role, ["permissions"])
    
    return ResponseResource.success_response(
        data=[RoleResponse.model_validate(r) for r in roles],
        message="Roles retrieved successfully"
    )


@router.get("/roles/{role_id}", response_model=ResponseResource[RoleResponse])
async def get_role(
    role_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific role by ID (admin only)."""
    role_repo = RoleRepository(db)
    role = await role_repo.get_role_by_id(role_id)
    
    if not role:
        raise NotFoundError(resource="Role", resource_id=role_id)
    
    await db.refresh(role, ["permissions"])
    
    return ResponseResource.success_response(
        data=RoleResponse.model_validate(role),
        message="Role retrieved successfully"
    )


@router.post("/roles", response_model=ResponseResource[RoleResponse], status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new role (admin only)."""
    role_repo = RoleRepository(db)
    audit_service = AuditService(db)
    
    # Check if role already exists
    existing = await role_repo.get_role_by_name(role_data.name)
    if existing:
        raise ConflictError(f"Role '{role_data.name}' already exists")
    
    role = await role_repo.create_role(
        name=role_data.name,
        description=role_data.description,
        is_active=role_data.is_active
    )
    
    # Assign permissions if provided
    if role_data.permission_ids:
        role = await role_repo.assign_permissions_to_role(role, role_data.permission_ids)
    
    await db.refresh(role, ["permissions"])
    
    # Log the action
    await audit_service.log_action(
        action=AuditLogAction.CREATE,
        entity_type="role",
        entity_id=role.id,
        admin_id=current_admin.id,
        description=f"Role '{role.name}' created",
        success=True,
        request=None
    )
    
    return ResponseResource.success_response(
        data=RoleResponse.model_validate(role),
        message="Role created successfully"
    )


@router.put("/roles/{role_id}", response_model=ResponseResource[RoleResponse])
async def update_role(
    role_id: int,
    role_data: RoleUpdateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a role (admin only)."""
    role_repo = RoleRepository(db)
    audit_service = AuditService(db)
    
    role = await role_repo.get_role_by_id(role_id)
    if not role:
        raise NotFoundError(resource="Role", resource_id=role_id)
    
    # Check name uniqueness if name is being updated
    if role_data.name and role_data.name != role.name:
        existing = await role_repo.get_role_by_name(role_data.name)
        if existing:
            raise ConflictError(f"Role '{role_data.name}' already exists")
    
    role = await role_repo.update_role(
        role=role,
        name=role_data.name,
        description=role_data.description,
        is_active=role_data.is_active
    )
    
    # Update permissions if provided
    if role_data.permission_ids is not None:
        role = await role_repo.assign_permissions_to_role(role, role_data.permission_ids)
    
    await db.refresh(role, ["permissions"])
    
    # Log the action
    await audit_service.log_action(
        action=AuditLogAction.UPDATE,
        entity_type="role",
        entity_id=role.id,
        admin_id=current_admin.id,
        description=f"Role '{role.name}' updated",
        success=True,
        request=None
    )
    
    return ResponseResource.success_response(
        data=RoleResponse.model_validate(role),
        message="Role updated successfully"
    )


@router.post("/admins/{admin_id}/roles", response_model=ResponseResource[dict])
async def assign_roles_to_admin(
    admin_id: int,
    role_ids: List[int],
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Assign roles to an admin (admin only)."""
    role_repo = RoleRepository(db)
    admin_repo = AdminRepository(db)
    audit_service = AuditService(db)
    
    admin = await admin_repo.get_by_id(admin_id)
    if not admin:
        raise NotFoundError(resource="Admin", resource_id=admin_id)
    
    admin = await role_repo.assign_roles_to_admin(admin, role_ids)
    
    # Log the action
    await audit_service.log_action(
        action=AuditLogAction.UPDATE,
        entity_type="admin",
        entity_id=admin.id,
        admin_id=current_admin.id,
        description=f"Roles assigned to admin '{admin.username}'",
        success=True,
        request=None
    )
    
    return ResponseResource.success_response(
        data={"admin_id": admin.id, "role_ids": role_ids},
        message="Roles assigned successfully"
    )
