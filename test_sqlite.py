from sqlalchemy import Column, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class TestModel(Base):
    __tablename__ = "test"
    id = Column(UUID(as_uuid=True), primary_key=True)

engine = create_engine("sqlite:///./test.db")
try:
    Base.metadata.create_all(engine)
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
