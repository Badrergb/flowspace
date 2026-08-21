from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from app.db.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.models.entities import (
    Category, Task, Note, Habit, HabitLog, Goal, GoalProgress, 
    Journal, CalendarEvent, Reminder, UserSettings, WaterLog, 
    WorkoutSession, WorkoutSet, Transaction
)
from app.schemas import entities as schemas

router = APIRouter()

def get_paginated_entities(db: Session, model, user_id, skip: int, limit: int):
    query = db.query(model).filter(
        model.user_id == user_id, 
        model.deleted_at == None
    )
    # Basic ordering by created_at descending if available, else fallback
    if hasattr(model, 'created_at'):
        query = query.order_by(desc(model.created_at))
    return query.offset(skip).limit(limit).all()

@router.get("/tasks", response_model=List[schemas.TaskResponse])
def get_tasks(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_paginated_entities(db, Task, current_user.id, skip, limit)

@router.get("/habits", response_model=List[schemas.HabitResponse])
def get_habits(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_paginated_entities(db, Habit, current_user.id, skip, limit)

@router.get("/goals", response_model=List[schemas.GoalResponse])
def get_goals(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_paginated_entities(db, Goal, current_user.id, skip, limit)

@router.get("/journals", response_model=List[schemas.JournalResponse])
def get_journals(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_paginated_entities(db, Journal, current_user.id, skip, limit)

@router.get("/notes", response_model=List[schemas.NoteResponse])
def get_notes(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_paginated_entities(db, Note, current_user.id, skip, limit)

@router.get("/calendar-events", response_model=List[schemas.CalendarEventResponse])
def get_calendar_events(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_paginated_entities(db, CalendarEvent, current_user.id, skip, limit)

@router.get("/water-logs", response_model=List[schemas.WaterLogResponse])
def get_water_logs(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_paginated_entities(db, WaterLog, current_user.id, skip, limit)

@router.get("/workout-sessions", response_model=List[schemas.WorkoutSessionResponse])
def get_workout_sessions(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_paginated_entities(db, WorkoutSession, current_user.id, skip, limit)

@router.get("/transactions", response_model=List[schemas.TransactionResponse])
def get_transactions(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_paginated_entities(db, Transaction, current_user.id, skip, limit)

@router.get("/categories", response_model=List[schemas.CategoryResponse])
def get_categories(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_paginated_entities(db, Category, current_user.id, skip, limit)

@router.get("/habit-logs", response_model=List[schemas.HabitLogResponse])
def get_habit_logs(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(HabitLog).join(Habit, HabitLog.habit_id == Habit.id).filter(
        Habit.user_id == current_user.id,
        HabitLog.deleted_at == None
    ).order_by(desc(HabitLog.completed_at)).offset(skip).limit(limit)
    return query.all()

@router.get("/goal-progress", response_model=List[schemas.GoalProgressResponse])
def get_goal_progress(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(GoalProgress).join(Goal, GoalProgress.goal_id == Goal.id).filter(
        Goal.user_id == current_user.id,
        GoalProgress.deleted_at == None
    ).order_by(desc(GoalProgress.created_at)).offset(skip).limit(limit)
    return query.all()

@router.get("/workout-sets", response_model=List[schemas.WorkoutSetResponse])
def get_workout_sets(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(WorkoutSet).join(WorkoutSession, WorkoutSet.workout_session_id == WorkoutSession.id).filter(
        WorkoutSession.user_id == current_user.id,
        WorkoutSet.deleted_at == None
    ).order_by(desc(WorkoutSet.created_at)).offset(skip).limit(limit)
    return query.all()
