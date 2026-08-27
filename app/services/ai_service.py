import os
import json
import logging
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

_cached_model = None

def _get_active_model() -> str:
    global _cached_model
    if _cached_model:
        return _cached_model
    
    try:
        import requests
        headers = {"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"}
        resp = requests.get("https://api.groq.com/openai/v1/models", headers=headers)
        if resp.status_code == 200:
            models = resp.json().get("data", [])
            for m in models:
                model_id = m.get("id", "")
                if "llama" in model_id.lower() or "mixtral" in model_id.lower() or "gemma" in model_id.lower():
                    _cached_model = model_id
                    return _cached_model
            
            # If no llama/mixtral, just pick the first one
            if models:
                _cached_model = models[0].get("id")
                return _cached_model
    except Exception as e:
        logger.error(f"Failed to fetch dynamic model: {e}")
        
    return "llama-3.3-70b-versatile"

def _check_ai_enabled(db, user_id) -> bool:
    try:
        settings_doc = (
            db.collection("users")
            .document(user_id)
            .collection("settings")
            .document("preferences")
            .get()
        )
        if settings_doc.exists:
            data = settings_doc.to_dict()
            if not data.get("ai_features_enabled", True):
                return False
    except Exception:
        pass
    return True

def check_and_increment_quota(db, user_id):
    try:
        ref = (
            db.collection("users")
            .document(user_id)
            .collection("settings")
            .document("preferences")
        )
        doc = ref.get()
        today_str = date.today().isoformat()

        if doc.exists:
            data = doc.to_dict()
            reset_at = str(data.get("ai_quota_reset_at", today_str))
            try:
                requests_used = int(data.get("ai_requests_used", 0))
            except (ValueError, TypeError):
                requests_used = 0

            if reset_at < today_str:
                requests_used = 0
                reset_at = today_str

            if requests_used >= settings.AI_DAILY_REQUEST_LIMIT:
                raise HTTPException(
                    status_code=429,
                    detail=f"Daily AI limit reached ({settings.AI_DAILY_REQUEST_LIMIT}/day). Resets at midnight."
                )

            ref.set({
                "ai_requests_used": requests_used + 1,
                "ai_quota_reset_at": today_str,
                "ai_features_enabled": data.get("ai_features_enabled", True),
            }, merge=True)
        else:
            ref.set({
                "ai_requests_used": 1,
                "ai_quota_reset_at": today_str,
                "ai_features_enabled": True,
            })
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Could not check AI quota: {e}")

def categorize_transactions(transactions: list, db, user_id) -> dict:
    """
    Takes a list of transaction descriptions and returns a dictionary
    mapping each description to a category.
    """
    ai_client = _get_client()
    if not ai_client or not _check_ai_enabled(db, user_id):
        return {tx: "Other" for tx in transactions}

    check_and_increment_quota(db, user_id)

    prompt = (
        "Categorize the following transactions into standard budgeting categories "
        "(e.g., Food, Transport, Utilities, Entertainment, Housing, Other).\n"
        "Return a JSON object where keys are the descriptions and values are the categories.\n\n"
        f"Transactions: {json.dumps(transactions)}"
    )

    try:
        response = ai_client.chat.completions.create(
            model=_get_active_model(),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Failed to categorize via AI: {e}")
        return {tx: "Other" for tx in transactions}

def generate_weekly_review(db, user_id) -> str:
    """
    Generates a motivational weekly review summary.
    """
    ai_client = _get_client()
    if not ai_client or not _check_ai_enabled(db, user_id):
        return "You had a great week! Keep up the momentum!"

    check_and_increment_quota(db, user_id)

    # Gather context from Firestore
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    try:
        task_docs = (
            db.collection("users").document(user_id).collection("tasks")
            .where("is_completed", "==", True)
            .stream()
        )
        completed_tasks = [doc.to_dict() for doc in task_docs]

        habit_docs = (
            db.collection("users").document(user_id).collection("habit_logs")
            .stream()
        )
        completed_habits = [doc.to_dict() for doc in habit_docs]
    except Exception:
        completed_tasks = []
        completed_habits = []

    task_count = len(completed_tasks)
    habit_count = len(completed_habits)
    task_titles = [t.get("title", "") for t in completed_tasks[:5]]

    context_str = f"This week, the user completed {task_count} tasks and logged {habit_count} habit completions."
    if task_titles:
        context_str += f" Some tasks they finished: {', '.join(task_titles)}."

    prompt = (
        f"Based on the user's activity: '{context_str}', "
        "write a short, highly encouraging 2-sentence summary of their productivity this week."
    )

    try:
        response = ai_client.chat.completions.create(
            model=_get_active_model(),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Failed to generate review via AI: {e}")
        return "You had a great week! Keep up the momentum!"

def chat_with_data(query: str, db, user_id) -> str:
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

    system_prompt = (
        "Your name is Flow AI. You are a highly focused productivity assistant built directly into the FlowSpace app. "
        "You must ONLY answer questions related to productivity, time management, habits, the FlowSpace app itself, or the user's tasks and goals. "
        "If the user asks you a question about any other topic (such as general knowledge, coding, history, entertainment, etc.), "
        "you must politely decline to answer and remind them that you are Flow AI, a productivity assistant. "
        "Keep your answers concise, encouraging, and highly relevant."
    )

    try:
        response = ai_client.chat.completions.create(
            model=_get_active_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Failed to chat via AI: {e}")
        return f"AI Connection Error: {str(e)}"
