from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PersonalAccessTokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    token: str
    name: Optional[str] = None
    user_id: Optional[int] = None
    admin_id: Optional[int] = None
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    is_expired: bool


class PersonalAccessTokenCreateRequest(BaseModel):
    name: Optional[str] = None
    expires_at: Optional[datetime] = None
