from fastapi import APIRouter, Depends
from google.cloud.firestore_v1 import Client as FirestoreClient
from app.db.database import get_db
from app.api.deps import get_current_user
from app.schemas.ai import CategorizeRequest, CategorizeResponse, ChatRequest, ChatResponse, WeeklyReviewResponse
from app.services import ai_service

router = APIRouter()

@router.post("/categorize-transactions", response_model=CategorizeResponse)
def categorize_transactions(
    payload: CategorizeRequest,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    categories = ai_service.categorize_transactions(payload.transactions, db, current_user["uid"])
    return CategorizeResponse(categories=categories)

@router.get("/weekly-review", response_model=WeeklyReviewResponse)
def get_weekly_review(
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    review = ai_service.generate_weekly_review(db, current_user["uid"])
    return WeeklyReviewResponse(review=review)

@router.post("/chat", response_model=ChatResponse)
def chat_with_data(
    payload: ChatRequest,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    response = ai_service.chat_with_data(payload.query, db, current_user["uid"])
    return ChatResponse(response=response)
