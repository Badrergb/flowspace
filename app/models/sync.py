from sqlalchemy import Column, String, Integer, ForeignKey, JSON, DateTime, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base
from app.models.base import UUIDMixin, TimeStampMixin
from datetime import datetime

class SyncOperation(Base, UUIDMixin, TimeStampMixin):
    """
    Stores operations uploaded by devices.
    """
    __tablename__ = "sync_operations"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    
    entity_type = Column(String, nullable=False, index=True) # e.g., 'task', 'habit'
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    operation_type = Column(String, nullable=False) # 'create', 'update', 'delete'
    
    payload = Column(JSON, nullable=True) # the actual data changed
    
    # Server assigned version/timestamp (used for LWW and download ordering)
    version = Column(BigInteger, nullable=False, index=True)
    
    # User relationship
    user = relationship("User")
    device = relationship("Device")


class DeviceSyncState(Base, UUIDMixin):
    """
    Tracks the highest version a particular device has downloaded.
    """
    __tablename__ = "device_sync_states"

    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, unique=True)
    last_sync_version = Column(BigInteger, default=0, nullable=False)
    last_sync_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    device = relationship("Device", back_populates="sync_states")
