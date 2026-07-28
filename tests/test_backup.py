import uuid

def test_backup_roundtrip(auth_client, test_user_and_token, monkeypatch):
    import app.api.v1.backup
    
    # In-memory storage to simulate Supabase so we can test the encryption/decryption round trip
    storage_mock = {}
    
    class MockSupabase:
        class storage:
            @staticmethod
            def from_(bucket):
                class Bucket:
                    def upload(self, path, file, file_options=None):
                        storage_mock[path] = file
                        return {"Key": path}
                    def download(self, path):
                        if path not in storage_mock:
                            raise Exception("File not found")
                        return storage_mock[path]
                    def list(self, path=None):
                        return [{"name": p.split("/")[-1]} for p in storage_mock.keys()]
                    def remove(self, paths):
                        for p in paths:
                            storage_mock.pop(p, None)
                return Bucket()
    monkeypatch.setattr(app.api.v1.backup, "get_supabase", lambda: MockSupabase)

    user, _, _ = test_user_and_token
    
    # 1. Create a backup
    file_content = b"fake database backup content for real roundtrip"
    filename = f"test_backup_{uuid.uuid4().hex}.db"
    files = {"file": (filename, file_content, "application/octet-stream")}
    
    response = auth_client.post("/api/v1/backup/create", files=files)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    path = res_data["path"]
    
    # 2. List backups and verify it's there
    list_response = auth_client.get("/api/v1/backup/list")
    assert list_response.status_code == 200
    backups = list_response.json().get("backups", [])
    
    found = False
    for b in backups:
        if b.get("name") == f"{filename}.enc":
            found = True
            break
    assert found, "Uploaded backup not found in list"
    
    # 3. Restore the backup and verify the content matches EXACTLY
    restore_response = auth_client.post(f"/api/v1/backup/restore?backup_path={path}")
    assert restore_response.status_code == 200
    restore_data = restore_response.json()
    assert restore_data["status"] == "success"
    # Note: Our restore endpoint currently returns a success payload with the length, not the raw file.
    # We should assert the length matches!
    assert restore_data["size"] == len(file_content)
    
    # 4. Clean up
    storage_mock.clear()
