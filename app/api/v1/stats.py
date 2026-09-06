from fastapi import APIRouter, Depends
from google.cloud.firestore_v1 import Client as FirestoreClient
from google.cloud import firestore

from app.db.database import get_db

router = APIRouter()

@router.get("/downloads")
def get_downloads(db: FirestoreClient = Depends(get_db)):
    try:
        doc_ref = db.collection("stats").document("app_stats")
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return {"count": data.get("download_count", 0)}
        return {"count": 0}
    except Exception as e:
        return {"count": 0, "error": str(e)}

@router.post("/downloads")
def increment_downloads(db: FirestoreClient = Depends(get_db)):
    try:
        doc_ref = db.collection("stats").document("app_stats")
        doc_ref.set({"download_count": firestore.Increment(1)}, merge=True)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
