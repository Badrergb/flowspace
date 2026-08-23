import os
os.environ["GROQ_API_KEY"] = "mock-key"
os.environ["FIREBASE_CREDENTIALS_JSON"] = "{}"

from app.db.database import get_db
from app.services.ai_service import chat_with_data

try:
    db_generator = get_db()
    db = next(db_generator)
    print(chat_with_data("hello", db, "test_user_id"))
except Exception as e:
    print("ERROR:", str(e))
