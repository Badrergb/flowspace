from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, Text, Numeric, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base
from app.models.base import UUIDMixin, TimeStampMixin, VersionMixin
from datetime import date

class UserSettings(Base, UUIDMixin, TimeStampMixin, VersionMixin):
    __tablename__ = "user_settings"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True, unique=True)
    daily_water_goal_ml = Column(Integer, default=2000)
    theme = Column(String, default="system")
    ai_features_enabled = Column(Boolean, default=True)
    ai_requests_used = Column(Integer, default=0, nullable=False)
    ai_quota_reset_at = Column(Date, default=date.today, nullable=False)
    # Add other settings here as needed

class Category(Base, UUIDMixin, TimeStampMixin, VersionMixin):
    __tablename__ = "categories"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    color = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    category_type = Column(String, nullable=True) # e.g. "task", "finance"

class Task(Base, UUIDMixin, TimeStampMixin, VersionMixin):
    __tablename__ = "tasks"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    due_date = Column(DateTime, nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    
    user = relationship("User", back_populates="tasks")

class Note(Base, UUIDMixin, TimeStampMixin, VersionMixin):
    __tablename__ = "notes"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

class Habit(Base, UUIDMixin, TimeStampMixin, VersionMixin):
    __tablename__ = "habits"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    icon_code = Column(String, nullable=True)
    category = Column(String, nullable=True)
    frequency_type = Column(String, nullable=False, default="daily")
    target_weekdays = Column(JSON, nullable=True)
    target_times_per_week = Column(Integer, default=7)
    reminder_time = Column(DateTime, nullable=True)
    is_archived = Column(Boolean, default=False)
    is_paused = Column(Boolean, default=False)
    available_freezes = Column(Integer, default=0)
    season_id = Column(String, nullable=True)
    freezes_used_log = Column(JSON, nullable=True)
    pause_windows = Column(JSON, nullable=True)
    best_streak = Column(Integer, default=0)
    
    # Legacy fields kept for backward compatibility if needed temporarily
    frequency = Column(String, nullable=True)
    streak = Column(Integer, default=0)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    
    user = relationship("User", back_populates="habits")

class HabitLog(Base, UUIDMixin, TimeStampMixin, VersionMixin):
    __tablename__ = "habit_logs"
    habit_id = Column(UUID(as_uuid=True), ForeignKey("habits.id"), nullable=False, index=True)
    completed_at = Column(DateTime, nullable=False)
    note = Column(Text, nullable=True)

class Goal(Base, UUIDMixin, TimeStampMixin, VersionMixin):
    __tablename__ = "goals"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    target_date = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="goals")

class GoalProgress(Base, UUIDMixin, TimeStampMixin, VersionMixin):
    __tablename__ = "goal_progress"
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=False, index=True)
    progress_value = Column(Integer, default=0)
    note = Column(Text, nullable=True)

class Journal(Base, UUIDMixin, TimeStampMixin, VersionMixin):
    __tablename__ = "journals"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    entry_date = Column(DateTime, nullable=False)
    content = Column(Text, nullable=True)
    mood = Column(String, nullable=True)
    
    user = relationship("User", back_populates="journals")

class CalendarEvent(Base, UUIDMixin, TimeStampMixin, VersionMixin):
    __tablename__ = "calendar_events"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)

class Reminder(Base, UUIDMixin, TimeStampMixin, VersionMixin):
    __tablename__ = "reminders"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    entity_type = Column(String, nullable=False) # 'task', 'habit', 'event'
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    remind_at = Column(DateTime, nullable=False)
    is_sent = Column(Boolean, default=False)

class WaterLog(Base, UUIDMixin, TimeStampMixin, VersionMixin):
    __tablename__ = "water_logs"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    amount_ml = Column(Integer, nullable=False)
    logged_at = Column(DateTime, nullable=False)

class WorkoutSession(Base, UUIDMixin, TimeStampMixin, VersionMixin):
    __tablename__ = "workout_sessions"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

class WorkoutSet(Base, UUIDMixin, TimeStampMixin, VersionMixin):
    __tablename__ = "workout_sets"
    workout_session_id = Column(UUID(as_uuid=True), ForeignKey("workout_sessions.id"), nullable=False, index=True)
    exercise_name = Column(String, nullable=False)
    set_number = Column(Integer, nullable=False)
    reps = Column(Integer, nullable=False)
    weight_kg = Column(Numeric(10, 2), nullable=False)

class Transaction(Base, UUIDMixin, TimeStampMixin, VersionMixin):
    __tablename__ = "transactions"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String, nullable=False) # 'income' or 'expense'
    amount = Column(Numeric(10, 2), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    date = Column(DateTime, nullable=False)
    note = Column(Text, nullable=True)
