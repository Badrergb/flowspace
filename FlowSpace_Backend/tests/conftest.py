import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from app.main import app
from app.db.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.device import Device
from app.core.security import get_password_hash, create_access_token
from datetime import timedelta

# We will use the direct URL for testing to avoid pgbouncer issues in short-lived tests
engine = create_engine(settings.DIRECT_URL, pool_pre_ping=True)

from app.db.database import Base
# ensure all models are imported so they are registered with Base
from app.models.user import User
from app.models.device import Device
from app.models.sync import SyncOperation, DeviceSyncState
from app.models.entities import Task, Habit, HabitLog, Journal, Goal, GoalProgress, Note, CalendarEvent, WaterLog, WorkoutSession, WorkoutSet, Transaction, Category
from app.models.social import Friendship, FeedPost, FeedComment, FeedLike, ChatThread, ChatMessage
Base.metadata.create_all(engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def test_db():
    db = TestingSessionLocal()
    yield db
    db.close()

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="session")
def test_user_and_token(test_db):
    # Setup test user
    email = f"test_{uuid.uuid4()}@example.com"
    password = "testpassword123"
    
    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=get_password_hash(password),
        full_name="Test User",
        is_active=True
    )
    test_db.add(user)
    
    device = Device(
        id=uuid.uuid4(),
        user_id=user.id,
        device_name="Test Device",
        device_type="test"
    )
    test_db.add(device)
    test_db.commit()
    
    access_token = create_access_token(
        data={"email": user.email, "sub": str(user.id)}, 
        expires_delta=timedelta(minutes=30)
    )
    
    yield user, device, access_token
    
    # Teardown
    from app.models.entities import Task
    from app.models.sync import SyncOperation, DeviceSyncState
    test_db.query(Task).filter(Task.user_id == user.id).delete()
    test_db.query(SyncOperation).filter(SyncOperation.user_id == user.id).delete()
    test_db.query(DeviceSyncState).filter(DeviceSyncState.device_id == device.id).delete()
    test_db.query(Device).filter(Device.user_id == user.id).delete()
    test_db.delete(user)
    test_db.commit()

@pytest.fixture(scope="function")
def auth_client(client, test_user_and_token):
    _, _, token = test_user_and_token
    client.headers["Authorization"] = f"Bearer {token}"
    return client
