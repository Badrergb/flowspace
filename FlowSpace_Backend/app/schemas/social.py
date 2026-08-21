from typing import Optional, List
from pydantic import BaseModel, UUID4
from datetime import datetime

class FriendshipBase(BaseModel):
    friend_id: UUID4

class FriendshipResponse(FriendshipBase):
    id: UUID4
    user_id: UUID4
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class FeedPostBase(BaseModel):
    content: str
    visibility: Optional[str] = "friends"

class FeedPostResponse(FeedPostBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class FeedCommentBase(BaseModel):
    post_id: UUID4
    content: str

class FeedCommentResponse(FeedCommentBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class FeedLikeBase(BaseModel):
    post_id: UUID4

class FeedLikeResponse(FeedLikeBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    model_config = {"from_attributes": True}

class ChatMessageBase(BaseModel):
    content: str

class ChatMessageResponse(ChatMessageBase):
    id: UUID4
    thread_id: UUID4
    sender_id: UUID4
    created_at: datetime
    model_config = {"from_attributes": True}

class ChatThreadResponse(BaseModel):
    id: UUID4
    created_at: datetime
    model_config = {"from_attributes": True}
