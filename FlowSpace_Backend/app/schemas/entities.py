from typing import Optional, List, Any
from pydantic import BaseModel, UUID4
from datetime import datetime
from decimal import Decimal

class CategoryBase(BaseModel):
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None
    category_type: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    model_config = {"from_attributes": True}

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_completed: bool = False
    due_date: Optional[datetime] = None
    category_id: Optional[UUID4] = None

class TaskResponse(TaskBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    model_config = {"from_attributes": True}

class HabitBase(BaseModel):
    title: str
    frequency: str
    streak: int = 0

class HabitResponse(HabitBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    model_config = {"from_attributes": True}

class GoalBase(BaseModel):
    title: str
    target_date: Optional[datetime] = None
    is_completed: bool = False

class GoalResponse(GoalBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    model_config = {"from_attributes": True}

class JournalBase(BaseModel):
    entry_date: datetime
    content: Optional[str] = None
    mood: Optional[str] = None

class JournalResponse(JournalBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    model_config = {"from_attributes": True}

class NoteBase(BaseModel):
    title: str
    content: Optional[str] = None
    category_id: Optional[UUID4] = None

class NoteResponse(NoteBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    model_config = {"from_attributes": True}

class CalendarEventBase(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    description: Optional[str] = None

class CalendarEventResponse(CalendarEventBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    model_config = {"from_attributes": True}

class WaterLogBase(BaseModel):
    amount_ml: int
    logged_at: datetime

class WaterLogResponse(WaterLogBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    model_config = {"from_attributes": True}

class WorkoutSessionBase(BaseModel):
    title: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    notes: Optional[str] = None

class WorkoutSessionResponse(WorkoutSessionBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    model_config = {"from_attributes": True}

class WorkoutSetBase(BaseModel):
    workout_session_id: UUID4
    exercise_name: str
    set_number: int
    reps: int
    weight_kg: Decimal

class WorkoutSetResponse(WorkoutSetBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    model_config = {"from_attributes": True}

class TransactionBase(BaseModel):
    type: str
    amount: Decimal
    category_id: Optional[UUID4] = None
    date: datetime
    note: Optional[str] = None

class TransactionResponse(TransactionBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    model_config = {"from_attributes": True}

class UserSettingsBase(BaseModel):
    daily_water_goal_ml: int
    theme: str

class UserSettingsResponse(UserSettingsBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    model_config = {"from_attributes": True}

class HabitLogBase(BaseModel):
    habit_id: UUID4
    completed_at: datetime

class HabitLogResponse(HabitLogBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    model_config = {"from_attributes": True}

class GoalProgressBase(BaseModel):
    goal_id: UUID4
    progress_date: datetime
    progress_value: float
    note: Optional[str] = None

class GoalProgressResponse(GoalProgressBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    model_config = {"from_attributes": True}
