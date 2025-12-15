"""Repository for audit log operations."""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog, AuditLogAction


class AuditLogRepository:
    """Repository for audit log database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_log(
        self,
        action: AuditLogAction,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        user_id: Optional[int] = None,
        admin_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        description: Optional[str] = None,
        extra_data: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Create a new audit log entry."""
        log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            admin_id=admin_id,
            ip_address=ip_address,
            user_agent=user_agent,
            description=description,
            extra_data=extra_data,
            success=success,
            error_message=error_message
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        action: Optional[AuditLogAction] = None,
        entity_type: Optional[str] = None,
        user_id: Optional[int] = None,
        admin_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success_only: Optional[bool] = None
    ) -> List[AuditLog]:
        """Get audit logs with filters."""
        query = select(AuditLog)
        
        if action:
            query = query.where(AuditLog.action == action)
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if admin_id:
            query = query.where(AuditLog.admin_id == admin_id)
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)
        if success_only is not None:
            query = query.where(AuditLog.success == success_only)
        
        query = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_logs(
        self,
        action: Optional[AuditLogAction] = None,
        entity_type: Optional[str] = None,
        user_id: Optional[int] = None,
        admin_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Count audit logs with filters."""
        from sqlalchemy import func
        
        query = select(func.count()).select_from(AuditLog)
        
        if action:
            query = query.where(AuditLog.action == action)
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if admin_id:
            query = query.where(AuditLog.admin_id == admin_id)
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)
        
        result = await self.db.execute(query)
        return result.scalar_one() or 0

    async def get_log_by_id(self, log_id: int) -> Optional[AuditLog]:
        """Get audit log by ID."""
        query = select(AuditLog).where(AuditLog.id == log_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
