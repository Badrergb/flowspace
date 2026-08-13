from typing import Optional, Any
from pydantic import BaseModel, UUID4
from datetime import datetime

class UserBase(BaseModel):
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID4
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

class DeviceBase(BaseModel):
    device_name: str
    device_type: str
    fcm_token: Optional[str] = None

class DeviceCreate(DeviceBase):
    pass

class DeviceResponse(DeviceBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    
    model_config = {"from_attributes": True}
