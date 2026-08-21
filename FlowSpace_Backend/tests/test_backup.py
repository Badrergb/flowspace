def test_backup_create(auth_client, monkeypatch):
    import app.api.v1.backup
    
    class MockSupabase:
        class storage:
            @staticmethod
            def from_(bucket):
                class Bucket:
                    def upload(self, file, path, file_options):
                        pass
                return Bucket()
    monkeypatch.setattr(app.api.v1.backup, "get_supabase", lambda: MockSupabase)

    file_content = b"fake database backup content"
    files = {"file": ("backup.db", file_content, "application/octet-stream")}
    
    response = auth_client.post("/api/v1/backup/create", files=files)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    # This just ensures the endpoint doesn't crash during the fernet encryption phase
