from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from typing import List, Optional
import uuid
from google.cloud.firestore_v1 import Client as FirestoreClient
from google.cloud import firestore

from app.db.database import get_db
from app.core.rate_limit import limiter
from app.core.errors import safe_error_message

router = APIRouter()


@router.post("")
@limiter.limit("3/hour")
async def create_review(
    request: Request,
    name: str = Form(...),
    rating: int = Form(...),
    review_text: str = Form(...),
    avatar: Optional[UploadFile] = File(None),
    db: FirestoreClient = Depends(get_db),
):
    if not (1 <= rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    avatar_url = None

    review_id = str(uuid.uuid4())
    review_data = {
        "id": review_id,
        "name": name,
        "rating": rating,
        "review_text": review_text,
        "avatar_url": avatar_url,
        "is_approved": False,
        "created_at": firestore.SERVER_TIMESTAMP,
    }

    db.collection("reviews").document(review_id).set(review_data)
    review_data["created_at"] = None  # SERVER_TIMESTAMP not serializable yet
    return review_data


@router.get("")
def get_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: FirestoreClient = Depends(get_db),
):
    docs = (
        db.collection("reviews")
        .where("is_approved", "==", True)
        .order_by("created_at", direction="DESCENDING")
        .limit(limit + skip)
        .stream()
    )
    results = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        if d.get("created_at") and hasattr(d["created_at"], "isoformat"):
            d["created_at"] = d["created_at"].isoformat()
        results.append(d)

    return results[skip:skip + limit]
