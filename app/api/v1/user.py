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
    username: str | None = None
    full_name: str | None = None
    phone_number: str | None = None
    avatar_url: str | None = None


@router.post("/profile")
def update_user_profile(
    profile: UserProfileUpdate,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    update_data = profile.dict(exclude_none=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Check username uniqueness if being changed
    if "username" in update_data and update_data["username"] != current_user.get("username"):
        existing = db.collection("users").where("username", "==", update_data["username"]).limit(1).get()
        if existing:
            raise HTTPException(status_code=400, detail="Username is already taken")

    db.collection("users").document(uid).update(update_data)
    return {"message": "Profile updated successfully"}


@router.get("/export")
def export_user_data(
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

    data = {"user": current_user}
    for col in collections:
        docs = user_ref.collection(col).stream()
        data[col] = [{**doc.to_dict(), "id": doc.id} for doc in docs]

    return data


@router.delete("/account")
def delete_user_account(
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
