from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from google.cloud.firestore_v1 import Client as FirestoreClient
from google.cloud.firestore_v1 import Query as FSQuery

from app.db.database import get_db
from app.api.deps import get_current_user

router = APIRouter()


def get_user_collection(db: FirestoreClient, uid: str, collection: str, limit: int = 100, skip: int = 0):
    """Generic helper to stream a user's subcollection."""
    docs = (
        db.collection("users")
        .document(uid)
        .collection(collection)
        .order_by("created_at", direction=FSQuery.DESCENDING)
        .limit(limit)
        .stream()
    )
    results = []
    for i, doc in enumerate(docs):
        if i < skip:
            continue
        d = doc.to_dict()
        d["id"] = doc.id
        results.append(d)
    return results


@router.get("/tasks")
def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_user_collection(db, current_user["uid"], "tasks", limit, skip)


@router.get("/habits")
def get_habits(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_user_collection(db, current_user["uid"], "habits", limit, skip)


@router.get("/goals")
def get_goals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_user_collection(db, current_user["uid"], "goals", limit, skip)


@router.get("/notes")
def get_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_user_collection(db, current_user["uid"], "notes", limit, skip)


@router.get("/journals")
def get_journals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_user_collection(db, current_user["uid"], "journals", limit, skip)


@router.get("/calendar-events")
def get_calendar_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_user_collection(db, current_user["uid"], "calendar_events", limit, skip)


@router.get("/water-logs")
def get_water_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_user_collection(db, current_user["uid"], "water_logs", limit, skip)


@router.get("/workout-sessions")
def get_workout_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_user_collection(db, current_user["uid"], "workout_sessions", limit, skip)


@router.get("/transactions")
def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_user_collection(db, current_user["uid"], "transactions", limit, skip)


@router.get("/categories")
def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_user_collection(db, current_user["uid"], "categories", limit, skip)


@router.get("/habit-logs")
def get_habit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_user_collection(db, current_user["uid"], "habit_logs", limit, skip)


@router.get("/goal-progress")
def get_goal_progress(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_user_collection(db, current_user["uid"], "goal_progress", limit, skip)


@router.get("/workout-sets")
def get_workout_sets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_user_collection(db, current_user["uid"], "workout_sets", limit, skip)
