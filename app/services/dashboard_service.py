"""Service for dashboard statistics."""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.admin import Admin
from app.models.collection import Collection
from app.models.audit_log import AuditLog


class DashboardService:
    """Service for dashboard operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_statistics(self) -> dict:
        """Get dashboard statistics."""
        # Count users
        user_count_query = select(func.count()).select_from(User).where(User.deleted_at.is_(None))
        user_result = await self.db.execute(user_count_query)
        total_users = user_result.scalar() or 0

        # Count active users
        active_user_query = select(func.count()).select_from(User).where(
            User.deleted_at.is_(None),
            User.is_active == True
        )
        active_user_result = await self.db.execute(active_user_query)
        active_users = active_user_result.scalar() or 0

        # Count admins
        admin_count_query = select(func.count()).select_from(Admin).where(Admin.deleted_at.is_(None))
        admin_result = await self.db.execute(admin_count_query)
        total_admins = admin_result.scalar() or 0

        # Count active admins
        active_admin_query = select(func.count()).select_from(Admin).where(
            Admin.deleted_at.is_(None),
            Admin.is_active == True
        )
        active_admin_result = await self.db.execute(active_admin_query)
        active_admins = active_admin_result.scalar() or 0

        # Count collections
        collection_count_query = select(func.count()).select_from(Collection).where(Collection.deleted_at.is_(None))
        collection_result = await self.db.execute(collection_count_query)
        total_collections = collection_result.scalar() or 0

        # Count active collections
        active_collection_query = select(func.count()).select_from(Collection).where(
            Collection.deleted_at.is_(None),
            Collection.is_active == True
        )
        active_collection_result = await self.db.execute(active_collection_query)
        active_collections = active_collection_result.scalar() or 0

        # Count recent login attempts (last 24 hours)
        from datetime import datetime, timedelta, timezone
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        login_query = select(func.count()).select_from(AuditLog).where(
            AuditLog.action == "login",
            AuditLog.created_at >= yesterday
        )
        login_result = await self.db.execute(login_query)
        recent_logins = login_result.scalar() or 0

        # Count successful logins (last 24 hours)
        successful_login_query = select(func.count()).select_from(AuditLog).where(
            AuditLog.action == "login",
            AuditLog.success == True,
            AuditLog.created_at >= yesterday
        )
        successful_login_result = await self.db.execute(successful_login_query)
        successful_logins = successful_login_result.scalar() or 0

        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "inactive": total_users - active_users
            },
            "admins": {
                "total": total_admins,
                "active": active_admins,
                "inactive": total_admins - active_admins
            },
            "collections": {
                "total": total_collections,
                "active": active_collections,
                "inactive": total_collections - active_collections
            },
            "logins": {
                "recent_24h": recent_logins,
                "successful_24h": successful_logins,
                "failed_24h": recent_logins - successful_logins
            }
        }