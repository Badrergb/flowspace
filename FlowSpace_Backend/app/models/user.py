from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.base import UUIDMixin, TimeStampMixin

class User(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    devices = relationship("Device", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    habits = relationship("Habit", back_populates="user")
    goals = relationship("Goal", back_populates="user")
    journals = relationship("Journal", back_populates="user")
