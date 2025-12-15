"""Schemas for collections."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CollectionResponse(BaseModel):
    """Collection response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    image: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool
    sort_order: int
    created_by_admin_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class CollectionCreateRequest(BaseModel):
    """Request schema for creating a collection."""
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class CollectionUpdateRequest(BaseModel):
    """Request schema for updating a collection."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None