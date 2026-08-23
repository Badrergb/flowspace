from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.api.v1.ai import router
from app.api.deps import get_current_user
from app.db.database import get_db

app = FastAPI()
app.include_router(router, prefix="/ai")

# Don't mock get_current_user this time to see if it crashes
def override_get_db():
    yield None

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)
response = client.post("/ai/chat", headers={"Authorization": "Bearer mock-token"}, json={"query": "send some song suggestions"})
print("STATUS CODE:", response.status_code)
print("JSON:", response.json())
