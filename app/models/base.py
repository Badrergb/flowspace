import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String, Boolean, text, BigInteger
from sqlalchemy.dialects.postgresql import UUID

class TimeStampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

class UUIDMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class VersionMixin:
    version = Column(BigInteger, default=0, nullable=False, index=True)
