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


class FriendRequestByUsername(BaseModel):
    username: str


class FriendRequestById(BaseModel):
    friend_id: str


class FeedPostCreate(BaseModel):
    content: str
    visibility: str = "public"


class ChatMessageCreate(BaseModel):
    content: str


def _thread_id(uid1: str, uid2: str) -> str:
    return "__".join(sorted([uid1, uid2]))


# --- Friends ---

@router.post("/friends/request/by-username")
def send_friend_request_by_username(
    req: FriendRequestByUsername,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    # Find target user by username field in Firestore
    results = db.collection("users").where("username", "==", req.username).limit(1).get()
    if not results:
        results = db.collection("users").where("email", "==", req.username).limit(1).get()
    if not results:
        results = db.collection("users").where("full_name", "==", req.username).limit(1).get()
    if not results:
        raise HTTPException(status_code=404, detail="User not found")

    target_doc = results[0]
    target_uid = target_doc.id

    if target_uid == uid:
        raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")

    friendship_id = f"{uid}_{target_uid}"
    existing = db.collection("friendships").document(friendship_id).get()
    if existing.exists:
        raise HTTPException(status_code=400, detail="Friend request already sent")

    db.collection("friendships").document(friendship_id).set({
        "id": friendship_id,
        "user_id": uid,
        "friend_id": target_uid,
        "status": "pending",
        "created_at": firestore.SERVER_TIMESTAMP,
    })
    return {"id": friendship_id, "status": "pending"}


@router.get("/friends/requests/pending")
def get_pending_requests(
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    
    # Incoming pending requests
    incoming_docs = db.collection("friendships").where("friend_id", "==", uid).where("status", "==", "pending").stream()
    
    results = []
    for doc in incoming_docs:
        d = doc.to_dict()
        sender_id = d.get("user_id")
        sender_name = "Unknown"
        if sender_id:
            sender_doc = db.collection("users").document(sender_id).get()
            if sender_doc.exists:
                sender_data = sender_doc.to_dict()
                sender_name = sender_data.get("full_name") or sender_data.get("username") or "Unknown"
                
        results.append({
            "id": doc.id,
            "sender_name": sender_name,
            "sender_id": sender_id,
            "created_at": d.get("created_at").isoformat() if hasattr(d.get("created_at"), "isoformat") else None
        })
    return results

@router.post("/friends/request/{id}/accept")
def accept_friend_request_by_id(
    id: str,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    ref = db.collection("friendships").document(id)
    doc = ref.get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Friend request not found")
        
    data = doc.to_dict()
    if data.get("friend_id") != uid:
        raise HTTPException(status_code=403, detail="Not authorized to accept this request")
        
    if data.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request is not pending")
        
    ref.update({"status": "accepted"})
    
    # Create reciprocal
    sender_id = data.get("user_id")
    reciprocal_id = f"{uid}_{sender_id}"
    db.collection("friendships").document(reciprocal_id).set({
        "id": reciprocal_id,
        "user_id": uid,
        "friend_id": sender_id,
        "status": "accepted",
        "created_at": firestore.SERVER_TIMESTAMP,
    })
    return {"message": "Friend request accepted"}

@router.post("/friends/request/{id}/decline")
def decline_friend_request_by_id(
    id: str,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    ref = db.collection("friendships").document(id)
    doc = ref.get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Friend request not found")
        
    data = doc.to_dict()
    if data.get("friend_id") != uid:
        raise HTTPException(status_code=403, detail="Not authorized to decline this request")
        
    if data.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request is not pending")
        
    ref.delete()
    return {"message": "Friend request declined"}


@router.get("/friends")
def get_friends(
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    
    # Fetch outgoing requests (where current user is the sender)
    outgoing_docs = db.collection("friendships").where("user_id", "==", uid).stream()
    
    # Fetch incoming requests (where current user is the receiver)
    incoming_docs = db.collection("friendships").where("friend_id", "==", uid).stream()
    
    friends_list = []
    seen_accepted = set()
    
    # Add outgoing requests
    for doc in outgoing_docs:
        d = doc.to_dict()
        d["id"] = doc.id
        d["direction"] = "outgoing"
        if d.get("status") == "accepted":
            seen_accepted.add(d.get("friend_id"))
        friends_list.append(d)
        
    # Add incoming requests
    for doc in incoming_docs:
        d = doc.to_dict()
        friend_target = d.get("user_id") # For incoming, the other person is the user_id
        
        # Skip duplicate accepted friends (already added from outgoing)
        if d.get("status") == "accepted" and friend_target in seen_accepted:
            continue
            
        d["id"] = doc.id
        d["direction"] = "incoming"
        friends_list.append(d)
        
    # Collect all unique friend UIDs we need to fetch profiles for
    friend_uids = set()
    for f in friends_list:
        other_uid = f.get("friend_id") if f["direction"] == "outgoing" else f.get("user_id")
        f["_other_uid"] = other_uid
        if other_uid:
            friend_uids.add(other_uid)
            
    # Fetch user profiles
    user_profiles = {}
    for other_uid in friend_uids:
        u_doc = db.collection("users").document(other_uid).get()
        if u_doc.exists:
            user_profiles[other_uid] = u_doc.to_dict()
            
    # Inject profile details into the response
    for f in friends_list:
        other_uid = f.pop("_other_uid", None)
        profile = user_profiles.get(other_uid, {})
        f["friend_name"] = profile.get("full_name") or profile.get("username") or "Unknown"
        f["friend_avatar"] = profile.get("avatar_url")
        f["streak"] = profile.get("streak", 0)
        
    return friends_list


# --- Feed ---

@router.post("/feed")
def create_feed_post(
    post: FeedPostCreate,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    post_id = str(uuid.uuid4())
    data = {
        "id": post_id,
        "user_id": uid,
        "content": post.content,
        "visibility": post.visibility,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    db.collection("feed_posts").document(post_id).set(data)
    data["created_at"] = None
    return data


@router.get("/feed")
def get_feed(
    skip: int = Query(0),
    limit: int = Query(50),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    # Get friend IDs
    friend_docs = db.collection("friendships").where("user_id", "==", uid).where("status", "==", "accepted").stream()
    friend_ids = {doc.to_dict()["friend_id"] for doc in friend_docs}
    friend_ids.add(uid)

    # Fetch public posts from friends + own posts
    posts = []
    # Avoid limiting the DB query before filtering, otherwise we might miss friend posts 
    # if there are many recent posts from non-friends.
    docs = (
        db.collection("feed_posts")
        .order_by("created_at", direction="DESCENDING")
        .stream()
    )
    for doc in docs:
        d = doc.to_dict()
        if d.get("user_id") in friend_ids:
            if d.get("created_at") and hasattr(d["created_at"], "isoformat"):
                d["created_at"] = d["created_at"].isoformat()
            posts.append(d)
            # Stop memory loop once we satisfy the pagination requirements
            if len(posts) >= limit + skip:
                break

    return posts[skip:skip + limit]


# --- Chat ---

@router.post("/chat/{friend_id}/messages")
def send_message(
    friend_id: str,
    msg: ChatMessageCreate,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    thread_id = _thread_id(uid, friend_id)
    msg_id = str(uuid.uuid4())
    data = {
        "id": msg_id,
        "thread_id": thread_id,
        "sender_id": uid,
        "content": msg.content,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    db.collection("chat_threads").document(thread_id).collection("messages").document(msg_id).set(data)
    data["created_at"] = None
    return data


@router.get("/chat/{friend_id}/messages")
def get_messages(
    friend_id: str,
    skip: int = Query(0),
    limit: int = Query(50),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    thread_id = _thread_id(uid, friend_id)
    docs = (
        db.collection("chat_threads")
        .document(thread_id)
        .collection("messages")
        .order_by("created_at", direction="DESCENDING")
        .limit(limit + skip)
        .stream()
    )
    results = []
    for doc in docs:
        d = doc.to_dict()
        if d.get("created_at") and hasattr(d["created_at"], "isoformat"):
            d["created_at"] = d["created_at"].isoformat()
        results.append(d)
    return results[skip:skip + limit]
