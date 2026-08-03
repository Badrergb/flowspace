import os
import json
import logging
from sqlalchemy.orm import Session
from app.models.entities import Transaction, Task, Habit, HabitLog, Journal, UserSettings
from app.core.config import settings
from datetime import date, datetime, timedelta
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Safely import OpenAI if available and configured
try:
    from openai import OpenAI
    client = OpenAI(
        api_key=os.environ.get("GROQ_API_KEY", "mock-key"),
        base_url="https://api.groq.com/openai/v1"
    )
except ImportError:
    client = None

def _get_client():
    if not client:
        logger.warning("Groq not configured due to missing openai library.")
        return None
    if os.environ.get("GROQ_API_KEY") is None:
        logger.warning("Groq API Key is None.")
        return None
    return client

def _check_ai_enabled(db: Session, user_id) -> bool:
    settings_obj = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if settings_obj and not settings_obj.ai_features_enabled:
        return False
    return True

def check_and_increment_quota(db: Session, user_id):
    user_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not user_settings:
        return

    # Reset the counter if it's a new day
    if user_settings.ai_quota_reset_at < date.today():
        user_settings.ai_requests_used = 0
        user_settings.ai_quota_reset_at = date.today()

    if user_settings.ai_requests_used >= settings.AI_DAILY_REQUEST_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Daily AI limit reached ({settings.AI_DAILY_REQUEST_LIMIT}/day). Resets at midnight."
        )

    user_settings.ai_requests_used += 1
    db.commit()

def categorize_transactions(transactions: list[str], db: Session, user_id) -> dict:
    """
    Takes a list of transaction descriptions and returns a dictionary
    mapping each description to a category.
    """
    ai_client = _get_client()
    if not ai_client or not _check_ai_enabled(db, user_id):
        return {tx: "Other" for tx in transactions}
        
    check_and_increment_quota(db, user_id)
        
    prompt = f"Categorize the following transactions into standard budgeting categories (e.g., Food, Transport, Utilities, Entertainment, Housing, Other).\nReturn a JSON object where keys are the descriptions and values are the categories.\n\nTransactions: {json.dumps(transactions)}"
    
    try:
        response = ai_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Failed to categorize via AI: {e}")
        return {tx: "Other" for tx in transactions}

def generate_weekly_review(db: Session, user_id) -> str:
    """
    Generates a motivational weekly review summary.
    """
    ai_client = _get_client()
    if not ai_client or not _check_ai_enabled(db, user_id):
        return "You had a great week! Keep up the momentum!"
        
    check_and_increment_quota(db, user_id)
        
    # Gather context: Get tasks completed in the last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    completed_tasks = db.query(Task).filter(
        Task.user_id == user_id, 
        Task.is_completed == True,
        Task.updated_at >= seven_days_ago
    ).all()
    
    completed_habits = db.query(HabitLog).join(Habit).filter(
        Habit.user_id == user_id,
        HabitLog.completed_at >= seven_days_ago
    ).all()
    
    task_count = len(completed_tasks)
    habit_count = len(completed_habits)
    
    task_titles = [t.title for t in completed_tasks[:5]] # sample up to 5 tasks
    
    context_str = f"This week, the user completed {task_count} tasks and logged {habit_count} habit completions."
    if task_titles:
        context_str += f" Some tasks they finished: {', '.join(task_titles)}."

    prompt = f"Based on the user's activity: '{context_str}', write a short, highly encouraging 2-sentence summary of their productivity this week."
    
    try:
        response = ai_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Failed to generate review via AI: {e}")
        return "You had a great week! Keep up the momentum!"

def chat_with_data(query: str, db: Session, user_id) -> str:
    """
    Answers user queries grounded in their data.
    """
    ai_client = _get_client()
    if not ai_client:
        if os.environ.get("GROQ_API_KEY") is None:
            return "Backend Error: GROQ_API_KEY is completely missing from Render environment variables."
        return "Backend Error: The 'openai' python package failed to load or is not installed."
        
    if not _check_ai_enabled(db, user_id):
        return "AI features are disabled in your settings."
        
    check_and_increment_quota(db, user_id)
        
    # Gather context (e.g. active goals)
    prompt = f"You are a helpful personal assistant. The user asks: '{query}'. Provide a brief helpful answer."
    
    try:
        response = ai_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Failed to chat via AI: {e}")
        return f"AI Connection Error: {str(e)}"
