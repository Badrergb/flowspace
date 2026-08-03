import time
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.sync import SyncOperation, DeviceSyncState
from app.schemas.sync import SyncOperationSchema
from app.models.entities import (
    Category, Task, Note, Habit, HabitLog, Goal, GoalProgress, 
    Journal, CalendarEvent, Reminder, UserSettings, WaterLog, 
    WorkoutSession, WorkoutSet, Transaction,
    StudySession, FlashcardDeck, Flashcard, DailyReflection
)
import uuid
import logging
from typing import List

logger = logging.getLogger(__name__)

# Map entity string names to SQLAlchemy models
ENTITY_MODEL_MAP = {
    "category": Category,
    "task": Task,
    "note": Note,
    "habit": Habit,
    "habit_log": HabitLog,
    "goal": Goal,
    "goal_progress": GoalProgress,
    "journal": Journal,
    "calendar_event": CalendarEvent,
    "reminder": Reminder,
    "user_settings": UserSettings,
    "water_log": WaterLog,
    "workout_session": WorkoutSession,
    "workout_set": WorkoutSet,
    "transaction": Transaction,
    "study_session": StudySession,
    "flashcard_deck": FlashcardDeck,
    "flashcard": Flashcard,
    "daily_reflection": DailyReflection
}

class SyncService:
    def __init__(self, db: Session):
        self.db = db

    def _get_next_version(self) -> int:
        return int(time.time_ns())

    def _verify_child_ownership(self, model_class, entity_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        if hasattr(model_class, 'user_id'):
            row = self.db.query(model_class).filter(model_class.id == entity_id, model_class.user_id == user_id).first()
            return row is not None
        
        if model_class == HabitLog:
            row = self.db.query(HabitLog).join(Habit, HabitLog.habit_id == Habit.id).filter(
                HabitLog.id == entity_id, Habit.user_id == user_id).first()
            return row is not None
        elif model_class == GoalProgress:
            row = self.db.query(GoalProgress).join(Goal, GoalProgress.goal_id == Goal.id).filter(
                GoalProgress.id == entity_id, Goal.user_id == user_id).first()
            return row is not None
        elif model_class == WorkoutSet:
            row = self.db.query(WorkoutSet).join(WorkoutSession, WorkoutSet.workout_session_id == WorkoutSession.id).filter(
                WorkoutSet.id == entity_id, WorkoutSession.user_id == user_id).first()
            return row is not None
        return False
        
    def _verify_parent_ownership_for_create(self, model_class, payload: dict, user_id: uuid.UUID) -> bool:
        if hasattr(model_class, 'user_id'):
            return True
            
        if model_class == HabitLog and "habit_id" in payload:
            parent = self.db.query(Habit).filter(Habit.id == payload["habit_id"], Habit.user_id == user_id).first()
            return parent is not None
        elif model_class == GoalProgress and "goal_id" in payload:
            parent = self.db.query(Goal).filter(Goal.id == payload["goal_id"], Goal.user_id == user_id).first()
            return parent is not None
        elif model_class == WorkoutSet and "workout_session_id" in payload:
            parent = self.db.query(WorkoutSession).filter(WorkoutSession.id == payload["workout_session_id"], WorkoutSession.user_id == user_id).first()
            return parent is not None
        return False

    def process_upload(self, user_id: uuid.UUID, device_id: uuid.UUID, operations: List[SyncOperationSchema]):
        processed_count = 0
        
        last_version = 0

        for op in operations:
            # Generate a strictly monotonic version per operation to handle intra-batch updates
            current_version = self._get_next_version()
            if current_version <= last_version:
                current_version = last_version + 1
            last_version = current_version
            # Idempotency check
            existing_op = self.db.query(SyncOperation).filter(
                SyncOperation.id == op.operation_id
            ).first()
            
            if existing_op:
                logger.info(f"Operation {op.operation_id} already processed. Skipping.")
                continue

            # Log the operation
            new_op = SyncOperation(
                id=op.operation_id,
                user_id=user_id,
                device_id=device_id,
                entity_type=op.entity_type,
                entity_id=op.entity_id,
                operation_type=op.operation_type,
                payload=op.payload,
                version=current_version
            )
            self.db.add(new_op)
            
            model_class = ENTITY_MODEL_MAP.get(op.entity_type.lower())
            if not model_class:
                logger.warning(f"Unknown entity type {op.entity_type}. Skipping table update.")
                continue

            # Fetch existing row and verify ownership if it exists
            existing_row = self.db.query(model_class).filter(model_class.id == op.entity_id).first()
            
            if existing_row and not self._verify_child_ownership(model_class, op.entity_id, user_id):
                logger.warning(f"Unauthorized access to existing {op.entity_type} {op.entity_id}. Skipping.")
                continue

            if op.operation_type == "create":
                if existing_row:
                    # Treat as update if it exists (Upsert logic)
                    client_version = op.payload.get('version') if op.payload else None
                    if client_version is not None and client_version < existing_row.version:
                        logger.warning(f"Stale create (upsert) for {op.entity_type} {op.entity_id}. Skipping.")
                    else:
                        for k, v in op.payload.items():
                            if hasattr(existing_row, k) and k not in ['id', 'user_id']:
                                setattr(existing_row, k, v)
                        existing_row.version = current_version
                else:
                    if not self._verify_parent_ownership_for_create(model_class, op.payload, user_id):
                        logger.warning(f"Unauthorized parent for new {op.entity_type} {op.entity_id}. Skipping.")
                        continue
                    new_row = model_class(**op.payload)
                    new_row.id = op.entity_id
                    if hasattr(new_row, 'user_id'):
                        new_row.user_id = user_id
                    new_row.version = current_version
                    self.db.add(new_row)

            elif op.operation_type == "update":
                if existing_row:
                    client_version = op.payload.get('version') if op.payload else None
                    if client_version is not None and client_version < existing_row.version:
                        logger.warning(f"Stale update for {op.entity_type} {op.entity_id}. Skipping.")
                    else:
                        for k, v in op.payload.items():
                            if hasattr(existing_row, k) and k not in ['id', 'user_id']:
                                setattr(existing_row, k, v)
                        existing_row.version = current_version
                else:
                    logger.warning(f"Update for missing {op.entity_type} {op.entity_id}. Skipping.")
                    
            elif op.operation_type == "delete":
                if existing_row:
                    client_version = op.payload.get('version') if op.payload else None
                    if client_version is not None and client_version < existing_row.version:
                        logger.warning(f"Stale delete for {op.entity_type} {op.entity_id}. Skipping.")
                    else:
                        # Soft delete
                        existing_row.deleted_at = func.now()
                        existing_row.version = current_version

            # Flush the session so that the next operation in the loop can see the changes
            # (e.g., an update following a create in the same batch).
            self.db.flush()

            processed_count += 1
            
        if processed_count > 0:
            self.db.commit()
            
        return {
            "status": "success",
            "processed_count": processed_count,
            "version": last_version
        }

    def get_downloads(self, user_id: uuid.UUID, device_id: uuid.UUID, last_sync_version: int):
        operations = self.db.query(SyncOperation).filter(
            SyncOperation.user_id == user_id,
            SyncOperation.version > last_sync_version,
            SyncOperation.device_id != device_id
        ).order_by(SyncOperation.version.asc()).all()
        
        sync_state = self.db.query(DeviceSyncState).filter(
            DeviceSyncState.device_id == device_id
        ).first()
        
        new_last_sync = last_sync_version
        if operations:
            new_last_sync = operations[-1].version
            
        if not sync_state:
            sync_state = DeviceSyncState(
                device_id=device_id,
                last_sync_version=new_last_sync
            )
            self.db.add(sync_state)
        else:
            sync_state.last_sync_version = new_last_sync
            
        self.db.commit()
        
        return {
            "operations": operations,
            "new_last_sync_version": new_last_sync
        }
