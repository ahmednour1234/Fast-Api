"""Schemas for audit logs."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.models.audit_log import AuditLogAction


class AuditLogResponse(BaseModel):
    """Audit log response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    action: AuditLogAction
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    user_id: Optional[int] = None
    admin_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    description: Optional[str] = None
    extra_data: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    created_at: datetime
