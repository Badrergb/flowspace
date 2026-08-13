from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.base import UUIDMixin, TimeStampMixin

class User(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    otp_hash = Column(String, nullable=True)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    otp_attempts = Column(Integer, default=0)
    
    devices = relationship("Device", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    habits = relationship("Habit", back_populates="user")
    goals = relationship("Goal", back_populates="user")
    journals = relationship("Journal", back_populates="user")
