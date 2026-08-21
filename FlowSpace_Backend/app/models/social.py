from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base
from app.models.base import UUIDMixin, TimeStampMixin
from sqlalchemy.sql import func
import uuid

class Friendship(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "friendships"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    friend_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String, default="pending") # pending, accepted, rejected

class FeedPost(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "feed_posts"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    visibility = Column(String, default="friends") # friends, public, private
    
    comments = relationship("FeedComment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("FeedLike", back_populates="post", cascade="all, delete-orphan")

class FeedComment(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "feed_comments"
    post_id = Column(UUID(as_uuid=True), ForeignKey("feed_posts.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    post = relationship("FeedPost", back_populates="comments")

class FeedLike(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "feed_likes"
    post_id = Column(UUID(as_uuid=True), ForeignKey("feed_posts.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    post = relationship("FeedPost", back_populates="likes")

# Association table for chat thread participants
chat_participants = Table(
    "chat_participants",
    Base.metadata,
    Column("thread_id", UUID(as_uuid=True), ForeignKey("chat_threads.id"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
)

class ChatThread(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "chat_threads"
    
    # Participants can be loaded through relationship
    # messages relationship
    messages = relationship("ChatMessage", back_populates="thread", cascade="all, delete-orphan")

class ChatMessage(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "chat_messages"
    thread_id = Column(UUID(as_uuid=True), ForeignKey("chat_threads.id"), nullable=False, index=True)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    thread = relationship("ChatThread", back_populates="messages")
