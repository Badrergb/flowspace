import pytest
from app.models.device import Device
import uuid

def test_update_push_token(auth_client, test_db, test_user_and_token):
    user, device, token = test_user_and_token
    
    payload = {
        "device_id": str(device.id),
        "push_token": "mock-fcm-token-123"
    }
    
    res = auth_client.post("/api/v1/devices/push-token", json=payload)
    assert res.status_code == 200
    
    test_db.refresh(device)
    assert device.push_token == "mock-fcm-token-123"
    
def test_update_push_token_wrong_device(auth_client):
    payload = {
        "device_id": str(uuid.uuid4()),
        "push_token": "mock-fcm-token-123"
    }
    
    res = auth_client.post("/api/v1/devices/push-token", json=payload)
    assert res.status_code == 404
