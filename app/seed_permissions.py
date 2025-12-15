"""Seeder for default permissions and roles."""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.repositories.role_repo import RoleRepository, PermissionRepository
from app.repositories.admin_repo import AdminRepository


async def seed_permissions_and_roles():
    """Seed default permissions and roles."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        permission_repo = PermissionRepository(session)
        role_repo = RoleRepository(session)
        admin_repo = AdminRepository(session)

        # Define default permissions
        default_permissions = [
            # Collections permissions
            ("collections:create", "collections", "create", "Create collections"),
            ("collections:read", "collections", "read", "Read collections"),
            ("collections:update", "collections", "update", "Update collections"),
            ("collections:delete", "collections", "delete", "Delete collections"),
            
            # Users permissions
            ("users:create", "users", "create", "Create users"),
            ("users:read", "users", "read", "Read users"),
            ("users:update", "users", "update", "Update users"),
            ("users:delete", "users", "delete", "Delete users"),
            
            # Admins permissions
            ("admins:create", "admins", "create", "Create admins"),
            ("admins:read", "admins", "read", "Read admins"),
            ("admins:update", "admins", "update", "Update admins"),
            ("admins:delete", "admins", "delete", "Delete admins"),
            
            # Settings permissions
            ("settings:create", "settings", "create", "Create settings"),
            ("settings:read", "settings", "read", "Read settings"),
            ("settings:update", "settings", "update", "Update settings"),
            ("settings:delete", "settings", "delete", "Delete settings"),
            
            # Roles permissions
            ("roles:create", "roles", "create", "Create roles"),
            ("roles:read", "roles", "read", "Read roles"),
            ("roles:update", "roles", "update", "Update roles"),
            ("roles:delete", "roles", "delete", "Delete roles"),
            
            # Audit logs permissions
            ("audit_logs:read", "audit_logs", "read", "Read audit logs"),
        ]

        created_permissions = []
        for name, resource, action, description in default_permissions:
            existing = await permission_repo.get_permission_by_name(name)
            if not existing:
                permission = await permission_repo.create_permission(
                    name=name,
                    resource=resource,
                    action=action,
                    description=description
                )
                created_permissions.append(permission)
                print(f"[OK] Permission created: {name}")
            else:
                created_permissions.append(existing)
                print(f"[OK] Permission already exists: {name}")

        # Create default roles
        # Super Admin - has all permissions
        super_admin_role = await role_repo.get_role_by_name("Super Admin")
        if not super_admin_role:
            super_admin_role = await role_repo.create_role(
                name="Super Admin",
                description="Full access to all resources",
                is_active=True
            )
            # Assign all permissions
            all_permission_ids = [p.id for p in created_permissions]
            super_admin_role = await role_repo.assign_permissions_to_role(super_admin_role, all_permission_ids)
            print(f"[OK] Role created: Super Admin")
        else:
            print(f"[OK] Role already exists: Super Admin")

        # Admin - has most permissions except role management
        admin_role = await role_repo.get_role_by_name("Admin")
        if not admin_role:
            admin_role = await role_repo.create_role(
                name="Admin",
                description="Administrative access with limited role management",
                is_active=True
            )
            # Assign permissions except role management
            admin_permission_ids = [
                p.id for p in created_permissions
                if not p.name.startswith("roles:")
            ]
            admin_role = await role_repo.assign_permissions_to_role(admin_role, admin_permission_ids)
            print(f"[OK] Role created: Admin")
        else:
            print(f"[OK] Role already exists: Admin")
            # Update permissions if needed
            await session.refresh(admin_role, ["permissions"])
            existing_permission_ids = {p.id for p in admin_role.permissions}
            admin_permission_ids = [
                p.id for p in created_permissions
                if not p.name.startswith("roles:")
            ]
            if set(admin_permission_ids) != existing_permission_ids:
                admin_role = await role_repo.assign_permissions_to_role(admin_role, admin_permission_ids)
                print(f"[OK] Permissions updated for Admin role")

        # Manager - has read and update permissions
        manager_role = await role_repo.get_role_by_name("Manager")
        if not manager_role:
            manager_role = await role_repo.create_role(
                name="Manager",
                description="Manager access with read and update permissions",
                is_active=True
            )
            # Assign read and update permissions
            manager_permission_ids = [
                p.id for p in created_permissions
                if p.action in ["read", "update"] and not p.name.startswith("roles:")
            ]
            manager_role = await role_repo.assign_permissions_to_role(manager_role, manager_permission_ids)
            print(f"[OK] Role created: Manager")
        else:
            print(f"[OK] Role already exists: Manager")
            # Update permissions if needed
            await session.refresh(manager_role, ["permissions"])
            existing_permission_ids = {p.id for p in manager_role.permissions}
            manager_permission_ids = [
                p.id for p in created_permissions
                if p.action in ["read", "update"] and not p.name.startswith("roles:")
            ]
            if set(manager_permission_ids) != existing_permission_ids:
                manager_role = await role_repo.assign_permissions_to_role(manager_role, manager_permission_ids)
                print(f"[OK] Permissions updated for Manager role")

        # Assign Super Admin role to existing admin user
        admin = await admin_repo.get_by_username("admin", include_deleted=False)
        if admin and super_admin_role:
            await session.refresh(admin, ["roles"])
            if not admin.roles or super_admin_role not in admin.roles:
                await role_repo.assign_roles_to_admin(admin, [super_admin_role.id])
                print(f"[OK] Super Admin role assigned to admin user")
            else:
                print(f"[OK] Admin user already has Super Admin role")

        print("\n" + "="*50)
        print("PERMISSIONS AND ROLES SEEDING COMPLETE")
        print("="*50)
        print(f"\nCreated {len(created_permissions)} permissions")
        print(f"Created 3 default roles: Super Admin, Admin, Manager")
        print(f"\nDefault admin user has been assigned 'Super Admin' role")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_permissions_and_roles())
