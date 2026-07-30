from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Optional

from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.models.entities import Task, Transaction, UserSettings, Habit, Goal, Note

router = APIRouter()

def verify_admin_key(x_admin_key: Optional[str] = Header(None)):
    if not x_admin_key or x_admin_key != settings.ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin key",
        )
    return True

@router.get("/kpis")
def get_admin_kpis(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_key)
):
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    total_tasks = db.query(func.count(Task.id)).scalar() or 0
    
    total_revenue = db.query(func.sum(Transaction.amount)).filter(Transaction.type == 'income').scalar() or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_tasks": total_tasks,
        "mrr": float(total_revenue)
    }

@router.get("/system")
def get_system_health(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_key)
):
    db_status = "operational"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "degraded"
        
    return {
        "services": [
            {"id": "db-1", "name": "Primary Database", "status": db_status, "latency": 12, "region": "us-east-1"},
            {"id": "cache-1", "name": "Redis Cache", "status": "operational", "latency": 2, "region": "us-east-1"},
            {"id": "api-1", "name": "API Gateway", "status": "operational", "latency": 45, "region": "global"}
        ]
    }

@router.get("/ai-usage")
def get_ai_usage(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_key)
):
    total_requests = db.query(func.sum(UserSettings.ai_requests_used)).scalar() or 0
    return {
        "total_ai_requests": total_requests
    }

@router.get("/analytics/growth")
def get_analytics_growth(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_key)
):
    # This is a basic implementation for SQLite/Postgres compatibility.
    # We fetch all users and aggregate in memory to avoid complex dialect-specific SQL.
    users = db.query(User.created_at).all()
    
    # Aggregate by YYYY-MM-DD
    from collections import defaultdict
    daily_counts = defaultdict(int)
    for u in users:
        if u.created_at:
            date_str = u.created_at.strftime("%Y-%m-%d")
            daily_counts[date_str] += 1
            
    # Format for the frontend chart: [{name: '2023-01-01', value: 5}, ...]
    chart_data = [{"name": k, "value": v} for k, v in sorted(daily_counts.items())]
    
    # If there's no data, return some sensible defaults so the chart doesn't break
    if not chart_data:
        import datetime
        today = datetime.date.today()
        chart_data = [{"name": (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d"), "value": 0} for i in range(7, -1, -1)]
        
    return chart_data

@router.get("/analytics/activity")
def get_analytics_activity(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_key)
):
    # Fetch latest 5 tasks, 5 habits, 5 goals to form an activity feed
    tasks = db.query(Task).order_by(Task.created_at.desc()).limit(5).all()
    habits = db.query(Habit).order_by(Habit.created_at.desc()).limit(5).all()
    goals = db.query(Goal).order_by(Goal.created_at.desc()).limit(5).all()
    
    feed = []
    for t in tasks:
        feed.append({"id": str(t.id), "type": "task", "title": t.title, "created_at": t.created_at})
    for h in habits:
        feed.append({"id": str(h.id), "type": "habit", "title": h.title, "created_at": h.created_at})
    for g in goals:
        feed.append({"id": str(g.id), "type": "goal", "title": g.title, "created_at": g.created_at})
        
    # Sort feed by created_at descending
    feed.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Format for JSON response
    for item in feed:
        item["created_at"] = item["created_at"].isoformat() if item["created_at"] else None
        
    return feed

@router.get("/analytics/features")
def get_analytics_features(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_key)
):
    # Count totals to see feature popularity
    return [
        {"name": "Tasks", "value": db.query(func.count(Task.id)).scalar() or 0},
        {"name": "Habits", "value": db.query(func.count(Habit.id)).scalar() or 0},
        {"name": "Goals", "value": db.query(func.count(Goal.id)).scalar() or 0},
        {"name": "Notes", "value": db.query(func.count(Note.id)).scalar() or 0},
        {"name": "Transactions", "value": db.query(func.count(Transaction.id)).scalar() or 0}
    ]

