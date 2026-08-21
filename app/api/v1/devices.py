from fastapi import APIRouter, Depends
from pydantic import BaseModel
from google.cloud.firestore_v1 import Client as FirestoreClient
from app.db.database import get_db
from app.api.deps import get_current_user

router = APIRouter()


class PushTokenUpdate(BaseModel):
    device_id: str
    push_token: str


@router.post("/push-token")
def update_push_token(
    payload: PushTokenUpdate,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Register or update a device's push notification token (FCM/APNs)."""
    uid = current_user["uid"]
    device_ref = (
        db.collection("users")
        .document(uid)
        .collection("devices")
        .document(payload.device_id)
    )
    device_doc = device_ref.get()

    if not device_doc.exists:
        # Auto-create the device document
        device_ref.set({
            "device_id": payload.device_id,
            "push_token": payload.push_token,
            "user_id": uid,
        })
    else:
        device_ref.update({"push_token": payload.push_token})

    return {"status": "success"}
