"""Schemas for roles and permissions."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class PermissionResponse(BaseModel):
    """Permission response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    resource: str
    action: str
    description: Optional[str] = None
    created_at: datetime


class RoleResponse(BaseModel):
    """Role response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    permissions: List[PermissionResponse] = []


class RoleCreateRequest(BaseModel):
    """Request schema for creating a role."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True
    permission_ids: List[int] = []


class RoleUpdateRequest(BaseModel):
    """Request schema for updating a role."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[int]] = None


class PermissionCreateRequest(BaseModel):
    """Request schema for creating a permission."""
    name: str = Field(..., min_length=1, max_length=100)
    resource: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None