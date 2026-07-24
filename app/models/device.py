from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base
from app.models.base import UUIDMixin, TimeStampMixin

class Device(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "devices"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    device_name = Column(String, nullable=False)
    device_type = Column(String, nullable=False) # e.g., 'ios', 'android', 'web'
    fcm_token = Column(String, nullable=True) 
    last_sync_time = Column(DateTime(timezone=True))
    push_token = Column(String, nullable=True) # FCM or APNs token for push notifications
    
    user = relationship("User", back_populates="devices")
    sync_states = relationship("DeviceSyncState", back_populates="device", cascade="all, delete-orphan")
