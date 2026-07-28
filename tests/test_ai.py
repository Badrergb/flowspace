import pytest

class MockMessage:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)

class MockCompletions:
    def create(self, **kwargs):
        # We look at response_format to mock properly
        if kwargs.get("response_format", {}).get("type") == "json_object":
            return type('obj', (object,), {'choices': [MockChoice('{"tx1": "Food"}')]})()
        return type('obj', (object,), {'choices': [MockChoice("Mock AI response")]})()

class MockChat:
    completions = MockCompletions()

class MockAIClient:
    chat = MockChat()

def test_categorize_transactions(auth_client, monkeypatch):
    monkeypatch.setattr("app.services.ai_service._get_client", lambda: MockAIClient())
    
    payload = {"transactions": ["tx1"]}
    res = auth_client.post("/api/v1/ai/categorize-transactions", json=payload)
    assert res.status_code == 200
    assert "tx1" in res.json()["categories"]

def test_weekly_review(auth_client, monkeypatch):
    monkeypatch.setattr("app.services.ai_service._get_client", lambda: MockAIClient())
    
    res = auth_client.get("/api/v1/ai/weekly-review")
    assert res.status_code == 200
    assert res.json()["review"] == "Mock AI response"

def test_chat(auth_client, monkeypatch):
    monkeypatch.setattr("app.services.ai_service._get_client", lambda: MockAIClient())
    
    payload = {"query": "Hello"}
    res = auth_client.post("/api/v1/ai/chat", json=payload)
    assert res.status_code == 200
    assert res.json()["response"] == "Mock AI response"

def test_ai_quota_exceeded(auth_client, test_db, test_user_and_token, monkeypatch):
    monkeypatch.setattr("app.services.ai_service._get_client", lambda: MockAIClient())
    user, _, _ = test_user_and_token
    from app.models.entities import UserSettings
    
    # Set quota to just below limit
    settings = test_db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if not settings:
        import uuid
        settings = UserSettings(id=uuid.uuid4(), user_id=user.id, version=1)
        test_db.add(settings)
    
    settings.ai_requests_used = 9
    test_db.commit()
    
    payload = {"query": "Hello"}
    # 10th request (should succeed)
    res = auth_client.post("/api/v1/ai/chat", json=payload)
    assert res.status_code == 200
    
    # 11th request (should fail)
    res = auth_client.post("/api/v1/ai/chat", json=payload)
    assert res.status_code == 429
    assert "limit reached" in res.json()["detail"].lower()
