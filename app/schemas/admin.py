from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class AdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    avatar: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime


class AdminCreateRequest(BaseModel):
    username: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    is_active: bool = True


class AdminUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
