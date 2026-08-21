import pytest
from app.models.entities import Task
from app.models.user import User

def test_export_data(auth_client, test_db, test_user_and_token):
    user, device, _ = test_user_and_token
    
    # Create a task for export test
    task = Task(title="Test Export Task", user_id=user.id)
    test_db.add(task)
    test_db.commit()
    
    res = auth_client.get("/api/v1/user/export")
    assert res.status_code == 200
    data = res.json()
    assert "user" in data
    assert data["user"]["email"] == user.email
    assert "tasks" in data
    assert len(data["tasks"]) >= 1
    assert data["tasks"][0]["title"] == "Test Export Task"


import uuid
from app.core.security import get_password_hash, create_access_token
from datetime import timedelta

def test_delete_account(client, test_db):
    # Setup test user directly
    email = f"delete_test_{uuid.uuid4()}@example.com"
    user_id_obj = uuid.uuid4()
    user = User(
        id=user_id_obj,
        email=email,
        hashed_password=get_password_hash("password"),
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    
    access_token = create_access_token(
        data={"email": user.email, "sub": str(user.id)}, 
        expires_delta=timedelta(minutes=30)
    )
    
    client.headers["Authorization"] = f"Bearer {access_token}"
    
    res = client.delete("/api/v1/user/account")
    assert res.status_code == 200
    assert res.json()["message"] == "Account successfully purged"
    
    # Verify user is deleted by ID
    deleted_user = test_db.query(User).filter(User.id == user_id_obj).first()
    assert deleted_user is None
