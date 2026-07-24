from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.entities import Task, Habit, HabitLog, Goal, GoalProgress, Journal, CalendarEvent, Reminder, WaterLog, WorkoutSession, WorkoutSet, Transaction, Category, UserSettings, Note
from app.models.social import Friendship, FeedPost, FeedComment, FeedLike, ChatMessage, chat_participants
from app.models.sync import SyncOperation, DeviceSyncState
from app.models.device import Device
from fastapi.encoders import jsonable_encoder
from app.core.errors import safe_error_message

router = APIRouter()

def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = getattr(row, column.name)
    return d

@router.get("/export")
def export_user_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Exports all entities owned by the user into a downloadable JSON structure.
    """
    user_id = current_user.id
    data = {
        "user": row2dict(current_user),
        "settings": [row2dict(r) for r in db.query(UserSettings).filter(UserSettings.user_id == user_id).all()],
        "categories": [row2dict(r) for r in db.query(Category).filter(Category.user_id == user_id).all()],
        "tasks": [row2dict(r) for r in db.query(Task).filter(Task.user_id == user_id).all()],
        "notes": [row2dict(r) for r in db.query(Note).filter(Note.user_id == user_id).all()],
        "habits": [row2dict(r) for r in db.query(Habit).filter(Habit.user_id == user_id).all()],
        "goals": [row2dict(r) for r in db.query(Goal).filter(Goal.user_id == user_id).all()],
        "journals": [row2dict(r) for r in db.query(Journal).filter(Journal.user_id == user_id).all()],
        "calendar_events": [row2dict(r) for r in db.query(CalendarEvent).filter(CalendarEvent.user_id == user_id).all()],
        "reminders": [row2dict(r) for r in db.query(Reminder).filter(Reminder.user_id == user_id).all()],
        "water_logs": [row2dict(r) for r in db.query(WaterLog).filter(WaterLog.user_id == user_id).all()],
        "workout_sessions": [row2dict(r) for r in db.query(WorkoutSession).filter(WorkoutSession.user_id == user_id).all()],
        "transactions": [row2dict(r) for r in db.query(Transaction).filter(Transaction.user_id == user_id).all()],
        "devices": [row2dict(r) for r in db.query(Device).filter(Device.user_id == user_id).all()],
    }
    
    # Include child entities requiring joins or complex queries
    # Habit logs
    data["habit_logs"] = [row2dict(r) for r in db.query(HabitLog).join(Habit).filter(Habit.user_id == user_id).all()]
    # Goal progress
    data["goal_progress"] = [row2dict(r) for r in db.query(GoalProgress).join(Goal).filter(Goal.user_id == user_id).all()]
    # Workout sets
    data["workout_sets"] = [row2dict(r) for r in db.query(WorkoutSet).join(WorkoutSession).filter(WorkoutSession.user_id == user_id).all()]
    
    # Social data
    data["friendships"] = [row2dict(r) for r in db.query(Friendship).filter((Friendship.user_id == user_id) | (Friendship.friend_id == user_id)).all()]
    data["feed_posts"] = [row2dict(r) for r in db.query(FeedPost).filter(FeedPost.user_id == user_id).all()]
    data["feed_comments"] = [row2dict(r) for r in db.query(FeedComment).filter(FeedComment.user_id == user_id).all()]
    data["feed_likes"] = [row2dict(r) for r in db.query(FeedLike).filter(FeedLike.user_id == user_id).all()]
    data["chat_messages"] = [row2dict(r) for r in db.query(ChatMessage).filter(ChatMessage.sender_id == user_id).all()]

    return jsonable_encoder(data)


@router.delete("/account")
def delete_user_account(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Hard purges the user and all associated records from the database.
    """
    user_id = current_user.id
    try:
        # Child entities
        db.query(HabitLog).filter(HabitLog.habit_id.in_(db.query(Habit.id).filter(Habit.user_id == user_id))).delete(synchronize_session=False)
        db.query(GoalProgress).filter(GoalProgress.goal_id.in_(db.query(Goal.id).filter(Goal.user_id == user_id))).delete(synchronize_session=False)
        db.query(WorkoutSet).filter(WorkoutSet.workout_session_id.in_(db.query(WorkoutSession.id).filter(WorkoutSession.user_id == user_id))).delete(synchronize_session=False)
        db.query(FeedComment).filter(FeedComment.user_id == user_id).delete(synchronize_session=False)
        db.query(FeedLike).filter(FeedLike.user_id == user_id).delete(synchronize_session=False)
        db.query(ChatMessage).filter(ChatMessage.sender_id == user_id).delete(synchronize_session=False)
        
        # Social associations (chat_participants)
        db.execute(chat_participants.delete().where(chat_participants.c.user_id == user_id))
        
        # We don't delete the entire chat_threads, just let them exist if others are in them, 
        # or delete threads if no participants left. Simpler to leave thread records.
        
        db.query(Friendship).filter((Friendship.user_id == user_id) | (Friendship.friend_id == user_id)).delete(synchronize_session=False)

        # Base entities
        db.query(Task).filter(Task.user_id == user_id).delete(synchronize_session=False)
        db.query(Note).filter(Note.user_id == user_id).delete(synchronize_session=False)
        db.query(Habit).filter(Habit.user_id == user_id).delete(synchronize_session=False)
        db.query(Goal).filter(Goal.user_id == user_id).delete(synchronize_session=False)
        db.query(Journal).filter(Journal.user_id == user_id).delete(synchronize_session=False)
        db.query(CalendarEvent).filter(CalendarEvent.user_id == user_id).delete(synchronize_session=False)
        db.query(Reminder).filter(Reminder.user_id == user_id).delete(synchronize_session=False)
        db.query(WaterLog).filter(WaterLog.user_id == user_id).delete(synchronize_session=False)
        db.query(WorkoutSession).filter(WorkoutSession.user_id == user_id).delete(synchronize_session=False)
        db.query(Transaction).filter(Transaction.user_id == user_id).delete(synchronize_session=False)
        db.query(Category).filter(Category.user_id == user_id).delete(synchronize_session=False)
        db.query(UserSettings).filter(UserSettings.user_id == user_id).delete(synchronize_session=False)
        db.query(FeedPost).filter(FeedPost.user_id == user_id).delete(synchronize_session=False)
        
        # Sync engine data
        db.query(SyncOperation).filter(SyncOperation.user_id == user_id).delete(synchronize_session=False)
        db.query(DeviceSyncState).filter(DeviceSyncState.device_id.in_(db.query(Device.id).filter(Device.user_id == user_id))).delete(synchronize_session=False)
        db.query(Device).filter(Device.user_id == user_id).delete(synchronize_session=False)
        
        # Finally delete user
        db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
        
        db.commit()
    except Exception as e:
        db.rollback()
        safe_msg = safe_error_message(e, fallback="An error occurred while deleting the account")
        raise HTTPException(status_code=500, detail=safe_msg)
        
    return {"message": "Account successfully purged"}
