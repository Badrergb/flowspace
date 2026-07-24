from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class ReviewBase(BaseModel):
    name: str
    rating: int = Field(ge=1, le=5)
    review_text: str
    avatar_url: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewResponse(ReviewBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
