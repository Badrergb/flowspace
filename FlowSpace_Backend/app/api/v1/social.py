from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import List
import uuid

from app.db.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.models.social import Friendship, FeedPost, FeedComment, FeedLike, ChatThread, ChatMessage, chat_participants
from app.schemas.social import (
    FriendshipBase, FriendshipResponse,
    FeedPostBase, FeedPostResponse,
    FeedCommentBase, FeedCommentResponse,
    FeedLikeBase, FeedLikeResponse,
    ChatMessageBase, ChatMessageResponse,
    ChatThreadResponse
)

router = APIRouter()

# --- Friends ---

@router.post("/friends/request", response_model=FriendshipResponse)
def send_friend_request(req: FriendshipBase, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if str(req.friend_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")
    
    existing = db.query(Friendship).filter(
        and_(Friendship.user_id == current_user.id, Friendship.friend_id == req.friend_id)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Friend request already sent")
        
    friendship = Friendship(id=uuid.uuid4(), user_id=current_user.id, friend_id=req.friend_id, status="pending")
    db.add(friendship)
    db.commit()
    db.refresh(friendship)
    return friendship

@router.post("/friends/accept", response_model=FriendshipResponse)
def accept_friend_request(req: FriendshipBase, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Look for a pending request where we are the friend_id
    existing = db.query(Friendship).filter(
        and_(Friendship.user_id == req.friend_id, Friendship.friend_id == current_user.id, Friendship.status == "pending")
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Friend request not found")
        
    existing.status = "accepted"
    
    # Create reciprocal friendship for easier querying
    reciprocal = Friendship(id=uuid.uuid4(), user_id=current_user.id, friend_id=req.friend_id, status="accepted")
    db.add(reciprocal)
    db.commit()
    db.refresh(existing)
    return existing

@router.get("/friends", response_model=List[FriendshipResponse])
def get_friends(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Friendship).filter(Friendship.user_id == current_user.id).all()

# --- Feed ---

@router.post("/feed", response_model=FeedPostResponse)
def create_feed_post(post: FeedPostBase, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_post = FeedPost(id=uuid.uuid4(), user_id=current_user.id, content=post.content, visibility=post.visibility)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@router.get("/feed", response_model=List[FeedPostResponse])
def get_feed(skip: int = Query(0), limit: int = Query(50), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Get friend IDs
    friend_ids_query = db.query(Friendship.friend_id).filter(
        Friendship.user_id == current_user.id, 
        Friendship.status == "accepted"
    )
    
    posts = db.query(FeedPost).filter(
        or_(
            FeedPost.user_id == current_user.id,
            and_(FeedPost.user_id.in_(friend_ids_query), FeedPost.visibility != "private")
        )
    ).order_by(desc(FeedPost.created_at)).offset(skip).limit(limit).all()
    
    return posts

# --- Chat ---

@router.post("/chat/{thread_id}/messages", response_model=ChatMessageResponse)
def send_message(thread_id: uuid.UUID, msg: ChatMessageBase, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # For MVP, assume thread exists. Ideally, check if current_user is in thread.
    thread = db.query(ChatThread).filter(ChatThread.id == thread_id).first()
    if not thread:
        # Create thread implicitly if it doesn't exist
        thread = ChatThread(id=thread_id)
        db.add(thread)
        db.commit()
        
    new_msg = ChatMessage(id=uuid.uuid4(), thread_id=thread_id, sender_id=current_user.id, content=msg.content)
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg

@router.get("/chat/{thread_id}/messages", response_model=List[ChatMessageResponse])
def get_messages(thread_id: uuid.UUID, skip: int = Query(0), limit: int = Query(50), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ChatMessage).filter(ChatMessage.thread_id == thread_id).order_by(desc(ChatMessage.created_at)).offset(skip).limit(limit).all()
