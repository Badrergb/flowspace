from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
import uuid
from datetime import datetime
from google.cloud.firestore_v1 import Client as FirestoreClient
from google.cloud import firestore
from pydantic import BaseModel

from app.db.database import get_db
from app.api.deps import get_current_user

router = APIRouter()


class DeckCreate(BaseModel):
    name: str


class CardCreate(BaseModel):
    deck_id: str
    front_content: str
    back_content: str
    ease_factor: float = 2.5
    interval_days: int = 0
    repetitions: int = 0
    due_date: str | None = None


class LiveFocusSessionCreate(BaseModel):
    status: str = "studying"
    current_activity: str | None = None


class FocusInviteRequest(BaseModel):
    username: str


# --- Flashcards ---

@router.post("/flashcards/decks")
def create_deck(
    deck: DeckCreate,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    deck_id = str(uuid.uuid4())
    data = {
        "id": deck_id,
        "user_id": uid,
        "name": deck.name,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    db.collection("users").document(uid).collection("flashcard_decks").document(deck_id).set(data)
    data["created_at"] = None
    return data


@router.get("/flashcards/decks")
def get_decks(
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    docs = db.collection("users").document(uid).collection("flashcard_decks").stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]


@router.post("/flashcards/cards")
def create_card(
    card: CardCreate,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    deck_ref = db.collection("users").document(uid).collection("flashcard_decks").document(card.deck_id).get()
    if not deck_ref.exists:
        raise HTTPException(status_code=404, detail="Deck not found")

    card_id = str(uuid.uuid4())
    data = {
        "id": card_id,
        "deck_id": card.deck_id,
        "front_content": card.front_content,
        "back_content": card.back_content,
        "ease_factor": card.ease_factor,
        "interval_days": card.interval_days,
        "repetitions": card.repetitions,
        "due_date": card.due_date,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    db.collection("users").document(uid).collection("flashcards").document(card_id).set(data)
    data["created_at"] = None
    return data


@router.get("/flashcards/decks/{deck_id}/cards")
def get_cards(
    deck_id: str,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    deck_ref = db.collection("users").document(uid).collection("flashcard_decks").document(deck_id).get()
    if not deck_ref.exists:
        raise HTTPException(status_code=404, detail="Deck not found")

    docs = (
        db.collection("users")
        .document(uid)
        .collection("flashcards")
        .where("deck_id", "==", deck_id)
        .stream()
    )
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]


# --- Group Focus ---

@router.post("/group/ping")
def ping_focus_session(
    session_data: LiveFocusSessionCreate,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    ref = db.collection("live_focus_sessions").document(uid)
    data = {
        "uid": uid,
        "status": session_data.status,
        "current_activity": session_data.current_activity,
        "last_ping_at": firestore.SERVER_TIMESTAMP,
    }
    doc = ref.get()
    if not doc.exists:
        data["started_at"] = firestore.SERVER_TIMESTAMP
        ref.set(data)
    else:
        ref.update(data)
    return {"uid": uid, **session_data.dict()}


@router.get("/group/friends")
def get_friends_focus(
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    friend_docs = db.collection("friendships").where("user_id", "==", uid).where("status", "==", "accepted").stream()
    friend_ids = [doc.to_dict()["friend_id"] for doc in friend_docs]

    sessions = []
    for fid in friend_ids:
        session_doc = db.collection("live_focus_sessions").document(fid).get()
        if session_doc.exists:
            sessions.append(session_doc.to_dict())

    return sessions


@router.post("/group/invite")
def invite_focus_partner(
    req: FocusInviteRequest,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    results = db.collection("users").where("username", "==", req.username).limit(1).get()
    if not results:
        results = db.collection("users").where("email", "==", req.username).limit(1).get()
    if not results:
        raise HTTPException(status_code=404, detail="User not found")

    target = results[0].to_dict()
    if results[0].id == current_user["uid"]:
        raise HTTPException(status_code=400, detail="Cannot invite yourself")

    return {"message": f"Invite sent to {target.get('username') or target.get('email')}"}
