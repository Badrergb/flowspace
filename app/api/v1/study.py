from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List
import uuid
from datetime import datetime

from app.db.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.models.entities import FlashcardDeck, Flashcard, LiveFocusSession
from app.models.social import Friendship
from app.schemas.entities import (
    FlashcardDeckBase, FlashcardDeckResponse,
    FlashcardBase, FlashcardResponse,
    LiveFocusSessionBase, LiveFocusSessionResponse
)

router = APIRouter()

# --- Flashcards ---

@router.post("/flashcards/decks", response_model=FlashcardDeckResponse)
def create_deck(deck: FlashcardDeckBase, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_deck = FlashcardDeck(id=uuid.uuid4(), user_id=current_user.id, name=deck.name)
    db.add(new_deck)
    db.commit()
    db.refresh(new_deck)
    return new_deck

@router.get("/flashcards/decks", response_model=List[FlashcardDeckResponse])
def get_decks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(FlashcardDeck).filter(FlashcardDeck.user_id == current_user.id).all()

@router.post("/flashcards/cards", response_model=FlashcardResponse)
def create_card(card: FlashcardBase, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify deck ownership
    deck = db.query(FlashcardDeck).filter(FlashcardDeck.id == card.deck_id, FlashcardDeck.user_id == current_user.id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
        
    new_card = Flashcard(
        id=uuid.uuid4(),
        deck_id=card.deck_id,
        front_content=card.front_content,
        back_content=card.back_content,
        ease_factor=card.ease_factor,
        interval_days=card.interval_days,
        repetitions=card.repetitions,
        due_date=card.due_date
    )
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    return new_card

@router.get("/flashcards/decks/{deck_id}/cards", response_model=List[FlashcardResponse])
def get_cards(deck_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify deck ownership
    deck = db.query(FlashcardDeck).filter(FlashcardDeck.id == deck_id, FlashcardDeck.user_id == current_user.id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
        
    return db.query(Flashcard).filter(Flashcard.deck_id == deck_id).all()

# --- Group Focus ---

@router.post("/group/ping", response_model=LiveFocusSessionResponse)
def ping_focus_session(session_data: LiveFocusSessionBase, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(LiveFocusSession).filter(LiveFocusSession.user_id == current_user.id).first()
    if session:
        session.status = session_data.status
        session.current_activity = session_data.current_activity
        session.last_ping_at = datetime.utcnow()
    else:
        session = LiveFocusSession(
            id=uuid.uuid4(),
            user_id=current_user.id,
            status=session_data.status,
            current_activity=session_data.current_activity,
            started_at=datetime.utcnow(),
            last_ping_at=datetime.utcnow()
        )
        db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/group/friends", response_model=List[LiveFocusSessionResponse])
def get_friends_focus(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    friend_ids_query = db.query(Friendship.friend_id).filter(
        Friendship.user_id == current_user.id,
        Friendship.status == "accepted"
    )
    
    # Get active sessions
    sessions = db.query(LiveFocusSession).filter(
        LiveFocusSession.user_id.in_(friend_ids_query)
    ).all()
    
    return sessions
