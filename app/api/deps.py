from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from google.cloud.firestore_v1 import Client as FirestoreClient

from app.db.database import get_db

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: FirestoreClient = Depends(get_db),
) -> dict:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token.get("uid")
        email = decoded_token.get("email", "")
        name = decoded_token.get("name", email.split("@")[0] if email else "")
    except Exception as e:
        print(f"Auth error: {e}")
        raise credentials_exception

    if not uid:
        raise credentials_exception

    # Fetch or auto-create the user document in Firestore
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        user_data = {
            "uid": uid,
            "email": email,
            "full_name": name,
            "is_active": True,
        }
        user_ref.set(user_data)
    else:
        user_data = user_doc.to_dict()
        user_data["uid"] = uid

    if not user_data.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")

    return user_data
