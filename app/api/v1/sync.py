from typing import Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
from google.cloud.firestore_v1 import Client as FirestoreClient

from app.db.database import get_db
from app.api.deps import get_current_user
from app.core.rate_limit import limiter

router = APIRouter()


class SyncOperation(BaseModel):
    collection: str
    document_id: str
    data: dict
    operation: str  # "set", "update", "delete"
    timestamp: str


class SyncUploadRequest(BaseModel):
    device_id: str
    operations: List[SyncOperation]


class SyncDownloadRequest(BaseModel):
    device_id: str
    last_sync_version: Optional[str] = None


@router.post("/upload")
@limiter.limit("30/minute")
def sync_upload(
    request: Request,
    payload: SyncUploadRequest,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Receives local operations from a device and applies them to Firestore.
    """
    uid = current_user["uid"]
    applied = 0

    for op in payload.operations:
        ref = db.collection("users").document(uid).collection(op.collection).document(op.document_id)
        try:
            if op.operation == "delete":
                ref.delete()
            elif op.operation == "set":
                ref.set(op.data)
            elif op.operation == "update":
                ref.set(op.data, merge=True)
            applied += 1
        except Exception as e:
            print(f"Failed to apply op {op.document_id}: {e}")

    return {"applied": applied, "total": len(payload.operations)}


@router.post("/download")
@limiter.limit("30/minute")
def sync_download(
    request: Request,
    payload: SyncDownloadRequest,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Returns all user data for full re-sync. Firestore handles real-time sync natively on the client.
    """
    uid = current_user["uid"]
    collections = ["tasks", "habits", "goals", "notes", "journals",
                   "calendar_events", "transactions", "categories"]

    result = {}
    for col in collections:
        docs = db.collection("users").document(uid).collection(col).stream()
        result[col] = [{**doc.to_dict(), "id": doc.id} for doc in docs]

    return result
