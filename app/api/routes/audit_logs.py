"""Routes for audit log management."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.core.resources import ResponseResource, PaginatedResponse
from app.repositories.audit_log_repo import AuditLogRepository
from app.models.audit_log import AuditLogAction
from app.schemas.audit_log import AuditLogResponse
from app.models.user import Admin

router = APIRouter()


@router.get("/logs", response_model=ResponseResource[PaginatedResponse[AuditLogResponse]])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    admin_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    success_only: Optional[bool] = Query(None),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs with filters (admin only)."""
    audit_repo = AuditLogRepository(db)
    
    # Convert action string to enum if provided
    action_enum = None
    if action:
        try:
            action_enum = AuditLogAction(action.lower())
        except ValueError:
            pass
    
    logs = await audit_repo.get_logs(
        skip=skip,
        limit=limit,
        action=action_enum,
        entity_type=entity_type,
        user_id=user_id,
        admin_id=admin_id,
        start_date=start_date,
        end_date=end_date,
        success_only=success_only
    )
    
    total = await audit_repo.count_logs(
        action=action_enum,
        entity_type=entity_type,
        user_id=user_id,
        admin_id=admin_id,
        start_date=start_date,
        end_date=end_date
    )
    
    log_responses = [AuditLogResponse.model_validate(log) for log in logs]
    
    return ResponseResource.success_response(
        data=PaginatedResponse(
            items=log_responses,
            total=total,
            page=skip // limit + 1,
            size=len(log_responses)
        ),
        message="Audit logs retrieved successfully"
    )


@router.get("/logs/{log_id}", response_model=ResponseResource[AuditLogResponse])
async def get_audit_log(
    log_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific audit log by ID (admin only)."""
    from app.core.exceptions import NotFoundError
    
    audit_repo = AuditLogRepository(db)
    log = await audit_repo.get_log_by_id(log_id)
    
    if not log:
        raise NotFoundError(resource="Audit log", resource_id=log_id)
    
    return ResponseResource.success_response(
        data=AuditLogResponse.model_validate(log),
        message="Audit log retrieved successfully"
    )
