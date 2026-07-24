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
