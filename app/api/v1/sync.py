from typing import Optional, List
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from google.cloud.firestore_v1 import Client as FirestoreClient

from app.db.database import get_db
from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.services.email_service import send_streak_milestone_email, MILESTONE_STREAKS

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
    Also detects habit streak milestones and sends a celebration email.
    """
    uid = current_user["uid"]
    
    if len(payload.operations) > 500:
        raise HTTPException(status_code=400, detail="Too many operations in a single sync request (max 500).")

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

            # ── Streak milestone detection ──────────────────────────────
            # Sends a celebration email when a habit hits 7, 14, 21, 30,
            # 60, 90, 180, or 365 days. Deduped via milestones_sent list.
            if op.collection == "habits" and op.operation in ("set", "update"):
                streak = op.data.get("current_streak")
                if streak and isinstance(streak, int) and streak in MILESTONE_STREAKS:
                    milestones_sent = current_user.get("milestones_sent", [])
                    milestone_key = f"{op.document_id}_{streak}"
                    if milestone_key not in milestones_sent:
                        email = current_user.get("email")
                        full_name = current_user.get("full_name", "") or ""
                        first_name = full_name.split()[0] if full_name else "there"
                        if email:
                            send_streak_milestone_email(
                                to_email=email,
                                first_name=first_name,
                                streak=streak,
                            )
                            milestones_sent.append(milestone_key)
                            db.collection("users").document(uid).set(
                                {"milestones_sent": milestones_sent}, merge=True
                            )
            # ────────────────────────────────────────────────────────────

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
