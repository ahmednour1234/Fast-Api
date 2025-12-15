"""Schemas for settings."""
from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field, ConfigDict, EmailStr


class SettingResponse(BaseModel):
    """Setting response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    key: str
    value: str
    description: Optional[str] = None
    is_public: bool
    is_encrypted: bool
    created_at: datetime
    updated_at: datetime


class SettingCreateRequest(BaseModel):
    """Request schema for creating/updating a setting."""
    key: str = Field(..., min_length=1, max_length=100)
    value: str
    description: Optional[str] = None
    is_public: bool = False
    is_encrypted: bool = False


class SettingUpdateRequest(BaseModel):
    """Request schema for updating a setting."""
    value: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    is_encrypted: Optional[bool] = None


class AppSettingsResponse(BaseModel):
    """Application settings response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    logo: Optional[str] = None
    logo_url: Optional[str] = None
    email: Optional[str] = None
    contact_info: Optional[str] = None
    app_name: Optional[str] = None
    url: Optional[str] = None


class AppSettingsUpdateRequest(BaseModel):
    """Request schema for updating application settings."""
    logo: Optional[str] = None  # Filename if uploaded
    email: Optional[EmailStr] = None
    contact_info: Optional[str] = None
    app_name: Optional[str] = None
    url: Optional[str] = None


class BulkSettingsRequest(BaseModel):
    """Request schema for bulk setting updates (key-value pairs)."""
    settings: Dict[str, str] = Field(..., description="Dictionary of key-value pairs")
    is_public: Optional[bool] = None
    description: Optional[str] = None
