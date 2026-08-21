from sqlalchemy import Column, String, Integer, Text, Boolean
from app.db.database import Base
from app.models.base import UUIDMixin, TimeStampMixin

class Review(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "reviews"
    name = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5, validate range in the schema
    review_text = Column(Text, nullable=False)
    avatar_url = Column(String, nullable=True)  # R2 URL, optional
    is_approved = Column(Boolean, default=False, nullable=False)
