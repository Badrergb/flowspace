import pytest
from fastapi.testclient import TestClient
import uuid

class MockStorageClient:
    def upload(self, path, file, file_options=None):
        return {"Key": path}
        
    def get_public_url(self, path):
        return f"https://mock-supabase.com/storage/v1/object/public/media/{path}"
        
    def remove(self, paths):
        return [{"name": paths[0]}]

class MockSupabase:
    class Storage:
        def from_(self, bucket):
            return MockStorageClient()
            
    storage = Storage()

def test_upload_media(auth_client, monkeypatch):
    monkeypatch.setattr("app.api.v1.media.get_supabase", lambda: MockSupabase())
    
    # Create a dummy file
    files = {'file': ('test.jpg', b'dummy content', 'image/jpeg')}
    
    res = auth_client.post("/api/v1/media/upload", files=files)
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert "url" in res.json()
    assert "test.jpg" not in res.json()["url"] # UUID renaming

def test_delete_media(auth_client, test_user_and_token, monkeypatch):
    user, _, _ = test_user_and_token
    monkeypatch.setattr("app.api.v1.media.get_supabase", lambda: MockSupabase())
    
    # Valid delete (owns the path)
    valid_path = f"{user.id}/dummy.jpg"
    res = auth_client.delete(f"/api/v1/media/{valid_path}")
    assert res.status_code == 200
    
    # Invalid delete (wrong user)
    invalid_path = f"{uuid.uuid4()}/dummy.jpg"
    res2 = auth_client.delete(f"/api/v1/media/{invalid_path}")
    assert res2.status_code == 403
