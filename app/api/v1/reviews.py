from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import uuid

from app.db.database import get_db
from app.models.reviews import Review
from app.schemas.reviews import ReviewResponse
from app.core.rate_limit import limiter
from app.services.storage_service import upload_file_to_supabase
from app.core.errors import safe_error_message
from app.core.config import settings

router = APIRouter()

@router.post("", response_model=ReviewResponse)
@limiter.limit("3/hour")
async def create_review(
    request: Request,
    name: str = Form(...),
    rating: int = Form(...),
    review_text: str = Form(...),
    avatar: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    if not (1 <= rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    avatar_url = None
    if avatar:
        # Upload avatar to R2
        file_bytes = await avatar.read()
        file_ext = avatar.filename.split('.')[-1] if avatar.filename else 'png'
        file_path = f"reviews/avatars/{uuid.uuid4()}.{file_ext}"
        try:
            # Upload to the flowspace-media bucket
            avatar_url = upload_file_to_supabase("flowspace-media", file_path, file_bytes, avatar.content_type or "image/png")
        except Exception as e:
            safe_msg = safe_error_message(e, fallback="Failed to upload avatar")
            raise HTTPException(status_code=500, detail=safe_msg)

    review = Review(
        id=uuid.uuid4(),
        name=name,
        rating=rating,
        review_text=review_text,
        avatar_url=avatar_url,
        is_approved=False
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

@router.get("", response_model=List[ReviewResponse])
def get_reviews(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000), 
    db: Session = Depends(get_db)
):
    reviews = db.query(Review).filter(Review.is_approved == True).order_by(desc(Review.created_at)).offset(skip).limit(limit).all()
    return reviews
