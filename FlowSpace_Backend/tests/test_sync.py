import uuid
import time
from app.models.entities import Task
from app.models.sync import SyncOperation

def test_sync_upsert(auth_client, test_db, test_user_and_token):
    user, device, _ = test_user_and_token
    entity_id = str(uuid.uuid4())
    op_id = str(uuid.uuid4())
    
    # 1. Create a task via sync
    payload = {
        "device_id": str(device.id),
        "operations": [
            {
                "operation_id": op_id,
                "entity_type": "task",
                "entity_id": entity_id,
                "operation_type": "create",
                "payload": {
                    "title": "Test Sync Task",
                    "is_completed": False
                }
            }
        ]
    }
    
    response = auth_client.post("/api/v1/sync/upload", json=payload)
    assert response.status_code == 200
    assert response.json()["processed_count"] == 1
    
    # Verify in DB
    task = test_db.query(Task).filter(Task.id == entity_id).first()
    assert task is not None
    assert task.title == "Test Sync Task"
    
    # 2. Re-send create with same entity_id but different op_id (simulating a collision or retry with new op_id)
    # The upsert logic should handle this and treat it as an update if version is higher
    op_id_2 = str(uuid.uuid4())
    payload["operations"][0]["operation_id"] = op_id_2
    payload["operations"][0]["payload"]["title"] = "Upserted Title"
    
    time.sleep(0.01) # Ensure monotonic clock ticks
    response = auth_client.post("/api/v1/sync/upload", json=payload)
    assert response.status_code == 200
    
    test_db.refresh(task)
    assert task.title == "Upserted Title"

def test_lww_conflict_resolution(auth_client, test_db, test_user_and_token):
    user, device, _ = test_user_and_token
    entity_id = str(uuid.uuid4())
    
    # Setup initial row
    initial_version = int(time.time_ns())
    task = Task(id=entity_id, user_id=user.id, title="Initial", version=initial_version)
    test_db.add(task)
    test_db.commit()
    
    # Attempt to update with a lower version (should be ignored by LWW)
    # Wait, the server assigns the version during /upload, so it will ALWAYS be higher than the initial_version
    # if we just call the endpoint. 
    # To properly test LWW where an incoming operation has an older timestamp, we'd need the client to provide the timestamp, 
    # BUT our spec says "server-assigned timestamp". Wait, if the server assigns the timestamp at upload time, 
    # how does a conflict happen? 
    # If device A goes offline, edits at T1. Device B goes offline, edits at T2.
    # Device A comes online, uploads at T3 (gets version T3).
    # Device B comes online, uploads at T4 (gets version T4).
    # The server applies both in order of arrival, so T4 overwrites T3. This is true Last-Write(to server)-Wins.
    # The test should just verify that a normal update works, since the server dictates the timeline.
    
    op_id = str(uuid.uuid4())
    payload = {
        "device_id": str(device.id),
        "operations": [
            {
                "operation_id": op_id,
                "entity_type": "task",
                "entity_id": entity_id,
                "operation_type": "update",
                "payload": {
                    "title": "Updated Title"
                }
            }
        ]
    }
    
    response = auth_client.post("/api/v1/sync/upload", json=payload)
    assert response.status_code == 200
    
    test_db.refresh(task)
    assert task.title == "Updated Title"

def test_sync_soft_delete(auth_client, test_db, test_user_and_token):
    user, device, _ = test_user_and_token
    entity_id = str(uuid.uuid4())
    
    task = Task(id=entity_id, user_id=user.id, title="To Delete", version=int(time.time_ns()))
    test_db.add(task)
    test_db.commit()
    
    op_id = str(uuid.uuid4())
    payload = {
        "device_id": str(device.id),
        "operations": [
            {
                "operation_id": op_id,
                "entity_type": "task",
                "entity_id": entity_id,
                "operation_type": "delete",
                "payload": {}
            }
        ]
    }
    
    response = auth_client.post("/api/v1/sync/upload", json=payload)
    assert response.status_code == 200
    
    test_db.refresh(task)
    assert task.deleted_at is not None

def test_sync_download(auth_client, test_db, test_user_and_token):
    user, device, _ = test_user_and_token
    
    # Create another device to verify download filtering
    from app.models.device import Device
    device2 = Device(id=uuid.uuid4(), user_id=user.id, device_name="Device 2", device_type="test")
    test_db.add(device2)
    test_db.commit()
    
    # Create an operation as device 2
    op = SyncOperation(
        id=uuid.uuid4(),
        user_id=user.id,
        device_id=device2.id,
        entity_type="task",
        entity_id=uuid.uuid4(),
        operation_type="create",
        payload={"title": "From Device 2"},
        version=int(time.time_ns())
    )
    test_db.add(op)
    test_db.commit()
    
    # Download as device 1
    payload = {
        "device_id": str(device.id),
        "last_sync_version": 0
    }
    response = auth_client.post("/api/v1/sync/download", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["operations"]) >= 1
    # Check that device 2's operation is included
    op_ids = [o["id"] for o in data["operations"]]
    assert str(op.id) in op_ids
    
    # Teardown for this specific test
    test_db.delete(op)
    test_db.delete(device2)
    test_db.commit()

def test_sync_intra_batch_updates(auth_client, test_db, test_user_and_token):
    user, device, _ = test_user_and_token
    entity_id = str(uuid.uuid4())
    
    # Send a create and an update for the same entity in the same batch
    op1_id = str(uuid.uuid4())
    op2_id = str(uuid.uuid4())
    payload = {
        "device_id": str(device.id),
        "operations": [
            {
                "operation_id": op1_id,
                "entity_type": "task",
                "entity_id": entity_id,
                "operation_type": "create",
                "payload": {
                    "title": "Initial Title",
                    "is_completed": False
                }
            },
            {
                "operation_id": op2_id,
                "entity_type": "task",
                "entity_id": entity_id,
                "operation_type": "update",
                "payload": {
                    "is_completed": True
                }
            }
        ]
    }
    
    response = auth_client.post("/api/v1/sync/upload", json=payload)
    assert response.status_code == 200
    
    test_db.expire_all()
    task = test_db.query(Task).filter(Task.id == entity_id).first()
    assert task is not None
    assert task.title == "Initial Title"
    assert task.is_completed is True # The second operation should have applied

