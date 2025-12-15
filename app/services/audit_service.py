"""Service for audit logging."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.repositories.audit_log_repo import AuditLogRepository
from app.models.audit_log import AuditLogAction


class AuditService:
    """Service for audit logging operations."""
    
    def __init__(self, db: AsyncSession):
        self.audit_repo = AuditLogRepository(db)

    def _get_client_info(self, request: Optional[Request]) -> tuple[Optional[str], Optional[str]]:
        """Extract IP address and user agent from request."""
        if not request:
            return None, None
        
        ip_address = None
        if request.client:
            ip_address = request.client.host
        
        user_agent = request.headers.get("user-agent")
        
        return ip_address, user_agent

    async def log_login(
        self,
        entity_type: str,  # 'user' or 'admin'
        entity_id: int,
        success: bool,
        request: Optional[Request] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Log a login attempt."""
        ip_address, user_agent = self._get_client_info(request)
        
        user_id = entity_id if entity_type == "user" else None
        admin_id = entity_id if entity_type == "admin" else None
        
        await self.audit_repo.create_log(
            action=AuditLogAction.LOGIN,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            admin_id=admin_id,
            ip_address=ip_address,
            user_agent=user_agent,
            description=f"{entity_type.capitalize()} login attempt",
            success=success,
            error_message=error_message
        )

    async def log_action(
        self,
        action: AuditLogAction,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        user_id: Optional[int] = None,
        admin_id: Optional[int] = None,
        description: Optional[str] = None,
        extra_data: Optional[dict] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        request: Optional[Request] = None
    ) -> None:
        """Log a general action."""
        import json
        
        ip_address, user_agent = self._get_client_info(request)
        
        extra_data_str = None
        if extra_data:
            extra_data_str = json.dumps(extra_data)
        
        await self.audit_repo.create_log(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            admin_id=admin_id,
            ip_address=ip_address,
            user_agent=user_agent,
            description=description,
            extra_data=extra_data_str,
            success=success,
            error_message=error_message
        )
