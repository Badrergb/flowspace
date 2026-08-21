import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

def test_friend_request(auth_client, test_db, test_user_and_token):
    user, _, _ = test_user_and_token
    friend_id = str(uuid.uuid4())
    
    # Send request
    res = auth_client.post("/api/v1/social/friends/request", json={"friend_id": friend_id})
    assert res.status_code == 200
    assert res.json()["status"] == "pending"
    
    # Send again should fail
    res2 = auth_client.post("/api/v1/social/friends/request", json={"friend_id": friend_id})
    assert res2.status_code == 400

def test_feed_post(auth_client):
    res = auth_client.post("/api/v1/social/feed", json={"content": "Hello world", "visibility": "public"})
    assert res.status_code == 200
    assert res.json()["content"] == "Hello world"
    
    res2 = auth_client.get("/api/v1/social/feed")
    assert res2.status_code == 200
    assert len(res2.json()) >= 1

def test_chat_messages(auth_client):
    thread_id = str(uuid.uuid4())
    res = auth_client.post(f"/api/v1/social/chat/{thread_id}/messages", json={"content": "Hi"})
    assert res.status_code == 200
    assert res.json()["content"] == "Hi"
    
    res2 = auth_client.get(f"/api/v1/social/chat/{thread_id}/messages")
    assert res2.status_code == 200
    assert len(res2.json()) == 1
    assert res2.json()[0]["content"] == "Hi"
