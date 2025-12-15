"""Audit log model for tracking system events."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.core.database import Base


class AuditLogAction(str, enum.Enum):
    """Types of audit log actions."""
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    UPDATE = "update"
    DELETE = "delete"
    CREATE = "create"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    BLOCK = "block"
    UNBLOCK = "unblock"
    SOFT_DELETE = "soft_delete"
    RESTORE = "restore"
    PASSWORD_CHANGE = "password_change"
    TOKEN_CREATE = "token_create"
    TOKEN_REVOKE = "token_revoke"
    SETTINGS_UPDATE = "settings_update"
    OTHER = "other"


class AuditLog(Base):
    """Audit log table for tracking all system events."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    action: Mapped[AuditLogAction] = mapped_column(
        SQLEnum(AuditLogAction),
        nullable=False,
        index=True
    )
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)  # 'user', 'admin', 'settings', etc.
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)  # User who performed the action
    admin_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)  # Admin who performed the action
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string for additional data
    success: Mapped[bool] = mapped_column(default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
