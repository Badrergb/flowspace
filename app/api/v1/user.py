from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from google.cloud.firestore_v1 import Client as FirestoreClient
from firebase_admin import auth as firebase_auth

from app.db.database import get_db
from app.api.deps import get_current_user
from app.core.rate_limit import limiter

from pydantic import BaseModel
from fastapi import Request

router = APIRouter()


class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    birthday: Optional[datetime] = None


def _serialize_user(user_data: dict) -> dict:
    """Convert Firestore Timestamps and datetime objects to ISO 8601 strings."""
    result = {}
    for key, value in user_data.items():
        if hasattr(value, "isoformat"):
            # Handles both Python datetime and Firestore DatetimeWithNanoseconds
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result


@router.get("/me")
@limiter.limit("30/minute")
def get_current_user_profile(
    request: Request,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Returns the current user's full profile including birthday."""
    uid = current_user["uid"]
    user_doc = db.collection("users").document(uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = user_doc.to_dict()
    user_data["uid"] = uid
    return _serialize_user(user_data)


@router.patch("/me/profile")
@limiter.limit("15/minute")
def update_user_profile(
    request: Request,
    profile: UserProfileUpdate,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Updates the current user's profile fields. Only provided fields are updated."""
    uid = current_user["uid"]
    update_data = profile.model_dump(exclude_none=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Check username uniqueness if being changed
    if "username" in update_data and update_data["username"] != current_user.get("username"):
        existing = db.collection("users").where("username", "==", update_data["username"]).limit(1).get()
        if existing:
            raise HTTPException(status_code=400, detail="Username is already taken")

    # Convert birthday datetime to ISO string for Firestore storage
    if "birthday" in update_data and isinstance(update_data["birthday"], datetime):
        update_data["birthday"] = update_data["birthday"].isoformat()

    db.collection("users").document(uid).set(update_data, merge=True)
    return {"message": "Profile updated successfully"}


# Keep the old POST /profile route as an alias for backward compatibility
@router.post("/profile")
@limiter.limit("15/minute")
def update_user_profile_legacy(
    request: Request,
    profile: UserProfileUpdate,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Deprecated: Use PATCH /me/profile instead."""
    return update_user_profile(request, profile, db, current_user)


@router.get("/export")
@limiter.limit("2/minute")
def export_user_data(
    request: Request,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Exports all entities owned by the user as a JSON structure."""
    uid = current_user["uid"]
    user_ref = db.collection("users").document(uid)

    collections = [
        "tasks", "notes", "habits", "goals", "journals",
        "calendar_events", "reminders", "water_logs",
        "workout_sessions", "transactions", "categories",
        "habit_logs", "goal_progress", "workout_sets",
    ]

    data = {"user": _serialize_user(current_user)}
    for col in collections:
        docs = user_ref.collection(col).stream()
        data[col] = [{**doc.to_dict(), "id": doc.id} for doc in docs]

    return data


@router.delete("/account")
@limiter.limit("2/minute")
def delete_user_account(
    request: Request,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Hard purges the user and all associated Firestore documents."""
    uid = current_user["uid"]
    user_ref = db.collection("users").document(uid)

    collections = [
        "tasks", "notes", "habits", "goals", "journals",
        "calendar_events", "reminders", "water_logs",
        "workout_sessions", "transactions", "categories",
        "habit_logs", "goal_progress", "workout_sets",
        "settings",
    ]

    try:
        # Delete all subcollections
        for col in collections:
            docs = user_ref.collection(col).stream()
            for doc in docs:
                doc.reference.delete()

        # Delete user document
        user_ref.delete()

        # Delete from Firebase Auth
        firebase_auth.delete_user(uid)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting account: {str(e)}")

    return {"message": "Account successfully purged"}


