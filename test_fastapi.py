from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.api.v1.ai import router
from app.api.deps import get_current_user
from app.db.database import get_db

app = FastAPI()
app.include_router(router, prefix="/ai")

def override_get_current_user():
    return {"uid": "test_uid"}

class MockDB:
    class Collection:
        def document(self, doc_id):
            return self
        def collection(self, col_id):
            return self
        def get(self):
            class Doc:
                exists = False
            return Doc()
        def set(self, data, merge=False):
            pass
    def collection(self, name):
        return self.Collection()

def override_get_db():
    yield MockDB()

app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)
response = client.post("/ai/chat", json={"query": "send some song suggestions"})
print("STATUS CODE:", response.status_code)
print("JSON:", response.json())
